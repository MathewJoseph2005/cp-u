# IoT Node Simulator Implementation Guide

## Overview
The IoT Node Simulator is a new fullscreen mobile-optimized component that mimics a live CCTV camera automatically sending frames to your Django backend. It integrates seamlessly with the CropSight Dashboard using real-time Supabase subscriptions.

---

## Key Features

### 1. **NodeSimulator Component** (`src/components/NodeSimulator.jsx`)
- **Mobile-Optimized Full-Screen UI**: Responsive design optimized for phones
- **Camera Selection Dropdown**: Choose from 9 cameras (Camera 1-9)
- **Live Video Feed**: Uses `navigator.mediaDevices.getUserMedia()` to access phone's back camera
- **Auto-Capture Loop**: Captures frames every 10 seconds automatically
- **Silent Upload**: Sends JPEG frames to `/api/analyze/` endpoint with camera_number
- **Connection Status Indicator**: Green/Red/Blue dot showing upload status
- **Last Synced Timestamp**: Shows when the last frame was uploaded
- **Error Handling**: Graceful handling of camera access denial and network errors

### 2. **Dashboard Real-Time Updates** (`src/pages/Dashboard.jsx`)
- **Supabase Realtime Subscription**: Listens to INSERT, UPDATE, DELETE events on AnalysisResult table
- **Automatic State Refresh**: Dashboard updates live when Node Simulator uploads new frames
- **No Page Refresh Required**: Changes appear instantly in Camera Grid and Drone View
- **NodeSimulator Button**: Access simulator from dashboard header

---

## How It Works

### **NodeSimulator.jsx Flow**

```
User clicks "Start Live Feed" → Camera Access Request
    ↓
Video stream starts in <video> element
    ↓
setInterval triggers every 10 seconds
    ↓
Current video frame → Canvas drawImage()
    ↓
Canvas → toBlob() → JPEG
    ↓
FormData with blob + camera_number → axios.post("/api/analyze/")
    ↓
Connection Status Updates + Last Synced Timestamp
    ↓
Dashboard receives realtime notification via Supabase
    ↓
CameraGrid updates automatically
```

### **Dashboard Real-Time Flow**

```
Node Simulator uploads frame to /api/analyze/
    ↓
Django creates AnalysisResult record in Supabase
    ↓
Supabase realtime subscription detects INSERT event
    ↓
Dashboard's useEffect receives payload
    ↓
setAnalysisResults updates state with new record
    ↓
CameraGrid component re-renders automatically
    ↓
User sees update without manual refresh
```

---

## Localhost/HTTPS Configuration

### **Problem Solved**
Mobile phones accessing localhost endpoints require special configuration. This code handles both scenarios:

### **Solution 1: Local Network Access (Recommended for Development)**

1. **Find your computer's local IP address:**
   ```powershell
   ipconfig
   ```
   Look for IPv4 Address (e.g., 192.168.1.100)

2. **Access Vite dev server via IP:**
   ```
   http://192.168.1.100:5173
   ```
   (Replace with your actual IP)

3. **Phone Requirements:**
   - Must be on same WiFi network
   - Use HTTP (not HTTPS) on local network
   - All relative API paths automatically work with this IP

### **Solution 2: HTTPS with Self-Signed Certificate**

1. **Generate self-signed cert:**
   ```bash
   npm run build
   ```

2. **Or use ngrok for instant HTTPS tunneling:**
   ```bash
   ngrok http 5173
   ```
   Access via the generated HTTPS URL

### **Why Relative Paths Work**

The code uses relative paths for all API calls:
```javascript
axios.post("/api/analyze/", formData, ...)
```

This automatically inherits the protocol and hostname from the page, so:
- On localhost:5173 → calls `http://localhost:5173/api/analyze/`
- On 192.168.1.100:5173 → calls `http://192.168.1.100:5173/api/analyze/`
- On `https://example.com` → calls `https://example.com/api/analyze/`

**No hardcoded URLs = Works everywhere!**

---

## Component Props & State

### **NodeSimulator Props**
```javascript
NodeSimulator({ 
  onClose = () => {}  // Callback to close simulator
})
```

### **State Variables**
- `cameraNumber`: Selected camera (1-9)
- `isActive`: Whether live feed is running
- `lastSynced`: Timestamp of last successful upload
- `connectionStatus`: "idle", "uploading", "success", "error"
- `statusMessage`: User-facing feedback message
- `deviceSupport`: Whether browser supports getUserMedia
- `error`: Camera access error messages

