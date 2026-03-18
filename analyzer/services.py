
# pyright: reportMissingTypeStubs=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownReturnType=false
import os
import uuid
from io import BytesIO
from typing import Any, BinaryIO

import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import ExifTags, Image
from rest_framework.exceptions import ValidationError
from supabase import create_client


def read_image(file: BinaryIO) -> NDArray[np.uint8]:
    try:
        file.seek(0)
        raw = file.read()
        image = Image.open(BytesIO(raw)).convert("RGB")
    except Exception as exc:
        raise ValidationError("Invalid image file.") from exc

    rgb = np.array(image, dtype=np.uint8)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return bgr


def calculate_exg(image: NDArray[np.uint8]) -> NDArray[np.float32]:
    b = image[:, :, 0].astype(np.float32)
    g = image[:, :, 1].astype(np.float32)
    r = image[:, :, 2].astype(np.float32)
    return (2.0 * g) - r - b


def run_kmeans(exg: NDArray[np.float32]) -> NDArray[np.uint8]:
    flattened = exg.reshape((-1, 1)).astype(np.float32)
    if flattened.shape[0] < 3:
        raise ValidationError("Image is too small for clustering.")

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.2)
    best_labels = np.zeros((flattened.shape[0], 1), dtype=np.int32)
    _, labels, centers = cv2.kmeans(
        flattened,
        3,
        best_labels,
        criteria,
        10,
        cv2.KMEANS_PP_CENTERS,
    )

    vegetation_label = int(np.argmax(centers))
    mask = (labels.reshape(exg.shape) == vegetation_label).astype(np.uint8) * 255
    return mask


def create_overlay(image: NDArray[np.uint8], mask: NDArray[np.uint8]) -> NDArray[np.uint8]:
    color_mask = np.zeros_like(image)
    color_mask[:, :, 1] = mask
    return cv2.addWeighted(image, 0.75, color_mask, 0.25, 0)


def _dms_to_decimal(dms: Any, ref: str) -> float:
    def _to_float(value: Any) -> float:
        if hasattr(value, "numerator") and hasattr(value, "denominator"):
            return float(value.numerator) / float(value.denominator)
        if isinstance(value, (tuple, list)) and len(value) == 2:
            return float(value[0]) / float(value[1])
        return float(value)

    degrees = _to_float(dms[0])
    minutes = _to_float(dms[1])
    seconds = _to_float(dms[2])

    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ("S", "W"):
        decimal *= -1
    return decimal


def extract_gps(file: BinaryIO) -> tuple[float | None, float | None]:
    try:
        file.seek(0)
        raw = file.read()
        image = Image.open(BytesIO(raw))
        exif = image.getexif()
    except Exception:
        return None, None

    if not exif:
        return None, None

    gps_tag = None
    for tag_id, tag_name in ExifTags.TAGS.items():
        if tag_name == "GPSInfo":
            gps_tag = tag_id
            break

    if gps_tag is None or gps_tag not in exif:
        return None, None

    gps_info = exif.get(gps_tag)
    if not gps_info:
        return None, None

    gps_decoded = {}
    for key, value in gps_info.items():
        gps_decoded[ExifTags.GPSTAGS.get(key, key)] = value

    lat = gps_decoded.get("GPSLatitude")
    lat_ref = gps_decoded.get("GPSLatitudeRef")
    lon = gps_decoded.get("GPSLongitude")
    lon_ref = gps_decoded.get("GPSLongitudeRef")

    if not (lat and lat_ref and lon and lon_ref):
        return None, None

    try:
        return _dms_to_decimal(lat, lat_ref), _dms_to_decimal(lon, lon_ref)
    except Exception:
        return None, None


def resolve_location(
    file: BinaryIO,
    request_lat: float | str | None,
    request_lon: float | str | None,
) -> tuple[float, float]:
    exif_lat, exif_lon = extract_gps(file)
    if exif_lat is not None and exif_lon is not None:
        return exif_lat, exif_lon

    if request_lat is not None and request_lon is not None:
        lat = float(request_lat)
        lon = float(request_lon)

        if not (-90.0 <= lat <= 90.0):
            raise ValidationError("Latitude must be between -90 and 90.")
        if not (-180.0 <= lon <= 180.0):
            raise ValidationError("Longitude must be between -180 and 180.")

        return lat, lon

    raise ValidationError(
        "Location not found in EXIF and request latitude/longitude not provided."
    )


def upload_to_supabase(image_array: NDArray[np.uint8]) -> str:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValidationError("SUPABASE_URL and SUPABASE_KEY must be configured.")

    success, encoded = cv2.imencode(".jpg", image_array)
    if not success:
        raise ValidationError("Failed to encode image for upload.")

    client = create_client(supabase_url, supabase_key)
    file_name = f"{uuid.uuid4().hex}.jpg"

    try:
        bucket = client.storage.from_("farm-images")
        upload_result = bucket.upload(
            path=file_name,
            file=encoded.tobytes(),
            file_options={"content-type": "image/jpeg", "upsert": "true"},
        )
        if isinstance(upload_result, dict) and upload_result.get("error"):
            raise ValidationError(
                f"Failed to upload image to Supabase: {upload_result.get('error')}"
            )
        public_url = bucket.get_public_url(file_name)
    except Exception as exc:
        raise ValidationError(f"Failed to upload image to Supabase: {exc}") from exc

    if isinstance(public_url, dict):
        url = public_url.get("publicUrl") or public_url.get("public_url")
    else:
        url = str(public_url)

    if not url:
        raise ValidationError("Supabase did not return a public URL.")

    return url


def analyze_image(
    file: BinaryIO,
    request_lat: float | str | None,
    request_lon: float | str | None,
) -> dict[str, Any]:
    latitude, longitude = resolve_location(file, request_lat, request_lon)
    image = read_image(file)
    exg = calculate_exg(image)
    mask = run_kmeans(exg)
    overlay = create_overlay(image, mask)
    overlay_image_url = upload_to_supabase(overlay)

    vegetation_ratio = float(np.count_nonzero(mask)) / float(mask.size)
    health_score = int(max(0, min(100, round(vegetation_ratio * 100))))

    if health_score >= 70:
        recommendation = "Crop appears healthy. Continue current practices."
    elif health_score >= 40:
        recommendation = "Crop health is moderate. Monitor irrigation and nutrients."
    else:
        recommendation = "Crop health is low. Inspect soil, pests, and watering schedule."

    actions = {
        "recommendation": recommendation,
        "vegetation_ratio": round(vegetation_ratio, 4),
    }

    return {
        "health_score": health_score,
        "actions": actions,
        "latitude": latitude,
        "longitude": longitude,
        "overlay_image_url": overlay_image_url,
    }
