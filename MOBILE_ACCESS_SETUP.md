# Quick Start: Mobile Access Setup

## Problem
When developing on your computer, accessing `localhost:5173` from a phone won't work because phones don't have access to your computer's localhost network interface.

## Solution: Use Your Computer's Local IP Address

### Step 1: Find Your Computer's IP Address

**Windows (PowerShell):**
```powershell
ipconfig
```
Look for "IPv4 Address" under "Ethernet adapter" or "Wireless LAN adapter"
Example: `192.168.1.100`

**Mac/Linux (Terminal):**
```bash
ifconfig
```
Look for `inet` address (usually starts with 192.168.x.x or 10.0.x.x)

### Step 2: Start Development Server

Make sure your Vite dev server is running:
```bash
npm run dev
```
You should see:
```
Local:    http://localhost:5173
```

### Step 3: Access from Phone on Same WiFi

**Important**: Phone must be on the **same WiFi network** as your computer.

1. On your phone browser (Chrome, Safari, Firefox), visit:
   ```
   http://192.168.1.100:5173
   ```
   (Replace 192.168.1.100 with your actual IP from Step 1)

2. You should see the CropSight Dashboard

3. Click **"📱 Node Simulator"** button

4. Grant camera permission when prompted

5. Select a camera and click **"▶ Start Live Feed"**

6. Frames will upload every 10 seconds

7. Return to Dashboard (click back) to see live updates

---

## Why This Works

All API calls use relative paths:
```javascript
axios.post("/api/analyze/", formData, ...)
```

When you access via `http://192.168.1.100:5173`, the browser automatically sends API requests to:
- `http://192.168.1.100/api/analyze/`
- `http://192.168.1.100/api/...`

So **no code changes needed** - just use the IP address!

---

## Testing Checklist

- [ ] Computer and phone on same WiFi
- [ ] `npm run dev` is running
- [ ] Browser can access `http://192.168.1.100:5173` (replace IP)
- [ ] Dashboard loads
- [ ] Click Node Simulator button
- [ ] Camera permission granted
- [ ] Video stream appears
- [ ] "Start Live Feed" button works
- [ ] Status shows "Uploading..." every 10 seconds
- [ ] Dashboard updates automatically

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Can't access IP from phone | Check WiFi connection, same network |
| Camera not working | Grant camera permission in browser settings |
| Uploads failing | Check Django backend running, check terminal for errors |
| Dashboard not updating | Check Supabase credentials in .env.local |
| Connection times out | Check firewall not blocking port 5173 |

---

## Advanced: HTTPS on Local Network

If you need HTTPS (for some browsers' security policies):

### Option 1: ngrok (Easiest)
```bash
npm install -g ngrok
ngrok http 5173
```
You'll get an HTTPS URL like: `https://abc-123.ngrok.io`

### Option 2: Self-Signed Certificate
```bash
# Create cert (one time)
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Update vite.config.js to use HTTPS
```

### Option 3: Localhost with mkcert
```bash
mkcert localhost 127.0.0.1 192.168.1.100
# Then configure Vite to use the cert
```

---

## Production Deployment

When deploying to production:

1. Your app will be at `https://yourdomain.com`
2. All relative paths automatically work
3. No changes to code needed
4. Users access from any phone via public URL

The architecture is ready for production!

---

**Last Updated**: March 19, 2025
