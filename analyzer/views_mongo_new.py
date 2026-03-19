from datetime import datetime, timezone
import re
from typing import Any

from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings
from pymongo.errors import DuplicateKeyError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .mongo import get_collections, serialize_result, serialize_user
from .serializers import AnalyzeRequestSerializer, LoginSerializer
from .services import (
    analyze_image,
    generate_grok_ai_analysis,
    read_image,
    save_image_locally,
    synthesize_report_tts,
)


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


def normalize_phone(value: str) -> str:
    trimmed = str(value).strip()
    digits_only = re.sub(r"\D", "", trimmed)
    return digits_only or trimmed


class RegisterView(APIView):
    parser_classes = [JSONParser, FormParser]

    def post(self, request):
        name = str(request.data.get("name", "")).strip()
        phone = normalize_phone(str(request.data.get("phone", "")))
        password = str(request.data.get("password", "")).strip()

        if not name or not phone or not password:
            return Response(
                {"detail": "name, phone and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        collections = get_collections()
        users = collections["users"]

        existing_user = users.find_one({"phone": phone})
        if existing_user:
            if existing_user.get("password"):
                return Response(
                    {"detail": "Phone number is already registered."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            users.update_one(
                {"_id": existing_user["_id"]},
                {
                    "$set": {
                        "name": name,
                        "password": make_password(password),
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            updated = users.find_one({"_id": existing_user["_id"]})
            return Response(serialize_user(updated or existing_user), status=status.HTTP_201_CREATED)

        try:
            insert_result = users.insert_one(
                {
                    "name": name,
                    "phone": phone,
                    "password": make_password(password),
                    "created_at": datetime.now(timezone.utc),
                }
            )
        except DuplicateKeyError:
            return Response(
                {"detail": "Phone number is already registered."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_doc = users.find_one({"_id": insert_result.inserted_id})
        return Response(serialize_user(user_doc or {}), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    parser_classes = [JSONParser, FormParser]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        data = validated_data if isinstance(validated_data, dict) else {}

        phone = normalize_phone(str(data.get("phone", "")))
        password = str(data.get("password", ""))

        users = get_collections()["users"]
        user_doc = users.find_one({"phone": phone})

        if not user_doc:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        hashed_password = user_doc.get("password")
        if not hashed_password:
            return Response(
                {
                    "detail": "This account has no password yet. Sign up with this phone number to activate login.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not check_password(password, hashed_password):
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serialize_user(user_doc), status=status.HTTP_200_OK)


class AnalyzeView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = AnalyzeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        data: dict[str, Any] = validated_data if isinstance(validated_data, dict) else {}

        image_file = data["image"]
        name = str(data["name"])
        phone = normalize_phone(str(data["phone"]))
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        camera_number = data.get("camera_number")
        field_zone = CAMERA_ZONE_MAP.get(int(camera_number)) if camera_number is not None else None
        explicit_gps_provided = latitude is not None and longitude is not None

        collections = get_collections()
        users = collections["users"]
        image_records = collections["image_records"]
        analysis_results = collections["analysis_results"]

        try:
            image_file.seek(0)
            image_bytes = image_file.read()
            image_file.seek(0)

            users.update_one(
                {"phone": phone},
                {
                    "$set": {"name": name, "phone": phone, "updated_at": datetime.now(timezone.utc)},
                    "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
                },
                upsert=True,
            )
            user_doc = users.find_one({"phone": phone})

            original_image = read_image(image_file)
            original_image_url = save_image_locally(original_image, "originals")

            image_insert = image_records.insert_one(
                {
                    "user_id": user_doc.get("_id") if user_doc else None,
                    "original_image_url": original_image_url,
                    "uploaded_at": datetime.now(timezone.utc),
                }
            )

            analysis_data = analyze_image(
                image_file,
                latitude,
                longitude,
                require_location=False,
            )

            result_latitude = analysis_data["latitude"] if (camera_number is None and explicit_gps_provided) else None
            result_longitude = analysis_data["longitude"] if (camera_number is None and explicit_gps_provided) else None

            ai_analysis = generate_grok_ai_analysis(
                image_bytes=image_bytes,
                mathematical_analysis={
                    "health_score": analysis_data.get("health_score"),
                    "actions": analysis_data.get("actions") or {},
                },
                camera_number=camera_number,
                field_zone=field_zone,
                latitude=result_latitude,
                longitude=result_longitude,
            )

            result_doc = {
                "image_id": image_insert.inserted_id,
                "user_id": user_doc.get("_id") if user_doc else None,
                "user_phone": phone,
                "health_score": analysis_data["health_score"],
                "actions": analysis_data["actions"],
                "ai_analysis": ai_analysis,
                "latitude": result_latitude,
                "longitude": result_longitude,
                "camera_number": camera_number,
                "field_zone": field_zone,
                "overlay_image_url": analysis_data["overlay_image_url"],
                "original_image_url": original_image_url,
                "created_at": datetime.now(timezone.utc),
            }

            inserted = analysis_results.insert_one(result_doc)
            created_doc = analysis_results.find_one({"_id": inserted.inserted_id})
        except Exception as exc:
            detail = "Failed to analyze image."
            if settings.DEBUG:
                detail = f"Failed to analyze image: {exc}"
            return Response({"detail": detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serialize_result(created_doc or result_doc), status=status.HTTP_201_CREATED)


class AnalyzeBatchView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        name = str(request.data.get("name", "")).strip()
        phone = normalize_phone(str(request.data.get("phone", "")))
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

        collections = get_collections()
        users = collections["users"]
        image_records = collections["image_records"]
        analysis_results = collections["analysis_results"]
        results: list[dict[str, Any]] = []

        try:
            users.update_one(
                {"phone": phone},
                {
                    "$set": {"name": name, "phone": phone, "updated_at": datetime.now(timezone.utc)},
                    "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
                },
                upsert=True,
            )
            user_doc = users.find_one({"phone": phone})

            for image_file, camera_number in zip(images, camera_numbers):
                image_file.seek(0)
                image_bytes = image_file.read()
                image_file.seek(0)

                field_zone = CAMERA_ZONE_MAP.get(camera_number) if camera_number is not None else None

                original_image = read_image(image_file)
                original_image_url = save_image_locally(original_image, "originals")

                image_insert = image_records.insert_one(
                    {
                        "user_id": user_doc.get("_id") if user_doc else None,
                        "original_image_url": original_image_url,
                        "uploaded_at": datetime.now(timezone.utc),
                    }
                )

                analysis_data = analyze_image(
                    image_file,
                    request_lat=None,
                    request_lon=None,
                    require_location=False,
                )

                ai_analysis = generate_grok_ai_analysis(
                    image_bytes=image_bytes,
                    mathematical_analysis={
                        "health_score": analysis_data.get("health_score"),
                        "actions": analysis_data.get("actions") or {},
                    },
                    camera_number=camera_number,
                    field_zone=field_zone,
                    latitude=None,
                    longitude=None,
                )

                result_doc = {
                    "image_id": image_insert.inserted_id,
                    "user_id": user_doc.get("_id") if user_doc else None,
                    "user_phone": phone,
                    "health_score": analysis_data["health_score"],
                    "actions": analysis_data["actions"],
                    "ai_analysis": ai_analysis,
                    "latitude": None,
                    "longitude": None,
                    "camera_number": camera_number,
                    "field_zone": field_zone,
                    "overlay_image_url": analysis_data["overlay_image_url"],
                    "original_image_url": original_image_url,
                    "created_at": datetime.now(timezone.utc),
                }

                inserted = analysis_results.insert_one(result_doc)
                created_doc = analysis_results.find_one({"_id": inserted.inserted_id})
                results.append(serialize_result(created_doc or result_doc))
        except Exception as exc:
            detail = "Failed to process batch analysis."
            if settings.DEBUG:
                detail = f"Failed to process batch analysis: {exc}"
            return Response({"detail": detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(results, status=status.HTTP_201_CREATED)


class ResultsView(APIView):
    def get(self, request):
        collections = get_collections()
        analysis_results = collections["analysis_results"]

        phone_raw = request.query_params.get("phone")
        phone = normalize_phone(str(phone_raw)) if phone_raw else ""

        query: dict[str, Any] = {}
        if phone:
            users = collections["users"]
            image_records = collections["image_records"]

            user_doc = users.find_one({"phone": phone})
            if not user_doc:
                return Response([], status=status.HTTP_200_OK)

            user_id = user_doc.get("_id")
            image_ids = [row.get("_id") for row in image_records.find({"user_id": user_id}, {"_id": 1})]

            query = {
                "$or": [
                    {"user_id": user_id},
                    {"user_phone": phone},
                    {"image_id": {"$in": image_ids}} if image_ids else {"_id": None},
                ]
            }

        rows = list(analysis_results.find(query).sort("created_at", -1).limit(500))
        return Response([serialize_result(row) for row in rows], status=status.HTTP_200_OK)


class ReportTTSView(APIView):
    parser_classes = [JSONParser, FormParser]

    def post(self, request):
        text = str(request.data.get("text", "")).strip()
        voice_id_raw = request.data.get("voice_id", 147320)
        language = str(request.data.get("language", "en-us")).strip() or "en-us"
        speech_model = str(request.data.get("speech_model", "mars-flash")).strip() or "mars-flash"
        output_format = str(request.data.get("format", "mp3")).strip() or "mp3"

        try:
            voice_id = int(voice_id_raw)
        except (TypeError, ValueError):
            return Response(
                {"detail": "voice_id must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = synthesize_report_tts(
                text,
                voice_id=voice_id,
                language=language,
                speech_model=speech_model,
                output_format=output_format,
            )
        except ValidationError as exc:
            message = exc.detail if hasattr(exc, "detail") else str(exc)
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            detail = "Failed to generate TTS audio."
            if settings.DEBUG:
                detail = f"Failed to generate TTS audio: {exc}"
            return Response({"detail": detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(payload, status=status.HTTP_200_OK)
