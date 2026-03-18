import { useState, useContext } from "react";
import axios from "axios";
import { AuthContext } from "../context/AuthContext";
import FarmMap from "../components/FarmMap";

export default function Dashboard() {
  const { user, logout } = useContext(AuthContext);
  
  const [analysisResults, setAnalysisResults] = useState([]);
  const [selectedMarker, setSelectedMarker] = useState(null);

  const [image, setImage] = useState(null);
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!user?.name || !user?.phone) {
      setError("Your login session is incomplete. Please log out and log in again.");
      return;
    }

    if (!image) {
      setError("Image is required.");
      return;
    }

    const formData = new FormData();
    formData.append("image", image);
    formData.append("name", user.name);
    formData.append("phone", user.phone);

    // Only add latitude/longitude if both are valid numbers
    if (latitude && longitude) {
      const lat = parseFloat(latitude);
      const lon = parseFloat(longitude);
      
      if (!isNaN(lat) && !isNaN(lon)) {
        formData.append("latitude", lat);
        formData.append("longitude", lon);
      }
    }

    try {
      setLoading(true);

      const response = await axios.post("/api/analyze/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const newRecord = response?.data;
      if (newRecord && typeof newRecord === "object") {
        setAnalysisResults((prev) => [newRecord, ...prev]);
        setSelectedMarker(newRecord);
      }
      setSuccess("Image analyzed successfully.");

      setImage(null);
      setLatitude("");
      setLongitude("");
    } catch (err) {
      const responseData = err?.response?.data;
      const detail = responseData?.detail;

      if (Array.isArray(detail)) {
        setError(detail.join(", "));
      } else if (typeof detail === "string") {
        setError(detail);
      } else if (responseData && typeof responseData === "object") {
        // DRF serializer errors often come as { field: ["message"] }
        const fieldErrors = Object.entries(responseData)
          .flatMap(([field, messages]) => {
            if (Array.isArray(messages)) {
              return messages.map((message) => `${field}: ${message}`);
            }
            if (typeof messages === "string") {
              return `${field}: ${messages}`;
            }
            return [];
          })
          .join(", ");

        setError(fieldErrors || "Failed to analyze image.");
      } else {
        setError("Failed to analyze image.");
      }
    } finally {
      setLoading(false);
    }
  }

  const actionEntries = selectedMarker?.actions
    ? Object.entries(selectedMarker.actions)
    : [];

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 p-4 shadow-sm">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">CropSight Dashboard</h1>
            <p className="text-sm text-slate-600">Welcome, {user.name}</p>
          </div>
          <button
            onClick={logout}
            className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-medium transition"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="p-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2 space-y-6">
            <form
              onSubmit={handleSubmit}
              className="bg-white p-5 rounded-xl border border-slate-200 space-y-4"
            >
              <h2 className="text-xl font-semibold text-slate-900">Analyze Crop</h2>

              {/* User Info Display */}
              <div className="bg-slate-50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-slate-600">Name:</span>
                  <span className="text-sm text-slate-900 font-semibold">{user.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-slate-600">Phone:</span>
                  <span className="text-sm text-slate-900 font-semibold">{user.phone}</span>
                </div>
              </div>

              {error ? <p className="text-sm text-red-600 bg-red-50 p-3 rounded">{error}</p> : null}
              {success ? <p className="text-sm text-emerald-700 bg-emerald-50 p-3 rounded">{success}</p> : null}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Upload Image
                  </label>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setImage(e.target.files?.[0] || null)}
                    className="w-full border border-slate-300 rounded-md p-2"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Latitude (optional)
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={latitude}
                    onChange={(e) => setLatitude(e.target.value)}
                    placeholder="Enter latitude"
                    className="w-full border border-slate-300 rounded-md p-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Longitude (optional)
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={longitude}
                    onChange={(e) => setLongitude(e.target.value)}
                    placeholder="Enter longitude"
                    className="w-full border border-slate-300 rounded-md p-2"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full px-4 py-3 rounded-md bg-green-600 hover:bg-green-700 text-white font-semibold disabled:opacity-60 transition"
              >
                {loading ? "Analyzing..." : "Analyze"}
              </button>
            </form>

            <FarmMap
              analysisResults={analysisResults}
              setAnalysisResults={setAnalysisResults}
              selectedMarker={selectedMarker}
              setSelectedMarker={setSelectedMarker}
            />
          </div>

          {selectedMarker ? (
            <aside className="bg-white p-5 rounded-xl border border-slate-200 h-fit">
              <h2 className="text-lg font-semibold text-slate-900 mb-3">Analysis Details</h2>

              <p className="text-sm text-slate-700 mb-4">
                Health Score: <span className="font-semibold text-lg">{selectedMarker.health_score}</span>
              </p>

              {selectedMarker.overlay_image_url ? (
                <img
                  src={selectedMarker.overlay_image_url}
                  alt="Overlay"
                  className="w-full rounded-lg border border-slate-200 mb-4"
                />
              ) : null}

              <h3 className="text-sm font-semibold text-slate-800 mb-2">Actions</h3>
              <ul className="space-y-1 text-sm text-slate-700">
                {actionEntries.length > 0 ? (
                  actionEntries.map(([key, value]) => (
                    <li key={key}>
                      <span className="font-medium">{key}:</span> {String(value)}
                    </li>
                  ))
                ) : (
                  <li>No actions available.</li>
                )}
              </ul>
            </aside>
          ) : (
            <aside className="bg-white p-5 rounded-xl border border-slate-200 h-fit text-sm text-slate-600">
              Select a marker on the map to view analysis details.
            </aside>
          )}
        </div>
      </div>
    </div>
  );
}
