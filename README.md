# CropSight Platform

Django + DRF backend and a Vite + Tailwind React dashboard for agri-tech image analysis using Supabase Postgres and Supabase Storage.

## 1) Windows setup (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Update values in `.env`:

- `DATABASE_URL`: Supabase Postgres URL
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
- `SUPABASE_BUCKET_NAME`: `farm-images`

## 2) Run backend

```powershell
python manage.py migrate
python manage.py runserver
```

## 3) Run frontend (PowerShell)

```powershell
npm install
npm run dev
```

The dashboard will run at `http://127.0.0.1:5173`.

## 4) API endpoint

- `POST /api/analyze/`
- form-data fields:
  - `image` (file, required)
  - `farm_name` (string, optional)

Example with PowerShell curl:

```powershell
curl -Method Post -Uri http://127.0.0.1:8000/api/analyze/ -Form @{
  image = Get-Item ".\sample.jpg"
  farm_name = "Demo Farm"
}
```

## 5) Frontend features delivered

- `FarmMap.jsx`: initializes Leaflet `MapContainer`, loads historical records from Supabase (`AnalysisResult`, with fallback to `analyzer_analysisresult`), and renders color-coded markers:
  - Green: `health_score >= 75`
  - Yellow: `45 <= health_score < 75`
  - Red: `health_score < 45`
- `Dashboard.jsx`: uploads drone images to Django `POST /api/analyze/` via Axios and inserts the returned record into local state so the map updates instantly without refresh.
- Marker click interaction: opens the side panel with `overlay_image_url` preview and AI actions list.
