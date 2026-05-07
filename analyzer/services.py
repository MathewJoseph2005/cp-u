<<<<<<< HEAD
import cv2
import numpy as np
import io
import uuid
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from django.conf import settings
from supabase import create_client, Client
from .models import UserProfile, ImageRecord, AnalysisResult

# Initialize Supabase Client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def read_image(image_file):
    """Reads image file into OpenCV format."""
    file_bytes = np.frombuffer(image_file.read(), np.uint8)
    image_file.seek(0)
    return cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

def calculate_exg(image):
    """Calculates Excess Green Index (2G - R - B)."""
    b, g, r = cv2.split(image.astype(np.float32))
    exg = 2 * g - r - b
    return cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

def run_kmeans(image, clusters=3):
    """Runs KMeans clustering on a grayscale or single-channel image."""
    pixel_values = image.reshape((-1, 1)).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_values, clusters, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    centers = np.uint8(centers)
    res = centers[labels.flatten()]
    return res.reshape(image.shape)

def create_overlay(original_image, processed_mask):
    """Creates a heat-map style overlay using cv2.addWeighted."""
    heatmap = cv2.applyColorMap(processed_mask, cv2.COLORMAP_JET)
    return cv2.addWeighted(original_image, 0.6, heatmap, 0.4, 0)

def _get_decimal_from_dms(dms, ref):
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0
    if ref in ['S', 'W']:
        return -(degrees + minutes + seconds)
    return degrees + minutes + seconds