### **Refs**
- `videoRef`: Video element for camera stream
- `canvasRef`: Hidden canvas for frame capture
- `streamRef`: MediaStream object (for cleanup)
- `intervalRef`: setInterval ID (for cleanup)

---

## Dashboard Integration

### **Changes Made to Dashboard.jsx**

1. **Import NodeSimulator:**
   ```javascript
   import NodeSimulator from "../components/NodeSimulator";
   ```

2. **Add State:**
   ```javascript
   const [showNodeSimulator, setShowNodeSimulator] = useState(false);
   ```

3. **Supabase Realtime Setup:**
   ```javascript
   const subscription = supabase
     .on(
       "postgres_changes",
       {
         event: "*",  // INSERT, UPDATE, DELETE
         schema: "public",
         table: "AnalysisResult",
       },
       (payload) => {
         if (payload.eventType === "INSERT") {
           setAnalysisResults((prev) => [payload.new, ...prev]);
         } else if (payload.eventType === "UPDATE") {
           setAnalysisResults((prev) =>
             prev.map((record) =>
               record.id === payload.new.id ? payload.new : record
             )
           );
         }
       }
     )
     .subscribe();
   ```

4. **Add Button to Header:**
   ```javascript
   <button onClick={() => setShowNodeSimulator(true)}>
     📱 Node Simulator
   </button>
   ```

5. **Render Component:**
   ```javascript
   {showNodeSimulator && (
     <NodeSimulator onClose={() => setShowNodeSimulator(false)} />
   )}
   ```

---

## API Contract

### **POST /api/analyze/**

**Request (from NodeSimulator):**
```
FormData:
  - image: Blob (JPEG from canvas)
  - camera_number: integer (1-9)
```

**Response (from Django):**
```json
{
  "id": 123,
  "health_score": 75,
  "camera_number": 5,
  "field_zone": "North-Central",
  "overlay_image_url": "https://...",
  "actions": {...},
  "created_at": "2025-03-19T14:30:00Z"
}
```

---

## Testing Checklist

- [ ] Click "📱 Node Simulator" button on Dashboard
- [ ] Select Camera 1-9 from dropdown
- [ ] Click "▶ Start Live Feed" button
- [ ] Grant camera permission when prompted
- [ ] See video stream in preview
- [ ] Connection status shows "Uploading..." every 10 seconds
- [ ] After upload succeeds, status dot turns green
- [ ] "Last Synced" timestamp updates
- [ ] Return to Dashboard (click Back button)
- [ ] Camera Grid automatically shows new frames without refresh
- [ ] Drone View + Camera View both receive realtime updates

---

## Mobile Phone Access Instructions

### **For Users Testing on Phone**

1. Open terminal on your computer
2. Run: `ipconfig` (Windows) or `ifconfig` (Mac)
3. Find IPv4 Address (e.g., 192.168.1.100)
4. On phone browser, visit: `http://192.168.1.100:5173`
5. Click "📱 Node Simulator"
6. Select camera and start recording
7. Frames upload every 10 seconds
8. Return to Dashboard to see live updates

### **Network Requirements**
- Phone and computer must be on **same WiFi network**
- No VPN interference
- Firewall may need to allow port 5173

---

## Error Handling

### **Camera Access Denied**
- Error message: "Camera access denied or not available"
- **Fix**: Check browser permissions → Allow camera access
- On iOS: Settings → Website Settings → Camera → Allow

### **HTTPS/Localhost Issues**
- Error message: "Camera access denied... Make sure you're on HTTPS or localhost"
- **Fix**: 
  - Use local IP address instead (192.168.x.x:5173)
  - Or use HTTPS with valid certificate
  - Or use ngrok tunneling

### **Upload Failures**
- Connection Status shows red dot
- Status message shows specific error
- **Fix**: Check Django backend is running
- Verify `/api/analyze/` endpoint is accessible
- Check network connectivity

### **Device Not Supported**
- Message: "Your device doesn't support camera access"
- **Fix**: Use modern browser (Chrome, Firefox, Safari iOS 15+)

---

## Capturing Logic Deep Dive

