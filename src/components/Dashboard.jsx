import { useMemo, useState } from "react";
import axios from "axios";

import FarmMap from "./FarmMap";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function renderActions(actions) {
  if (!actions) {
    return [];
  }

  if (Array.isArray(actions)) {
    return actions;
  }

  if (Array.isArray(actions.recommendations)) {
    return actions.recommendations;
  }

  return Object.values(actions).flatMap((value) => (Array.isArray(value) ? value : []));
}

function Dashboard() {
  const [records, setRecords] = useState([]);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [farmName, setFarmName] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const actionItems = useMemo(
    () => renderActions(selectedRecord?.actions),
    [selectedRecord?.actions]
  );

  function normalizeRecord(record) {
    return {
      ...record,
      latitude: record.latitude == null ? null : Number(record.latitude),
      longitude: record.longitude == null ? null : Number(record.longitude),
      health_score: Number(record.health_score),
    };
  }

  async function handleUpload(event) {
    event.preventDefault();
    setError("");

    if (!imageFile) {
      setError("Please select an image file first.");
      return;
    }

    const formData = new FormData();
    formData.append("image", imageFile);
    if (farmName.trim()) {
      formData.append("farm_name", farmName.trim());
    }

    setIsSubmitting(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/analyze/`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const created = normalizeRecord(response.data);
      setRecords((previous) => [created, ...previous]);
      setSelectedRecord(created);
      setImageFile(null);
      setFarmName("");
    } catch (uploadError) {
      const detail = uploadError.response?.data?.detail || "Upload failed. Please retry.";
      setError(detail);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-lime-50 via-white to-emerald-50 px-4 py-6 md:px-8 md:py-8">
      <div className="mx-auto grid w-full max-w-7xl gap-6 lg:grid-cols-[2fr_1fr]">
        <section className="space-y-6 rounded-2xl border border-emerald-100 bg-white/90 p-4 shadow-md md:p-6">
          <header className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">CropSight Field Analyzer</h1>
            <p className="text-sm text-slate-600">
              Upload drone images, run analysis, and inspect field health zones on the live map.
            </p>
          </header>

          <form className="grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 md:grid-cols-[1fr_1fr_auto]" onSubmit={handleUpload}>
            <input
              type="text"
              placeholder="Farm name"
              value={farmName}
              onChange={(event) => setFarmName(event.target.value)}
              className="h-11 rounded-lg border border-slate-300 px-3 text-sm focus:border-emerald-500 focus:outline-none"
            />
            <input
              type="file"
              accept="image/*"
              onChange={(event) => setImageFile(event.target.files?.[0] || null)}
              className="h-11 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-emerald-600 file:px-3 file:py-1.5 file:text-white"
            />
            <button
              type="submit"
              disabled={isSubmitting}
              className="h-11 rounded-lg bg-emerald-600 px-4 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting ? "Analyzing..." : "Upload & Analyze"}
            </button>
          </form>

          {error ? <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

          <FarmMap records={records} setRecords={setRecords} onMarkerSelect={setSelectedRecord} />
        </section>

        <aside className="rounded-2xl border border-slate-200 bg-white p-4 shadow-md md:p-5">
          <h2 className="mb-3 text-lg font-semibold text-slate-900">Zone Details</h2>

          {!selectedRecord ? (
            <p className="text-sm text-slate-500">Click a marker to inspect the analyzed overlay and recommendations.</p>
          ) : (
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-slate-900">{selectedRecord.farm_name}</p>
                <p className="text-xs text-slate-500">Health Score: {selectedRecord.health_score}</p>
              </div>

              <div className="overflow-hidden rounded-lg border border-slate-200">
                <img
                  src={selectedRecord.overlay_image_url}
                  alt="Overlay analysis"
                  className="h-48 w-full object-cover"
                />
              </div>

              <div>
                <p className="mb-2 text-sm font-semibold text-slate-800">AI Actions</p>
                {actionItems.length ? (
                  <ul className="space-y-2 text-sm text-slate-700">
                    {actionItems.map((item, index) => (
                      <li key={`${item}-${index}`} className="rounded-md bg-slate-50 px-3 py-2">
                        {item}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">No actions available for this record.</p>
                )}
              </div>
            </div>
          )}
        </aside>
      </div>
    </main>
  );
}

export default Dashboard;