def extract_gps(image_file):
    """Extracts GPS coordinates from image EXIF data."""
    try:
        img = Image.open(image_file)
        exif_data = img._getexif()
        image_file.seek(0)
        if not exif_data:
            return None

        gps_info = {}
        for tag, value in exif_data.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_info[sub_decoded] = value[t]

        if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
            lat = _get_decimal_from_dms(gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"])
            lon = _get_decimal_from_dms(gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"])
            return lat, lon
    except Exception:
        pass
    return None

def resolve_location(image_file, request_lat, request_lon):
    """Priority: EXIF > Request Params."""
    gps = extract_gps(image_file)
    if gps:
        return gps
    if request_lat is not None and request_lon is not None:
        return float(request_lat), float(request_lon)
    return None

def upload_to_supabase(image_array, bucket="farm-images"):
    """Encodes OpenCV image and uploads to Supabase bucket."""
    _, buffer = cv2.imencode('.jpg', image_array)
    file_name = f"{uuid.uuid4()}.jpg"
    
    supabase.storage.from_(bucket).upload(
        path=file_name,
        file=buffer.tobytes(),
        file_options={"content-type": "image/jpeg"}
    )
    
    return supabase.storage.from_(bucket).get_public_url(file_name)

def analyze_image(data):
    """Main service orchestration logic."""
    image_file = data['image']
    name = data['name']
    phone = data['phone']
    req_lat = data.get('latitude')
    req_lon = data.get('longitude')

    # Resolve Location
    location = resolve_location(image_file, req_lat, req_lon)
    if not location:
        raise ValueError("Location coordinates missing (EXIF or manual input required).")
    lat, lon = location

    # User Logic
    user, _ = UserProfile.objects.get_or_create(phone=phone, defaults={'name': name})

    # Read and Upload Original
    cv_img = read_image(image_file)
    original_url = upload_to_supabase(cv_img)
    image_record = ImageRecord.objects.create(user=user, original_image_url=original_url)

    # Image Processing
    exg = calculate_exg(cv_img)
    clustered = run_kmeans(exg)
    overlay = create_overlay(cv_img, clustered)
    overlay_url = upload_to_supabase(overlay)

    # Health Scoring Logic (Simplified)
    health_score = int(np.mean(exg) / 255 * 100)
    actions = {
        "irrigation": "required" if health_score < 40 else "optimal",
        "fertilizer": "apply nitrogen" if health_score < 60 else "not required"
    }

    # Save Result
    result = AnalysisResult.objects.create(
        image=image_record,
        health_score=health_score,
        actions=actions,
        latitude=lat,
        longitude=lon,
        overlay_image_url=overlay_url
    )

    return result
=======

# pyright: reportMissingTypeStubs=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownReturnType=false
import base64
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from io import BytesIO
from typing import Any, BinaryIO

import cv2
import numpy as np
from numpy.typing import NDArray
from django.conf import settings
from PIL import ExifTags, Image
from rest_framework.exceptions import ValidationError
from supabase import create_client

try:
    from camb.client import CambAI as CambSDKClient, save_stream_to_file  # pyright: ignore[reportMissingImports]
    from camb.types import StreamTtsOutputConfiguration  # pyright: ignore[reportMissingImports]
except ImportError:
    CambSDKClient = None
    save_stream_to_file = None
    StreamTtsOutputConfiguration = None

try:
    from cambai import CambAI as CambAIClient  # pyright: ignore[reportMissingImports]
except ImportError:
    CambAIClient = None


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


def _calculate_class_ratios(class_map: NDArray[np.uint8]) -> dict[str, float]:
    total_pixels = float(class_map.size)
    return {
        "red_ratio": float(np.count_nonzero(class_map == 0)) / total_pixels,
        "yellow_ratio": float(np.count_nonzero(class_map == 1)) / total_pixels,
        "green_ratio": float(np.count_nonzero(class_map == 2)) / total_pixels,
    }


def _classify_by_quantiles(index_map: NDArray[np.float32]) -> tuple[NDArray[np.uint8], dict[str, float]]:
    q1 = float(np.quantile(index_map, 0.33))
    q2 = float(np.quantile(index_map, 0.66))

    class_map = np.zeros(index_map.shape, dtype=np.uint8)
    class_map[index_map >= q1] = 1
    class_map[index_map >= q2] = 2

    return class_map, _calculate_class_ratios(class_map)


def _classify_by_rank(index_map: NDArray[np.float32]) -> tuple[NDArray[np.uint8], dict[str, float]]:
    """
    Force a visible 3-zone split by ranking pixels and assigning thirds.
    This guarantees red/yellow/green presence even when index contrast is weak.
    """
    flat = index_map.reshape(-1)
    n = flat.size

    # Stable sort keeps behavior deterministic when many values are equal.
    order = np.argsort(flat, kind="mergesort")

    class_flat = np.zeros(n, dtype=np.uint8)
    one_third = n // 3
    two_third = (2 * n) // 3

    class_flat[order[:one_third]] = 0
    class_flat[order[one_third:two_third]] = 1
    class_flat[order[two_third:]] = 2

    class_map = class_flat.reshape(index_map.shape)
    return class_map, _calculate_class_ratios(class_map)


def calculate_ndvi(image: NDArray[np.uint8]) -> tuple[NDArray[np.float32], str]:
    """
    Computes an index map with adaptive method selection:
    - NIR monochrome mode (single-band-like): intensity-based map with dynamic range stretch
    - visible proxy: (G - R) / (G + R)
    - NIR false-color proxy: (R - B) / (R + B)

    The variant with higher spatial variance is chosen per-image.
    """
    b = image[:, :, 0].astype(np.float32)
    g = image[:, :, 1].astype(np.float32)
    r = image[:, :, 2].astype(np.float32)
    eps = 1e-6

    # Detect near-monochrome NIR frames where channels are very similar.
    channel_delta = float(np.mean(np.abs(r - g)) + np.mean(np.abs(r - b)) + np.mean(np.abs(g - b))) / 3.0
    if channel_delta < 6.0:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
        p2 = float(np.percentile(gray, 2))
        p98 = float(np.percentile(gray, 98))
        denom = max(p98 - p2, 1e-6)
        normalized = np.clip((gray - p2) / denom, 0.0, 1.0)
        # map to [-1, 1] so downstream clustering/scoring remains consistent
        nir_index = (normalized * 2.0) - 1.0
        return nir_index.astype(np.float32), "NIR_intensity_stretch"

    visible_proxy = (g - r) / (g + r + eps)
    nir_false_color_proxy = (r - b) / (r + b + eps)

    visible_var = float(np.nanstd(visible_proxy))
    nir_var = float(np.nanstd(nir_false_color_proxy))

    if nir_var > visible_var:
        return nir_false_color_proxy.astype(np.float32), "NDVI_proxy_(R-B)/(R+B)"

    return visible_proxy.astype(np.float32), "NDVI_proxy_(G-R)/(G+R)"


def run_kmeans(index_map: NDArray[np.float32]) -> tuple[NDArray[np.uint8], dict[str, float]]:
    if float(np.nanstd(index_map)) < 1e-4:
        return _classify_by_rank(index_map)

    flattened = index_map.reshape((-1, 1)).astype(np.float32)
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

    label_map = labels.reshape(index_map.shape)

    # Order clusters by index center: low -> stressed (red), mid -> moderate (yellow), high -> healthy (green)
    sorted_cluster_indices = np.argsort(centers.flatten())
    red_cluster = int(sorted_cluster_indices[0])
    yellow_cluster = int(sorted_cluster_indices[1])
    green_cluster = int(sorted_cluster_indices[2])

    class_map = np.zeros_like(label_map, dtype=np.uint8)
    class_map[label_map == red_cluster] = 0
    class_map[label_map == yellow_cluster] = 1
    class_map[label_map == green_cluster] = 2

    ratios = _calculate_class_ratios(class_map)

    if max(ratios.values()) > 0.97:
        quantile_map, quantile_ratios = _classify_by_quantiles(index_map)
        # If quantile split still collapses because values are too flat/tied,
        # force a rank-balanced segmentation.
        if max(quantile_ratios.values()) > 0.97:
            return _classify_by_rank(index_map)
        return quantile_map, quantile_ratios

    return class_map, ratios


def create_overlay(image: NDArray[np.uint8], index_map: NDArray[np.float32], index_method: str) -> NDArray[np.uint8]:
    """
    Render a smooth red-yellow-green heatmap from continuous vegetation index values.
    This avoids blocky class-grid visuals while keeping clustering for scoring metrics.
    """
    finite_mask = np.isfinite(index_map)
    if not np.any(finite_mask):
        return image.copy()

    valid_values = index_map[finite_mask]
    low = float(np.percentile(valid_values, 2))
    high = float(np.percentile(valid_values, 98))
    if high <= low:
        high = low + 1e-6

    normalized = np.clip((index_map - low) / (high - low), 0.0, 1.0)

    if index_method.startswith("NIR_"):
        # Boost local contrast for NIR to avoid flat/single-color heatmaps.
        normalized_u8 = np.clip(normalized * 255.0, 0, 255).astype(np.uint8)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced_u8 = clahe.apply(normalized_u8)
        normalized = enhanced_u8.astype(np.float32) / 255.0

    # Smooth for natural gradients while preserving transitions.
    blur_sigma = 0.8 if index_method.startswith("NIR_") else 1.2
    normalized_blur = cv2.GaussianBlur(normalized.astype(np.float32), (0, 0), blur_sigma)

    # Build continuous RYG gradient in BGR space.
    b = np.zeros_like(normalized_blur, dtype=np.float32)
    g = np.zeros_like(normalized_blur, dtype=np.float32)
    r = np.zeros_like(normalized_blur, dtype=np.float32)

    lower_half = normalized_blur <= 0.5
    upper_half = ~lower_half

    # 0.0 -> 0.5 : red (255,0,0) to yellow (255,255,0)
    g[lower_half] = normalized_blur[lower_half] * 2.0
    r[lower_half] = 1.0

    # 0.5 -> 1.0 : yellow (255,255,0) to green (0,255,0)
    g[upper_half] = 1.0
    r[upper_half] = 1.0 - ((normalized_blur[upper_half] - 0.5) * 2.0)

    color_mask = np.stack([b, g, r], axis=-1)
    color_mask_u8 = np.clip(color_mask * 255.0, 0, 255).astype(np.uint8)

    return cv2.addWeighted(image, 0.62, color_mask_u8, 0.38, 0)


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
    *,
    require_location: bool = True,
) -> tuple[float | None, float | None]:
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

    if require_location:
        raise ValidationError(
            "Location not found in EXIF and request latitude/longitude not provided."
        )

    return None, None


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


def save_image_locally(image_array: NDArray[np.uint8], subfolder: str = "uploads") -> str:
    media_root = str(settings.MEDIA_ROOT)
    upload_dir = os.path.join(media_root, subfolder)
    os.makedirs(upload_dir, exist_ok=True)

    file_name = f"{uuid.uuid4().hex}.jpg"
    file_path = os.path.join(upload_dir, file_name)

    success = cv2.imwrite(file_path, image_array)
    if not success:
        raise ValidationError("Failed to save image locally.")

    return f"{settings.MEDIA_URL}{subfolder}/{file_name}"


def _default_farmer_tips(health_score: int) -> tuple[list[str], list[str], str]:
    if health_score >= 70:
        summary = "Crop condition appears healthy in the mathematical analysis."
        guidance = [
            "Keep irrigation schedule consistent and avoid overwatering.",
            "Maintain current nutrient plan with periodic soil checks.",
            "Continue weekly scouting for early pest detection.",
        ]
    elif health_score >= 40:
        summary = "Crop condition appears moderate and can be improved with timely intervention."
        guidance = [
            "Review irrigation uniformity and reduce dry stress spots.",
            "Apply balanced nutrients based on soil and leaf status.",
            "Inspect for weeds and early pest signs every 3-4 days.",
        ]
    else:
        summary = "Crop condition appears weak and needs corrective action quickly."
        guidance = [
            "Check soil moisture and root zone immediately.",
            "Run targeted nutrient correction, especially nitrogen and micronutrients.",
            "Perform intensive pest and disease scouting and act early.",
        ]

    maintenance = [
        "Record observations weekly and compare with image history.",
        "Calibrate irrigation and spraying tools before field operations.",
        "Remove visibly damaged plants/leaves to reduce disease spread.",
    ]
    return guidance, maintenance, summary


def _fallback_ai_analysis(
    mathematical_analysis: dict[str, Any],
    camera_number: int | None,
    field_zone: str | None,
    latitude: float | None,
    longitude: float | None,
) -> dict[str, Any]:
    health_score = int(mathematical_analysis.get("health_score", 0))
    guidance, maintenance, summary = _default_farmer_tips(health_score)

    # Do not auto-accept as field using camera metadata alone.
    # Field detection must come from the AI model response.
    object_type = "unknown"
    is_field_image = None
    confidence = 0.2

    return {
        "provider": "local-fallback",
        "model": None,
        "is_field_image": is_field_image,
        "object_type": object_type,
        "confidence": confidence,
        "summary": summary,
        "farmer_guidance": guidance,
        "maintenance_tips": maintenance,
        "raw": None,
    }


def _extract_json_text(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
    return text


def _get_env_value(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()

    # Some environments may carry accidental whitespace in env keys.
    normalized_env = {key.strip(): value for key, value in os.environ.items()}
    for name in names:
        value = normalized_env.get(name)
        if value and value.strip():
            return value.strip()
    return ""


def _coerce_is_field_image(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "y", "1", "field", "crop_field"}:
            return True
        if normalized in {"false", "no", "n", "0", "non-field", "non_field", "not_field", "unknown", "none", "null", ""}:
            return False if normalized in {"false", "no", "n", "0", "non-field", "non_field", "not_field"} else None

    return None


def estimate_field_likelihood(image_bytes: bytes) -> dict[str, float | bool]:
    """
    Lightweight visual heuristic for field detection.
    Used as a safety fallback when AI response is uncertain.
    """
    try:
        buffer = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            return {
                "likely_field": False,
                "green_ratio": 0.0,
                "soil_ratio": 0.0,
                "field_score": 0.0,
            }

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Vegetation-ish hues.
        green_mask = cv2.inRange(hsv, np.array([25, 35, 25]), np.array([95, 255, 255]))

        # Soil-ish hues (brown/yellow-dirt range).
        soil_mask_1 = cv2.inRange(hsv, np.array([5, 30, 20]), np.array([25, 255, 220]))
        soil_mask_2 = cv2.inRange(hsv, np.array([0, 20, 10]), np.array([10, 200, 180]))
        soil_mask = cv2.bitwise_or(soil_mask_1, soil_mask_2)

        total_pixels = float(image.shape[0] * image.shape[1])
        green_ratio = float(np.count_nonzero(green_mask)) / max(total_pixels, 1.0)
        soil_ratio = float(np.count_nonzero(soil_mask)) / max(total_pixels, 1.0)

        # Encourage mixed green + soil patterns common in fields.
        field_score = (green_ratio * 0.75) + (soil_ratio * 0.35)
        likely_field = bool(
            (green_ratio >= 0.12 and (green_ratio + soil_ratio) >= 0.22)
            or field_score >= 0.20
        )

        return {
            "likely_field": likely_field,
            "green_ratio": round(green_ratio, 4),
            "soil_ratio": round(soil_ratio, 4),
            "field_score": round(field_score, 4),
        }
    except Exception:
        return {
            "likely_field": False,
            "green_ratio": 0.0,
            "soil_ratio": 0.0,
            "field_score": 0.0,
        }


def generate_grok_ai_analysis(
    image_bytes: bytes,
    mathematical_analysis: dict[str, Any],
    camera_number: int | None,
    field_zone: str | None,
    latitude: float | None,
    longitude: float | None,
) -> dict[str, Any]:
    api_key = _get_env_value(
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
        "XAI_API_KEY",
    )
    if not api_key:
        return _fallback_ai_analysis(
            mathematical_analysis,
            camera_number,
            field_zone,
            latitude,
            longitude,
        )

    model = _get_env_value("GEMINI_MODEL") or "gemini-1.5-flash"
    base_url = _get_env_value("GEMINI_API_URL") or "https://generativelanguage.googleapis.com/v1beta/models"
    endpoint = f"{base_url.rstrip('/')}/{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(api_key)}"

    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    context = {
        "health_score": mathematical_analysis.get("health_score"),
        "actions": mathematical_analysis.get("actions"),
        "camera_number": camera_number,
        "field_zone": field_zone,
        "latitude": latitude,
        "longitude": longitude,
    }

    prompt = (
        "You are an agronomy assistant. Analyze the image and combine your visual reasoning "
        "with the provided mathematical crop metrics. Return ONLY valid JSON with keys: "
        "is_field_image (boolean), object_type (string), confidence (0-1 number), summary (string), "
        "farmer_guidance (array of strings), maintenance_tips (array of strings). "
        "If image is not an agricultural field, explain object_type and provide safe generic advice. "
        f"Context: {json.dumps(context)}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": encoded_image,
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            raw_payload = response.read().decode("utf-8")
        parsed = json.loads(raw_payload)

        content = (
            parsed.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        content_json = json.loads(_extract_json_text(str(content)))

        guidance = content_json.get("farmer_guidance")
        maintenance = content_json.get("maintenance_tips")
        if not isinstance(guidance, list):
            guidance = []
        if not isinstance(maintenance, list):
            maintenance = []

        return {
            "provider": "gemini",
            "model": model,
            "is_field_image": _coerce_is_field_image(content_json.get("is_field_image")),
            "object_type": str(content_json.get("object_type", "unknown")),
            "confidence": float(content_json.get("confidence", 0.0)),
            "summary": str(content_json.get("summary", "")),
            "farmer_guidance": [str(item) for item in guidance],
            "maintenance_tips": [str(item) for item in maintenance],
            "raw": None,
        }
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError, ValueError):
        fallback = _fallback_ai_analysis(
            mathematical_analysis,
            camera_number,
            field_zone,
            latitude,
            longitude,
        )
        fallback["provider"] = "gemini-fallback"
        fallback["model"] = model
        return fallback


def analyze_image(
    file: BinaryIO,
    request_lat: float | str | None,
    request_lon: float | str | None,
    *,
    require_location: bool = True,
) -> dict[str, Any]:
    latitude, longitude = resolve_location(
        file,
        request_lat,
        request_lon,
        require_location=require_location,
    )
    image = read_image(file)
    ndvi_map, index_method = calculate_ndvi(image)
    class_map, ratios = run_kmeans(ndvi_map)
    overlay = create_overlay(image, ndvi_map, index_method)
    try:
        overlay_image_url = upload_to_supabase(overlay)
    except ValidationError:
        overlay_image_url = save_image_locally(overlay, "overlays")

    # Weighted score: green contributes most, yellow partially, red none.
    vegetation_ratio = ratios["green_ratio"] + (0.5 * ratios["yellow_ratio"])
    health_score = int(max(0, min(100, round(vegetation_ratio * 100))))

    if health_score >= 70:
        recommendation = "Crop appears healthy. Continue current practices."
    elif health_score >= 40:
        recommendation = "Crop health is moderate. Monitor irrigation and nutrients."
    else:
        recommendation = "Crop health is low. Inspect soil, pests, and watering schedule."

    actions = {
        "recommendation": recommendation,
        "index_method": index_method,
        "vegetation_ratio": round(vegetation_ratio, 4),
        "green_ratio": round(ratios["green_ratio"], 4),
        "yellow_ratio": round(ratios["yellow_ratio"], 4),
        "red_ratio": round(ratios["red_ratio"], 4),
    }

    return {
        "health_score": health_score,
        "actions": actions,
        "latitude": latitude,
        "longitude": longitude,
        "overlay_image_url": overlay_image_url,
    }


def synthesize_report_tts(
    text: str,
    *,
    voice_id: int = 147320,
    language: str = "en-us",
    speech_model: str = "mars-flash",
    output_format: str = "mp3",
) -> dict[str, Any]:
    cleaned_text = str(text).strip()
    if len(cleaned_text) < 3:
        raise ValidationError("Text must be at least 3 characters for TTS.")

    api_key = _get_env_value("CAMB_API_KEY")
    if not api_key:
        raise ValidationError("CAMB_API_KEY is not configured.")

    sdk_style_available = (
        CambSDKClient is not None
        and save_stream_to_file is not None
        and StreamTtsOutputConfiguration is not None
    )

    if not sdk_style_available and CambAIClient is None:
        raise ValidationError("CAMB SDK is not installed (install `cambai` or `camb-ai`).")

    normalized_format = str(output_format).strip().lower() or "mp3"
    if normalized_format not in {"mp3", "wav", "pcm_s16le"}:
        normalized_format = "mp3"

    audio_bytes: bytes

    if sdk_style_available:
        client = CambSDKClient(api_key=api_key)
        stream = client.text_to_speech.tts(
            text=cleaned_text,
            voice_id=int(voice_id),
            language=language,
            speech_model=speech_model,
            output_configuration=StreamTtsOutputConfiguration(format=normalized_format),
        )

        suffix = ".wav" if normalized_format == "wav" else ".mp3"
        if normalized_format == "pcm_s16le":
            suffix = ".pcm"

        fd, temp_path = tempfile.mkstemp(prefix="cropsight_tts_", suffix=suffix)
        os.close(fd)

        try:
            save_stream_to_file(stream, temp_path)
            with open(temp_path, "rb") as file_obj:
                audio_bytes = file_obj.read()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    else:
        # Fallback for currently installable 'cambai' package.
        # It writes a wav file to output_directory using task polling APIs.
        language_id = 1
        normalized_lang = language.strip().lower()
        if normalized_lang.startswith("en"):
            language_id = 1

        client = CambAIClient(api_key=api_key)
        task_info = client.create_tts(
            text=cleaned_text,
            voice_id=int(voice_id),
            language=language_id,
        )
        task_id = str(task_info.get("task_id", "")).strip()
        if not task_id:
            raise ValidationError("CAMB TTS did not return a task_id.")

        run_id: int | None = task_info.get("run_id")
        max_attempts = 15
        for _ in range(max_attempts):
            status_info = client.get_tts_status(task_id)
            status_value = str(status_info.get("status", "")).upper()
            run_id = status_info.get("run_id") or run_id

            if status_value == "SUCCESS" and run_id is not None:
                break
            if status_value in {"ERROR", "TIMEOUT", "PAYMENT_REQUIRED"}:
                reason = status_info.get("exception_reason")
                raise ValidationError(
                    f"CAMB TTS task failed with status {status_value}. {reason or ''}".strip()
                )

            import time

            time.sleep(2)

        if run_id is None:
            raise ValidationError("CAMB TTS timed out before returning run_id.")

        temp_dir = tempfile.mkdtemp(prefix="cropsight_tts_")
        temp_path = os.path.join(temp_dir, f"tts_stream_{run_id}.wav")

        try:
            client.get_tts_result(int(run_id), output_directory=temp_dir)
            if not os.path.exists(temp_path):
                raise ValidationError("CAMB TTS result file was not generated.")

            with open(temp_path, "rb") as file_obj:
                audio_bytes = file_obj.read()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.isdir(temp_dir):
                os.rmdir(temp_dir)

        # cambai fallback currently returns wav stream.
        normalized_format = "wav"

    mime_type = "audio/mpeg"
    if normalized_format == "wav":
        mime_type = "audio/wav"
    if normalized_format == "pcm_s16le":
        mime_type = "audio/L16"

    return {
        "provider": "camb-ai",
        "voice_id": int(voice_id),
        "language": language,
        "speech_model": speech_model,
        "format": normalized_format,
        "mime_type": mime_type,
        "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
    }
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
