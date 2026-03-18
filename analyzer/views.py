from django.contrib.auth.hashers import check_password
from django.db import transaction
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


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserProfileSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phone"]
            password = serializer.validated_data["password"]
            try:
                user = UserProfile.objects.get(phone=phone)
                if user.password and check_password(password, user.password):
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

        image_file = serializer.validated_data["image"]
        name = serializer.validated_data["name"]
        phone = serializer.validated_data["phone"]
        latitude = serializer.validated_data.get("latitude")
        longitude = serializer.validated_data.get("longitude")

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

                analysis_data = analyze_image(image_file, latitude, longitude)

                result = AnalysisResult.objects.create(
                    image=image_record,
                    health_score=analysis_data["health_score"],
                    actions=analysis_data["actions"],
                    latitude=analysis_data["latitude"],
                    longitude=analysis_data["longitude"],
                    overlay_image_url=analysis_data["overlay_image_url"],
                )
        except ValidationError as exc:
            return Response({"detail": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {"detail": "Failed to analyze image."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(AnalysisResultSerializer(result).data, status=status.HTTP_201_CREATED)
