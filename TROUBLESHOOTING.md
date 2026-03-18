# CropSight Troubleshooting Guide

## Issue 1: Supabase 404 Error - "AnalysisResult" Table Not Found

### Error Message
```
wmwsyytzuvfymkmxiihm.supabase.co/rest/v1/AnalysisResult?select=*:1 
Failed to load resource: the server responded with a status of 404
```

### Root Cause
The frontend is trying to fetch from a Supabase table named `AnalysisResult`, but this table doesn't exist in your Supabase project yet.

### Solution

#### Step 1: Create the AnalysisResult Table in Supabase

1. Go to [Supabase Dashboard](https://app.supabase.com/)
2. Select your project
3. Click **SQL Editor** in the left sidebar
4. Click **New Query**
5. Paste the following SQL and run it:

```sql
-- Create AnalysisResult table
CREATE TABLE IF NOT EXISTS AnalysisResult (
  id BIGSERIAL PRIMARY KEY,
  health_score INTEGER NOT NULL,
  actions JSONB,
  latitude FLOAT8,
  longitude FLOAT8,
  overlay_image_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX idx_analysisresult_created_at ON AnalysisResult(created_at DESC);
```

#### Step 2: Enable Row Level Security (RLS)

1. In Supabase, go to **Authentication** > **Policies**
2. Select the `AnalysisResult` table
3. Click **New Policy**
4. Create a **SELECT** policy to allow public read access:
   - Allowed roles: anon
   - USING expression: `true`

This allows the frontend to fetch data without a login.

#### Step 3: Verify the Fix

1. Refresh your React app (Ctrl+Shift+Delete browser cache or use browser DevTools)
2. The Supabase 404 error should be gone
3. You may see an empty results list, which is correct (no analyses yet)

---

## Issue 2: Backend 400 Error - POST /api/analyze/ Bad Request

### Error Message
```
:5173/api/analyze/:1 Failed to load resource: the server responded with a status of 400 (Bad Request)
```

### Root Causes & Solutions

This error has several possible causes. Try these in order:

### Solution A: Set Backend Environment Variables

The backend services need Supabase credentials to upload images.

1. **Open or create** `.env` file in the project root:

```env
# Django Settings
DJANGO_SECRET_KEY=your-super-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Supabase Credentials (REQUIRED for image upload)
SUPABASE_URL=https://wmwsyytzuvfymkmxiihm.supabase.co  # Replace with your URL
SUPABASE_KEY=your-service-role-key-here  # Use SERVICE ROLE KEY (not anon key)
```

2. **Get your Supabase credentials:**
   - Go to [Supabase Dashboard](https://app.supabase.com/)
   - Click your project
   - Click **Settings** > **API**
   - Copy:
     - **Project URL** → `SUPABASE_URL`
     - **Service Role Secret** → `SUPABASE_KEY` (⚠️ Use SERVICE ROLE, not anon key)

3. **Restart the Django server:**
   ```bash
   python manage.py runserver
   ```

### Solution B: Verify Frontend Environment Variables

Ensure your `.env.local` is also set correctly:

```env
VITE_SUPABASE_URL=https://wmwsyytzuvfymkmxiihm.supabase.co
VITE_SUPABASE_KEY=your-anon-key-here
```

**Get anon key:**
- Supabase Dashboard > **Settings** > **API**
- Copy the **anon (public)** key

### Solution C: Check Form Data

The latitude/longitude fields might be sending empty strings instead of null values.

**Current form sends:**
```javascript
// This sends empty strings "" which fail validation
if (latitude.trim() && longitude.trim()) {
  formData.append("latitude", latitude.trim());
  formData.append("longitude", longitude.trim());
}
```

**Update Dashboard.jsx** to not send invalid coordinates:

```javascript
const formData = new FormData();
formData.append("image", image);
formData.append("name", name);
formData.append("phone", phone);

// Only add latitude/longitude if BOTH are valid numbers
if (latitude && longitude) {
  const lat = parseFloat(latitude);
  const lon = parseFloat(longitude);
  
  if (!isNaN(lat) && !isNaN(lon)) {
    formData.append("latitude", lat);
    formData.append("longitude", lon);
  }
}
```

### Solution D: Check Server Errors

The 400 error might have a detailed message. Check:

1. **Browser DevTools → Network Tab:**
   - Click the failed POST request to `/api/analyze/`
   - Click **Response** tab
   - Look for a `detail` field with error message

2. **Django Terminal Output:**
   - Check the terminal running `python manage.py runserver`
   - Look for exception traceback

3. **Check Services.py Requirements**

The `analyze_image()` service might be failing. File a detailed error report if you see:
```
Failed to analyze image.
```

---

## Quick Diagnosis Checklist

Run through this if you're still getting errors:

- [ ] ✅ Created `AnalysisResult` table in Supabase
- [ ] ✅ Set `SUPABASE_URL` in `.env` (backend)
- [ ] ✅ Set `SUPABASE_KEY` in `.env` (use SERVICE ROLE key)
- [ ] ✅ Set `VITE_SUPABASE_URL` in `.env.local` (frontend)
- [ ] ✅ Set `VITE_SUPABASE_KEY` in `.env.local` (use anon key)
- [ ] ✅ Restarted Django server
- [ ] ✅ Cleared browser cache (Ctrl+Shift+Delete)
- [ ] ✅ Check browser DevTools > Response tab for error details
- [ ] ✅ Check Django terminal for exception traceback

---

## Expected Behavior After Fixes

1. ✅ No 404 errors for Supabase
2. ✅ Form submits successfully (or shows specific validation error)
3. ✅ Image analyzed and uploaded to Supabase
4. ✅ Analysis result displayed on map
5. ✅ Result appears in the dashboard

---

## Still Having Issues?

If you've completed all steps above:

1. **Check exact error message:**
   - Browser DevTools > Network > Click failed request > **Response** tab
   - Copy the `detail` field exactly

2. **Check Django logs:**
   - Terminal running `python manage.py runserver`
   - Look for Python exception traceback

3. **Verify Supabase table:**
   - Supabase Dashboard > **Table Editor**
   - Should see `AnalysisResult` table with columns
   - RLS should allow public SELECT

4. **Test with curl (optional):**
   ```bash
   # Test if API accepts requests
   curl -X POST http://localhost:8000/api/analyze/ \
     -F "image=@/path/to/test/image.jpg" \
     -F "name=Test User" \
     -F "phone=1234567890"
   ```

---

## Key Differences: Service Role vs Anon Keys

- **Service Role Key** (SUPABASE_KEY in `.env` for **backend**)
  - Full database access
  - Can bypass RLS
  - **Keep secret!** Only on server
  
- **Anon Key** (VITE_SUPABASE_KEY in `.env.local` for **frontend**)
  - Limited access
  - Respects RLS policies
  - Safe to expose in frontend code

---

## React DevTools Notice (Not an Error)

```
Download the React DevTools for a better development experience
```

This is just a suggestion, not an error. You can ignore it or install [React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi) from Chrome Web Store for better debugging.
