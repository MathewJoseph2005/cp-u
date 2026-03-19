
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
    overlay_image_url = upload_to_supabase(overlay)

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
