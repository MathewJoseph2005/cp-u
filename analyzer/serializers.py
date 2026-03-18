# pyright: reportMissingTypeStubs=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownReturnType=false
from rest_framework import serializers
from typing import Any
from django.contrib.auth.hashers import make_password
from .models import AnalysisResult, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["id", "name", "phone"]


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["name", "phone", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)


class AnalyzeRequestSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
    name = serializers.CharField(required=True, max_length=255)
    phone = serializers.CharField(required=True, max_length=32)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        latitude = attrs.get("latitude")
        longitude = attrs.get("longitude")

        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError(
                "Both latitude and longitude must be provided together."
            )

        if latitude is not None and not (-90.0 <= latitude <= 90.0):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")

        if longitude is not None and not (-180.0 <= longitude <= 180.0):
            raise serializers.ValidationError("Longitude must be between -180 and 180.")

        return attrs


class AnalysisResultSerializer(serializers.ModelSerializer):
    original_image_url = serializers.URLField(source="image.original_image_url", read_only=True)

    class Meta:
        model = AnalysisResult
        fields = [
            "id",
            "health_score",
            "actions",
            "latitude",
            "longitude",
            "overlay_image_url",
            "original_image_url",
            "created_at",
        ]
