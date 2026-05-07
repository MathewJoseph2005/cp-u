# CropSight API – Testing Guide

## Status
✅ **Server is running on `http://127.0.0.1:8000`**

---

## Quick Access

- **Interactive Docs (Swagger UI)**: http://127.0.0.1:8000/docs
- **Alternative Docs (ReDoc)**: http://127.0.0.1:8000/redoc
- **Health Check**: http://127.0.0.1:8000/health

---

## Testing Endpoints

### 1. `POST /analyze` – Full-frame field crop analysis

**Description**: Upload a crop/field image. Returns ExG-based health segmentation (Healthy/Moderate/Critical), health score (0–100), and a base64 heatmap PNG.

**Using Swagger UI**:
1. Go to http://127.0.0.1:8000/docs
2. Click "Try it out" on `/analyze`
3. Click "Choose File" and select a crop/field image (JPG, PNG)
4. Click "Execute"

**Expected Response**:
```json
{
  "heatmap_base64": "iVBORw0KGgoAAAANS...",
  "health_score": 72.45,
  "summary": "Field scan indicates mostly healthy canopy with low stress signals.",
  "zones": {
    "healthy": 65.30,
    "moderate": 22.15,
    "critical": 12.55
  }
}
```

---

### 2. `POST /closeup` – Leaf-level diagnostic

**Description**: Upload a close-up leaf image. Focuses ExG analysis on the center 50% of the image for leaf-specific diagnostics.

**Using Swagger UI**:
1. Go to http://127.0.0.1:8000/docs
2. Click "Try it out" on `/closeup`
3. Upload a leaf image
4. Click "Execute"

**Expected Response**: (Same structure as `/analyze`, but summarized for leaf context)
```json
{
  "heatmap_base64": "iVBORw0KGgoAAAANS...",
  "health_score": 58.72,
  "summary": "Leaf close-up indicates mixed vegetation health; targeted intervention is recommended.",
  "zones": { ... }
}
```

---

### 3. `POST /tts` – Malayalam Text-to-Speech

**Description**: Send Malayalam text, receive a streaming MP3 audio file.

**Using cURL**:
```bash
curl -X POST "http://127.0.0.1:8000/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "നിങ്ങളുടെ വിളകൾ ആരോഗ്യകരമാണ്"}' \
  --output cropsight_audio.mp3
```

**Using Python**:
```python
import requests

url = "http://127.0.0.1:8000/tts"
payload = {"text": "നിങ്ങളുടെ വിളകൾ ആരോഗ്യകരമാണ്"}

response = requests.post(url, json=payload)
with open("cropsight_audio.mp3", "wb") as f:
    f.write(response.content)
print("Audio saved to cropsight_audio.mp3")
```

**Note**: gTTS requires an internet connection to synthesize audio.

---

## Color Map Interpretation

The heatmap uses the **JET color map**:
- 🔴 **Red** = Low ExG (Critical stress)
- 🟡 **Yellow** = Medium ExG (Moderate zones)
- 🟢 **Green** = High ExG (Healthy vegetation)

Higher ExG values (`2G - R - B`) indicate greener, healthier canopy.

---

## Error Handling

All endpoints return structured error responses:

```json
{
  "detail": "Only image uploads are supported."
}
```

Common status codes:
- `200`: Success
- `400`: Bad request (empty file, invalid format, invalid text)
- `422`: Validation error (missing fields)
- `500`: Server error
- `502`: TTS service unavailable (internet issue)

---

## Sample Images

To test `/analyze` and `/closeup`, use any RGB image:
- Agricultural field photos (JPG/PNG)
- Leaf close-ups
- Plant canopy photos

---

## Next Steps

1. ✅ Server is running
2. Open http://127.0.0.1:8000/docs to test interactively
3. Upload a crop or leaf image to `/analyze` or `/closeup`
4. Use `/tts` to generate Malayalam alerts
5. Integrate endpoints into your Agri-Tech frontend
