import { useState, useRef, useEffect } from "react";
import axios from "axios";

export default function NodeSimulator({ user, onClose = () => {} }) {
  const [cameraNumber, setCameraNumber] = useState("1");
  const [isActive, setIsActive] = useState(false);
  const [lastSynced, setLastSynced] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState("idle"); // idle, uploading, success, error
  const [statusMessage, setStatusMessage] = useState("");
  const [deviceSupport, setDeviceSupport] = useState(true);
  const [error, setError] = useState("");

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);

  // Request camera access and start video stream
  useEffect(() => {
    if (!isActive) return;

    const startCamera = async () => {
      try {
        setError("");
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: "environment", // Back camera on mobile
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
          audio: false,
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          streamRef.current = stream;
        }

        // Start auto-capture loop
        startCaptureLoop();
      } catch (err) {
        setError(
          `Camera access denied or not available: ${err.message}. Make sure you're on HTTPS or localhost.`
        );
        setConnectionStatus("error");
        setIsActive(false);

        // Check if device supports getUserMedia
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          setDeviceSupport(false);
        }
      }
    };

    startCamera();

    return () => {
      // Cleanup: stop camera stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isActive]);

  // Auto-capture function: Draw video frame to canvas and upload
  const captureAndUpload = async () => {
    try {
      if (!videoRef.current || !canvasRef.current) return;

      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      const video = videoRef.current;

      // Set canvas dimensions to match video
      canvas.width = video.videoWidth || 1280;
      canvas.height = video.videoHeight || 720;

      // Draw current video frame to canvas
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert canvas to JPEG blob
      canvas.toBlob(
        async (blob) => {
          if (!blob) {
            setStatusMessage("Failed to capture frame");
            setConnectionStatus("error");
            return;
          }

          try {
            setConnectionStatus("uploading");
            setStatusMessage("Uploading frame...");

            if (!user?.name || !user?.phone) {
              setConnectionStatus("error");
              setStatusMessage("✗ Missing user session. Please log in again.");
              return;
            }

            // Create FormData and append blob + camera_number
            const formData = new FormData();
            formData.append("image", blob, "frame.jpg");
            formData.append("camera_number", parseInt(cameraNumber, 10));
            formData.append("name", user.name);
            formData.append("phone", user.phone);

            // POST to /api/analyze/ endpoint
            // Using relative path so it works with both localhost and IP addresses
            const response = await axios.post("/api/analyze/", formData, {
              headers: { "Content-Type": "multipart/form-data" },
              timeout: 30000, // 30 second timeout
            });

            if (response.status === 200 || response.status === 201) {
              setConnectionStatus("success");
              setLastSynced(new Date());
              setStatusMessage("✓ Frame uploaded successfully");

              // Reset success message after 2 seconds
              setTimeout(() => {
                if (connectionStatus === "success") {
                  setConnectionStatus("idle");
                  setStatusMessage("");
                }
              }, 2000);
            }
          } catch (uploadErr) {
            console.error("Upload error:", uploadErr);
            setConnectionStatus("error");
            const errorMsg =
              uploadErr.response?.data?.detail ||
              uploadErr.message ||
              "Upload failed";
            setStatusMessage(`✗ ${errorMsg}`);
          }
        },
        "image/jpeg",
        0.85 // JPEG quality
      );
    } catch (err) {
      console.error("Capture error:", err);
      setConnectionStatus("error");
      setStatusMessage(`✗ Capture failed: ${err.message}`);
    }
  };

  // Start the auto-capture loop (every 10 seconds)
  const startCaptureLoop = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Capture immediately on start
    captureAndUpload();

    // Then capture every 10 seconds
    intervalRef.current = setInterval(() => {
      captureAndUpload();
    }, 10000);
  };

  // Stop the simulator
  const handleToggle = () => {
    if (isActive) {
      setIsActive(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      setConnectionStatus("idle");
      setStatusMessage("");
    } else {
      setIsActive(true);
    }
  };

  const statusDotColor =
    connectionStatus === "success"
      ? "bg-emerald-500"
      : connectionStatus === "error"
      ? "bg-red-500"
      : connectionStatus === "uploading"
      ? "bg-blue-500"
      : "bg-gray-300";

  return (
    <div className="fixed inset-0 z-50 bg-slate-900 flex flex-col">
      {/* Header */}
      <div className="bg-slate-800 text-white p-4 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold">📱 IoT Node Simulator</h1>
            <p className="text-xs text-slate-400 mt-1">
              Live Camera Feed Auto-Upload
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-sm px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded text-white font-medium transition"
          >
            ← Back
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center p-4 overflow-y-auto">
        {/* Camera Selection Dropdown */}
        <div className="mb-6 w-full max-w-sm">
          <label className="block text-sm font-semibold text-white mb-2">
            Select Camera
          </label>
          <select
            value={cameraNumber}
            onChange={(e) => setCameraNumber(e.target.value)}
            disabled={isActive}
            className="w-full px-4 py-3 rounded-lg bg-slate-700 text-white border border-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
              <option key={num} value={num}>
                Camera {num}
              </option>
            ))}
          </select>
        </div>

        {/* Video Preview */}
        <div className="w-full max-w-sm mb-6 rounded-lg overflow-hidden bg-black border-2 border-slate-600">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className="w-full h-auto block"
            style={{ aspectRatio: "16/9" }}
          />
        </div>

        {/* Hidden Canvas for Capture */}
        <canvas ref={canvasRef} style={{ display: "none" }} />

        {/* Info Display */}
        <div className="w-full max-w-sm mb-6 space-y-3">
          {/* Connection Status */}
          <div className="flex items-center gap-3 px-4 py-3 bg-slate-800 rounded-lg border border-slate-700">
            <div
              className={`w-3 h-3 rounded-full ${statusDotColor} flex-shrink-0 ${
                connectionStatus === "uploading" ? "animate-pulse" : ""
              }`}
            />
            <div className="flex-1">
              <p className="text-xs text-slate-400">Connection Status</p>
              <p className="text-sm font-semibold text-white capitalize">
                {connectionStatus === "idle"
                  ? "Ready"
                  : connectionStatus === "uploading"
                  ? "Uploading..."
                  : connectionStatus === "success"
                  ? "Connected"
                  : "Connection Error"}
              </p>
            </div>
          </div>

          {/* Last Synced Timestamp */}
          <div className="px-4 py-3 bg-slate-800 rounded-lg border border-slate-700">
            <p className="text-xs text-slate-400">Last Synced</p>
            <p className="text-sm font-semibold text-white">
              {lastSynced
                ? lastSynced.toLocaleTimeString()
                : "Awaiting first capture"}
            </p>
          </div>

          {/* Status Message */}
          {statusMessage && (
            <div
              className={`px-4 py-3 rounded-lg text-sm font-medium ${
                connectionStatus === "error"
                  ? "bg-red-900/30 border border-red-700 text-red-300"
                  : "bg-emerald-900/30 border border-emerald-700 text-emerald-300"
              }`}
            >
              {statusMessage}
            </div>
          )}
        </div>

        {/* Start/Stop Toggle Button */}
        <button
          onClick={handleToggle}
          className={`w-full max-w-sm px-6 py-4 rounded-lg font-bold text-lg transition transform active:scale-95 ${
            isActive
              ? "bg-red-600 hover:bg-red-700 text-white"
              : deviceSupport
              ? "bg-emerald-600 hover:bg-emerald-700 text-white"
              : "bg-gray-600 cursor-not-allowed text-gray-300"
          }`}
          disabled={!deviceSupport}
        >
          {isActive ? "🛑 Stop Live Feed" : "▶ Start Live Feed"}
        </button>

        {/* Error Display */}
        {error && (
          <div className="w-full max-w-sm mt-4 px-4 py-3 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm">
            <p className="font-semibold mb-1">⚠ Error</p>
            <p>{error}</p>
            <p className="text-xs mt-2 text-red-200">
              💡 Tip: Access via HTTPS or localhost. On mobile, use your local
              IP (e.g., http://192.168.1.x:5173)
            </p>
          </div>
        )}

        {!deviceSupport && (
          <div className="w-full max-w-sm mt-4 px-4 py-3 bg-yellow-900/30 border border-yellow-700 rounded-lg text-yellow-300 text-sm">
            <p className="font-semibold mb-1">📱 Device Not Supported</p>
            <p>
              Your device doesn't support camera access. Please use a browser
              with camera support (Chrome, Firefox, Safari on iOS 15+).
            </p>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="bg-slate-800 border-t border-slate-700 p-4 text-center text-xs text-slate-400">
        <p>
          Captures frame every 10 seconds and uploads to{" "}
          <code className="bg-slate-900 px-2 py-1 rounded text-slate-300">
            /api/analyze/
          </code>
        </p>
        <p className="mt-1">
          Mobile access: Use HTTPS or access via local IP address (not localhost)
        </p>
      </div>
    </div>
  );
}
