# Phone Connection Setup - Complete Guide

## Problem You're Facing
`http://0.0.0.0:8000/` and local IPs like `192.168.137.1:5173` don't work from your phone because:
- `0.0.0.0` is a "bind all interfaces" address (only works on the same computer)
- Local IP access requires same WiFi network (may fail due to firewall/routing)
- Both approaches are unreliable for mobile testing

## ✅ Solution: ngrok (Already Installed!)

ngrok creates a **public HTTPS tunnel** to your local development server. Works from anywhere - even on mobile data!

### Quick Start (2 steps)

#### Step 1: Ensure Vite is Running
```bash
npm run dev
```
You should see:
```
  ➜  Local:   http://localhost:5173/
```

#### Step 2: Start the Tunnel
```bash
# Windows (use this file):
start-tunnel.bat

# Or directly:
ngrok http 5173
```

You'll see output like:
```
Session Status       online
Account             yourname@example.com
Forwarding          https://abc-123d-ef.ngrok.io -> http://localhost:5173
```

### Step 3: Access from Phone
1. Copy the HTTPS URL (e.g., `https://abc-123d-ef.ngrok.io`)
2. On your phone browser, paste it
3. Done! ✨

---

## How It Works

```
Your Phone
    ↓
https://abc-123d-ef.ngrok.io
    ↓ (public internet)
ngrok tunnel (hosted by ngrok.com)
    ↓ (local network)
your computer
    ↓
http://localhost:5173 (Vite dev server)
```

All your API calls automatically get routed too:
- `/api/analyze/` → `https://abc-123d-ef.ngrok.io/api/analyze/`
- Works with your Django backend!

---

## Setup Ngrok Account (One-Time)

To avoid ngrok limits, create a free account:

1. Go to https://ngrok.com/
2. Sign up (free tier available)
3. Get your "Authtoken" from dashboard
4. Run this once:
   ```bash
   ngrok config add-authtoken YOUR_TOKEN_HERE
   ```

Done! Now each tunnel session gives you a persistent URL.

---

## Troubleshooting

### "ngrok: command not found"
```bash
npm install -g ngrok
```

### URL changes every time I restart
- Create ngrok account (see above)
- With authtoken, URL stays the same longer

### Still getting "connection refused" on phone?
1. Check Vite is running: `npm run dev`
2. Try ngrok in different terminal
3. Copy exact HTTPS URL from ngrok output
4. Make sure phone is online

### API calls still failing?
- Django must be running on port 8000
- ngrok only tunnels Vite frontend
- Backend still needs to be accessible locally (same computer)

---

## Production Deployment

When you deploy to production:
- Use your actual domain (not ngrok)
- All relative paths work the same way
- No code changes needed!

This is why we used relative paths (`/api/analyze/`) instead of hardcoded URLs.

---

## Files Included

- `start-tunnel.bat` - Windows batch file to launch ngrok
- `start-tunnel.sh` - Bash script for Mac/Linux
- This guide

---

## Next Steps

1. ✅ ngrok is already installed
2. Run `npm run dev` (if not already running)
3. Run `start-tunnel.bat` in a new terminal
4. Copy the HTTPS URL and test from phone
5. Done!

Questions? Check the main IoT_NODE_SIMULATOR_GUIDE.md for more details.