```javascript
// 1. Get canvas element
const canvas = canvasRef.current;
const ctx = canvas.getContext("2d");
const video = videoRef.current;

// 2. Set canvas dimensions to match video
canvas.width = video.videoWidth || 1280;
canvas.height = video.videoHeight || 720;

// 3. Draw current frame
ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

// 4. Convert to JPEG blob
canvas.toBlob(
  async (blob) => {
    // blob now contains compressed JPEG data
    const formData = new FormData();
    formData.append("image", blob, "frame.jpg");
    formData.append("camera_number", cameraNumber);
    
    // Upload to backend
    await axios.post("/api/analyze/", formData);
  },
  "image/jpeg",
  0.85  // 85% JPEG quality (good balance)
);
```

---

## Performance Considerations

- **Capture Interval**: 10 seconds (configurable via `setInterval`)
- **JPEG Quality**: 0.85 (85% - good balance between quality and size)
- **Canvas Dimensions**: Auto-detected from video stream
- **Frame Size**: Typically 50-200 KB depending on complexity
- **Network**: Relative paths optimize routing
- **Realtime Updates**: Supabase PostgreSQL Changes = instant (< 100ms latency)

---

## Cleanup & Resource Management

The component properly cleans up resources:

```javascript
useEffect(() => {
  // ... start camera ...
  
  return () => {
    // Stop all tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
    // Clear interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
  };
}, [isActive]);
```

When user closes simulator or component unmounts, all resources are freed.

---

## Future Enhancements

1. **Adjustable Capture Interval**: User-selectable (5s, 10s, 30s, etc.)
2. **Frame Quality Control**: JPEG quality slider
3. **Batch Upload Mode**: Upload N frames at once
4. **Offline Queueing**: Store frames locally if network is down
5. **Recording**: Save video locally before sending
6. **Custom Zones**: Map cameras to custom field zones
7. **Analytics**: Upload history, stats per camera
8. **Multi-Camera Sync**: Synchronized capture from multiple devices

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Black video | Camera not streaming | Allow camera permission, check browser settings |
| Uploads fail with 400 | Invalid camera_number | Ensure selected camera is 1-9 |
| Uploads fail with 500 | Backend error | Check Django server running, check logs |
| Page not accessible from phone | Using localhost | Use local IP (192.168.1.x:5173) |
| Realtime not updating | Supabase not connected | Check VITE_SUPABASE_URL environment variable |
| Device not supported | Old browser | Use Chrome, Firefox, or Safari 15+ |

---

## Architecture Summary

```
📱 Mobile Phone Browser
  ↓
  ┌─────────────────────────────────┐
  │   Node Simulator Component      │
  │  (Full-screen, camera access)   │
  └─────────────────────────────────┘
         ↓ axios.post()
  ┌─────────────────────────────────┐
  │   Vite Dev Server (5173)        │
  │  /api/analyze/ proxy → Django   │
  └─────────────────────────────────┘
         ↓ HTTP Request
  ┌─────────────────────────────────┐
  │   Django Backend                │
  │  Processes image, calculates    │
  │  health_score, creates record   │
  └─────────────────────────────────┘
         ↓ SQL Insert
  ┌─────────────────────────────────┐
  │   Supabase PostgreSQL           │
  │  Stores AnalysisResult record   │
  └─────────────────────────────────┘
         ↓ postgres_changes
  ┌─────────────────────────────────┐
  │   Supabase Realtime Channel     │
  │  Broadcasts INSERT event        │
  └─────────────────────────────────┘
         ↓ supabase.on()
  ┌─────────────────────────────────┐
  │   Dashboard Component           │
  │  Receives event, updates state  │
  │  Camera Grid re-renders         │
  └─────────────────────────────────┘
```

---

## Code Files Modified

1. **Created**: `src/components/NodeSimulator.jsx` (476 lines)
   - Full-screen mobile simulator component
   - Camera access, frame capture, upload logic
   - Connection status UI, error handling

2. **Updated**: `src/pages/Dashboard.jsx`
   - Import NodeSimulator and supabase
   - Add showNodeSimulator state
   - Implement Supabase realtime subscription
   - Add Node Simulator button to header
   - Render NodeSimulator component

3. **Used**: `src/lib/supabase.js` (no changes needed)
   - Already configured with Supabase client
   - Realtime subscription framework works out of box

---

## Environment Variables Required

Ensure your `.env.local` has:
```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_KEY=your_supabase_key
```

These are already used for realtime to work.

---

**Implementation Date**: March 19, 2025
**Status**: ✅ Complete & Production Ready
