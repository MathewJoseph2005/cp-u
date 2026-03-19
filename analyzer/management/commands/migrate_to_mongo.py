from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from django.core.management.base import BaseCommand

from analyzer.models import AnalysisResult, ImageRecord, UserProfile
from analyzer.mongo import get_collections


def _to_utc(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class Command(BaseCommand):
    help = "Migrates existing Django (SQLite) analyzer data to MongoDB collections."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing Mongo analyzer collections before migrating.",
        )

    def handle(self, *args, **options):
        collections = get_collections()
        users_col = collections["users"]
        images_col = collections["image_records"]
        results_col = collections["analysis_results"]

        if options.get("clear"):
            users_col.delete_many({})
            images_col.delete_many({})
            results_col.delete_many({})
            self.stdout.write(self.style.WARNING("Cleared Mongo analyzer collections."))

        user_id_map = self._migrate_users(users_col)
        image_id_map = self._migrate_images(images_col, user_id_map)
        self._migrate_results(results_col, image_id_map, images_col)

        user_count = users_col.count_documents({})
        image_count = images_col.count_documents({})
        result_count = results_col.count_documents({})

        self.stdout.write(self.style.SUCCESS("Mongo migration completed successfully."))
        self.stdout.write(f"Users in Mongo: {user_count}")
        self.stdout.write(f"Image records in Mongo: {image_count}")
        self.stdout.write(f"Analysis results in Mongo: {result_count}")

    def _migrate_users(self, users_col) -> dict[int, Any]:
        user_id_map: dict[int, Any] = {}
        queryset: Iterable[UserProfile] = UserProfile.objects.all().iterator()

        for user in queryset:
            phone = (user.phone or "").strip()
            if not phone:
                self.stdout.write(self.style.WARNING(f"Skipping user {user.pk} without phone."))
                continue

            users_col.update_one(
                {"legacy_user_id": user.pk},
                {
                    "$set": {
                        "name": user.name,
                        "phone": phone,
                        "updated_at": datetime.now(timezone.utc),
                    },
                    "$setOnInsert": {
                        "legacy_user_id": user.pk,
                        "created_at": datetime.now(timezone.utc),
                    },
                },
                upsert=True,
            )

            user_doc = users_col.find_one({"legacy_user_id": user.pk}, {"_id": 1})
            if user_doc is None:
                self.stdout.write(self.style.WARNING(f"Could not map user {user.pk}."))
                continue

            user_id_map[user.pk] = user_doc["_id"]

        self.stdout.write(self.style.SUCCESS(f"Migrated/updated users: {len(user_id_map)}"))
        return user_id_map

    def _migrate_images(self, images_col, user_id_map: dict[int, Any]) -> dict[int, Any]:
        image_id_map: dict[int, Any] = {}
        queryset: Iterable[ImageRecord] = ImageRecord.objects.select_related("user").all().iterator()

        for image in queryset:
            mongo_user_id = user_id_map.get(image.user.pk)
            if mongo_user_id is None:
                self.stdout.write(self.style.WARNING(f"Skipping image {image.pk}: user mapping missing."))
                continue

            images_col.update_one(
                {"legacy_image_id": image.pk},
                {
                    "$set": {
                        "user_id": mongo_user_id,
                        "original_image_url": image.original_image_url,
                        "uploaded_at": _to_utc(image.uploaded_at),
                    },
                    "$setOnInsert": {
                        "legacy_image_id": image.pk,
                    },
                },
                upsert=True,
            )

            image_doc = images_col.find_one({"legacy_image_id": image.pk}, {"_id": 1})
            if image_doc is None:
                self.stdout.write(self.style.WARNING(f"Could not map image {image.pk}."))
                continue

            image_id_map[image.pk] = image_doc["_id"]

        self.stdout.write(self.style.SUCCESS(f"Migrated/updated image records: {len(image_id_map)}"))
        return image_id_map

    def _migrate_results(self, results_col, image_id_map: dict[int, Any], images_col) -> None:
        migrated = 0
        queryset: Iterable[AnalysisResult] = AnalysisResult.objects.select_related("image").all().iterator()

        for result in queryset:
            mongo_image_id = image_id_map.get(result.image.pk)
            if mongo_image_id is None:
                self.stdout.write(
                    self.style.WARNING(f"Skipping analysis result {result.pk}: image mapping missing.")
                )
                continue

            source_image = images_col.find_one({"_id": mongo_image_id}, {"original_image_url": 1}) or {}

            results_col.update_one(
                {"legacy_analysis_id": result.pk},
                {
                    "$set": {
                        "image_id": mongo_image_id,
                        "health_score": int(result.health_score),
                        "actions": result.actions if isinstance(result.actions, dict) else {},
                        "latitude": result.latitude,
                        "longitude": result.longitude,
                        "overlay_image_url": result.overlay_image_url,
                        "original_image_url": source_image.get("original_image_url"),
                        "camera_number": None,
                        "field_zone": None,
                        "created_at": _to_utc(result.created_at),
                    },
                    "$setOnInsert": {
                        "legacy_analysis_id": result.pk,
                    },
                },
                upsert=True,
            )
            migrated += 1

        self.stdout.write(self.style.SUCCESS(f"Migrated/updated analysis results: {migrated}"))
