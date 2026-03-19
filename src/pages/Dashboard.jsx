import { useContext, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { AuthContext } from "../context/AuthContext";
import AnalysisModal from "../components/AnalysisModal";
import CameraGrid from "../components/CameraGrid";
import FarmMap from "../components/FarmMap";
import NodeSimulator from "../components/NodeSimulator";
import { fetchAnalysisResults, supabase } from "../lib/supabase";

export default function Dashboard() {
  const { user, logout } = useContext(AuthContext);

  const [analysisResults, setAnalysisResults] = useState([]);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [activeView, setActiveView] = useState("drone");
  const [showModal, setShowModal] = useState(false);
  const [showNodeSimulator, setShowNodeSimulator] = useState(false);

  const [image, setImage] = useState(null);
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [cameraNumber, setCameraNumber] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [exportMenuOpen, setExportMenuOpen] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function loadResults() {
      try {
        const rows = await fetchAnalysisResults();
        if (mounted) {
          setAnalysisResults(Array.isArray(rows) ? rows : []);
        }
      } catch (err) {
        if (mounted) {
          setError(err?.message || "Failed to load analysis results.");
        }
      }
    }

    loadResults();

    // Set up Supabase realtime subscription for INSERT and UPDATE events
    const channel = supabase
      .channel("table_changes")
      .on(
        "postgres_changes",
        {
          event: "*", // Subscribe to all events (INSERT, UPDATE, DELETE)
          schema: "public",
          table: "AnalysisResult",
        },
        (payload) => {
          if (mounted) {
            if (payload.eventType === "INSERT") {
              // New record inserted - add to the beginning of the list
              const newRecord = payload.new;
              setAnalysisResults((prev) => [newRecord, ...prev]);
            } else if (payload.eventType === "UPDATE") {
              // Record updated - replace old record with updated one
              const updatedRecord = payload.new;
              setAnalysisResults((prev) =>
                prev.map((record) =>
                  record.id === updatedRecord.id ? updatedRecord : record
                )
              );
            } else if (payload.eventType === "DELETE") {
              // Record deleted - remove from list
              const deletedId = payload.old.id;
              setAnalysisResults((prev) =>
                prev.filter((record) => record.id !== deletedId)
              );
            }
          }
        }
      )
      .subscribe();

    return () => {
      mounted = false;
      // Unsubscribe from realtime events when component unmounts
      supabase.removeChannel(channel);
    };
  }, []);

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

    if (cameraNumber.trim()) {
      const parsedCamera = parseInt(cameraNumber, 10);
      if (!Number.isNaN(parsedCamera) && parsedCamera > 0) {
        formData.append("camera_number", parsedCamera);
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
        setSelectedRecord(newRecord);
        setShowModal(true);
      }
      setSuccess("Image analyzed successfully.");

      setImage(null);
      setLatitude("");
      setLongitude("");
      setCameraNumber("");
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

  const droneRecords = useMemo(
    () =>
      analysisResults.filter(
        (item) =>
          typeof item.latitude === "number" &&
          !Number.isNaN(item.latitude) &&
          typeof item.longitude === "number" &&
          !Number.isNaN(item.longitude)
      ),
    [analysisResults]
  );

  const cameraRecords = useMemo(
    () => analysisResults.filter((item) => Number.isInteger(item.camera_number)),
    [analysisResults]
  );

  function handleExportJson() {
    if (!analysisResults.length) {
      setError("No analyzed data available to export.");
      return;
    }

    setError("");

    const exportPayload = {
      exported_at: new Date().toISOString(),
      exported_by: {
        name: user?.name || null,
        phone: user?.phone || null,
      },
      total_records: analysisResults.length,
      records: analysisResults,
    };

    const blob = new Blob([JSON.stringify(exportPayload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `cropsight-analysis-${new Date().toISOString().replace(/[:.]/g, "-")}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setExportMenuOpen(false);
  }

  function handleExportPdf() {
    if (!analysisResults.length) {
      setError("No analyzed data available to export.");
      return;
    }

    setError("");

    const reportRows = analysisResults
      .map((record, index) => {
        const actions = record.actions && typeof record.actions === "object"
          ? Object.entries(record.actions)
              .map(([key, value]) => `${key}: ${String(value)}`)
              .join("; ")
          : "No actions";

        const location = record.field_zone
          || (record.latitude != null && record.longitude != null
            ? `${record.latitude}, ${record.longitude}`
            : "N/A");

        return `
          <tr>
            <td>${index + 1}</td>
            <td>${record.health_score ?? "N/A"}</td>
            <td>${record.camera_number ?? "N/A"}</td>
            <td>${location}</td>
            <td>${actions}</td>
          </tr>
        `;
      })
      .join("");

    const printWindow = window.open("", "_blank", "width=1000,height=700");
    if (!printWindow) {
      setError("Unable to open print window. Please allow popups and try again.");
      return;
    }

    printWindow.document.write(`
      <html>
        <head>
          <title>CropSight Analysis Report</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 24px; color: #111827; }
            h1 { margin-bottom: 4px; }
            p { margin-top: 0; color: #475569; }
            table { width: 100%; border-collapse: collapse; margin-top: 16px; }
            th, td { border: 1px solid #cbd5e1; padding: 8px; text-align: left; vertical-align: top; font-size: 12px; }
            th { background: #f1f5f9; }
          </style>
        </head>
        <body>
          <h1>CropSight Analysis Report</h1>
          <p>Exported at: ${new Date().toISOString()}</p>
          <p>Exported by: ${user?.name || "N/A"} (${user?.phone || "N/A"})</p>
          <p>Total records: ${analysisResults.length}</p>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Health Score</th>
                <th>Camera</th>
                <th>Location / Zone</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${reportRows}
            </tbody>
          </table>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
    setExportMenuOpen(false);
  }

  function handleRecordSelect(record) {
    setSelectedRecord(record);
    setShowModal(true);
  }

  if (showNodeSimulator) {
    return (
      <NodeSimulator
        user={user}
        onClose={() => setShowNodeSimulator(false)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 p-4 shadow-sm">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">CropSight Dashboard</h1>
            <p className="text-sm text-slate-600">Welcome, {user.name}</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowNodeSimulator(true)}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition"
              title="Launch IoT Node Simulator for live camera feeds"
            >
              📱 Node Simulator
            </button>
            <button
              onClick={logout}
              className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-medium transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="p-6">
        <div className="max-w-7xl mx-auto space-y-6">
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
                  Camera Number (optional)
                </label>
                <input
                  type="number"
                  min="1"
                  value={cameraNumber}
                  onChange={(e) => setCameraNumber(e.target.value)}
                  placeholder="e.g. 1"
                  className="w-full border border-slate-300 rounded-md p-2"
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <button
                type="submit"
                disabled={loading}
                className="w-full px-4 py-3 rounded-md bg-green-600 hover:bg-green-700 text-white font-semibold disabled:opacity-60 transition"
              >
                {loading ? "Analyzing..." : "Analyze"}
              </button>

              <div className="relative">
                <button
                  type="button"
                  onClick={() => setExportMenuOpen((prev) => !prev)}
                  disabled={!analysisResults.length}
                  className="w-full px-4 py-3 rounded-md bg-slate-900 hover:bg-slate-700 text-white font-semibold disabled:opacity-60 transition flex items-center justify-center gap-2"
                >
                  Export
                  <span className="text-xs">▾</span>
                </button>

                {exportMenuOpen ? (
                  <div className="absolute z-10 mt-2 w-full rounded-md border border-slate-200 bg-white shadow-lg overflow-hidden">
                    <button
                      type="button"
                      onClick={handleExportJson}
                      className="w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100"
                    >
                      Export as JSON
                    </button>
                    <button
                      type="button"
                      onClick={handleExportPdf}
                      className="w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100"
                    >
                      Export as PDF
                    </button>
                  </div>
                ) : null}
              </div>
            </div>
          </form>

          <section className="bg-white p-5 rounded-xl border border-slate-200 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-slate-900">Center Stage</h2>
              <div className="inline-flex rounded-lg border border-slate-200 p-1 bg-slate-50">
                <button
                  type="button"
                  onClick={() => setActiveView("drone")}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
                    activeView === "drone"
                      ? "bg-slate-900 text-white"
                      : "text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  🛰️ Drone View
                </button>
                <button
                  type="button"
                  onClick={() => setActiveView("camera")}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
                    activeView === "camera"
                      ? "bg-slate-900 text-white"
                      : "text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  📷 Camera View
                </button>
              </div>
            </div>

            {activeView === "drone" ? (
              <FarmMap
                analysisResults={droneRecords}
                setAnalysisResults={setAnalysisResults}
                selectedMarker={selectedRecord}
                setSelectedMarker={setSelectedRecord}
                mapHeightClassName="h-[420px] md:h-[520px]"
                onRecordSelect={handleRecordSelect}
                autoFetch={false}
              />
            ) : (
              <CameraGrid
                analysisResults={cameraRecords}
                onRecordSelect={handleRecordSelect}
              />
            )}
          </section>
        </div>
      </div>

      {showModal ? (
        <AnalysisModal
          record={selectedRecord}
          onClose={() => setShowModal(false)}
        />
      ) : null}

    </div>
  );
}
