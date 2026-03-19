from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.db import transaction
from django.db.utils import DatabaseError
from typing import Any
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AnalysisResult, ImageRecord, UserProfile
from .serializers import (
    AnalysisResultSerializer,
    AnalyzeRequestSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)
from .services import analyze_image, read_image, upload_to_supabase


CAMERA_ZONE_MAP: dict[int, str] = {
    1: "North-West Zone",
    2: "North-Center Zone",
    3: "North-East Zone",
    4: "West-Center Zone",
    5: "Center Zone",
    6: "East-Center Zone",
    7: "South-West Zone",
    8: "South-Center Zone",
    9: "South-East Zone",
}


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            data = validated_data if isinstance(validated_data, dict) else {}

            name = str(data.get("name", ""))
            phone = str(data.get("phone", "")).strip()
            password = str(data.get("password", ""))

            existing_user = UserProfile.objects.filter(phone=phone).first()
            if existing_user:
                if existing_user.password:
                    return Response(
                        {"detail": "Phone number is already registered."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # User was likely auto-created from analysis without credentials.
                existing_user.name = name
                existing_user.password = make_password(password)
                existing_user.save(update_fields=["name", "password"])
                return Response(
                    UserProfileSerializer(existing_user).data,
                    status=status.HTTP_201_CREATED,
                )

            user = serializer.save()
            return Response(UserProfileSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            data = validated_data if isinstance(validated_data, dict) else {}

            phone = str(data.get("phone", "")).strip()
            password = str(data.get("password", ""))
            try:
                user = UserProfile.objects.get(phone=phone)
                if not user.password:
                    return Response(
                        {
                            "detail": "This account has no password yet. Sign up with this phone number to activate login.",
                        },
                        status=status.HTTP_401_UNAUTHORIZED,
                    )

                if check_password(password, user.password):
                    return Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)
                return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
            except UserProfile.DoesNotExist:
                return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AnalyzeView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = AnalyzeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        data: dict[str, Any] = validated_data if isinstance(validated_data, dict) else {}

        image_file = data["image"]
        name = str(data["name"])
        phone = str(data["phone"])
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        camera_number = data.get("camera_number")
        field_zone = CAMERA_ZONE_MAP.get(int(camera_number)) if camera_number is not None else None
        explicit_gps_provided = latitude is not None and longitude is not None

        try:
            with transaction.atomic():
                user, _ = UserProfile.objects.get_or_create(
                    phone=phone,
                    defaults={"name": name},
                )
                if user.name != name:
                    user.name = name
                    user.save(update_fields=["name"])

                original_image = read_image(image_file)
                original_image_url = upload_to_supabase(original_image)

                image_record = ImageRecord.objects.create(
                    user=user,
                    original_image_url=original_image_url,
                )

                analysis_data = analyze_image(
                    image_file,
                    latitude,
                    longitude,
                    require_location=False,
                )

                # Map behavior contract:
                # - Save coordinates only if user explicitly entered GPS and this is not a camera record.
                # - Camera records are grid-only, so map coordinates must remain null.
                result_latitude = analysis_data["latitude"] if (camera_number is None and explicit_gps_provided) else None
                result_longitude = analysis_data["longitude"] if (camera_number is None and explicit_gps_provided) else None

                result = AnalysisResult.objects.create(
                    image=image_record,
                    health_score=analysis_data["health_score"],
                    actions=analysis_data["actions"],
                    latitude=result_latitude,
                    longitude=result_longitude,
                    camera_number=camera_number,
                    field_zone=field_zone,
                    overlay_image_url=analysis_data["overlay_image_url"],
                )
        except ValidationError as exc:
            return Response({"detail": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            detail = "Failed to analyze image."
            if isinstance(exc, DatabaseError):
                detail = (
                    "Database schema is out of sync with code. "
                    "Run migrations and restart the server (python manage.py migrate)."
                )
            if settings.DEBUG:
                detail = f"Failed to analyze image: {exc}"
            return Response(
                {"detail": detail},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(AnalysisResultSerializer(result).data, status=status.HTTP_201_CREATED)


class AnalyzeBatchView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        name = str(request.data.get("name", "")).strip()
        phone = str(request.data.get("phone", "")).strip()
        images = request.FILES.getlist("images")
        camera_numbers_raw = request.data.getlist("camera_numbers")

        if not name or not phone:
            return Response(
                {"detail": "name and phone are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not images:
            return Response(
                {"detail": "At least one image file is required in images."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        camera_numbers: list[int | None] = [None] * len(images)
        if camera_numbers_raw:
            if len(camera_numbers_raw) != len(images):
                return Response(
                    {
                        "detail": "camera_numbers count must match images count when provided.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                camera_numbers = [int(value) for value in camera_numbers_raw]
            except (TypeError, ValueError):
                return Response(
                    {"detail": "camera_numbers must be valid integers."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        results: list[Any] = []

        try:
            with transaction.atomic():
                user, _ = UserProfile.objects.get_or_create(
                    phone=phone,
                    defaults={"name": name},
                )
                if user.name != name:
                    user.name = name
                    user.save(update_fields=["name"])

                for image_file, camera_number in zip(images, camera_numbers):
                    field_zone = (
                        CAMERA_ZONE_MAP.get(camera_number)
                        if camera_number is not None
                        else None
                    )

                    original_image = read_image(image_file)
                    original_image_url = upload_to_supabase(original_image)

                    image_record = ImageRecord.objects.create(
                        user=user,
                        original_image_url=original_image_url,
                    )

                    analysis_data = analyze_image(
                        image_file,
                        request_lat=None,
                        request_lon=None,
                        require_location=False,
                    )

                    # Batch endpoint is camera-grid oriented. If no explicit GPS is provided,
                    # keep map coordinates null.
                    result_latitude = None
                    result_longitude = None

                    result = AnalysisResult.objects.create(
                        image=image_record,
                        health_score=analysis_data["health_score"],
                        actions=analysis_data["actions"],
                        latitude=result_latitude,
                        longitude=result_longitude,
                        camera_number=camera_number,
                        field_zone=field_zone,
                        overlay_image_url=analysis_data["overlay_image_url"],
                    )

                    results.append(AnalysisResultSerializer(result).data)
        except ValidationError as exc:
            return Response({"detail": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            detail = "Failed to process batch analysis."
            if isinstance(exc, DatabaseError):
                detail = (
                    "Database schema is out of sync with code. "
                    "Run migrations and restart the server (python manage.py migrate)."
                )
            if settings.DEBUG:
                detail = f"Failed to process batch analysis: {exc}"
            return Response(
                {"detail": detail},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(results, status=status.HTTP_201_CREATED)
