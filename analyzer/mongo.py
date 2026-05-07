from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from django.conf import settings
from pymongo import ASCENDING, DESCENDING, MongoClient


_client: MongoClient[Any] | None = None


def get_client() -> MongoClient[Any]:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI)
    return _client


def get_db():
    return get_client()[settings.MONGODB_DB_NAME]


def get_collections() -> dict[str, Any]:
    db = get_db()
    users = db["users"]
    image_records = db["image_records"]
    analysis_results = db["analysis_results"]

    users.create_index([("phone", ASCENDING)], unique=True)
    analysis_results.create_index([("created_at", DESCENDING)])
    analysis_results.create_index([("camera_number", ASCENDING)])

    return {
        "users": users,
        "image_records": image_records,
        "analysis_results": analysis_results,
    }


def serialize_mongo_id(value: Any) -> str | Any:
    if isinstance(value, ObjectId):
        return str(value)
    return value


def to_iso(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return value


def serialize_user(user_doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": serialize_mongo_id(user_doc.get("_id")),
        "name": user_doc.get("name"),
        "phone": user_doc.get("phone"),
    }


def serialize_result(result_doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": serialize_mongo_id(result_doc.get("_id")),
        "health_score": result_doc.get("health_score"),
        "actions": result_doc.get("actions") or {},
        "ai_analysis": result_doc.get("ai_analysis") or {},
        "latitude": result_doc.get("latitude"),
        "longitude": result_doc.get("longitude"),
        "camera_number": result_doc.get("camera_number"),
        "field_zone": result_doc.get("field_zone"),
        "overlay_image_url": result_doc.get("overlay_image_url"),
        "original_image_url": result_doc.get("original_image_url"),
        "created_at": to_iso(result_doc.get("created_at")),
    }
