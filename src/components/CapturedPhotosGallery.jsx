import { useMemo } from "react";

function formatDate(value) {
  if (!value) {
    return "Unknown time";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Unknown time";
  }

  return date.toLocaleString();
}

function getHealthBadge(score) {
  if (typeof score !== "number") {
    return "bg-slate-100 text-slate-700";
  }
  if (score < 40) {
    return "bg-red-100 text-red-700";
  }
  if (score <= 70) {
    return "bg-yellow-100 text-yellow-700";
  }
  return "bg-emerald-100 text-emerald-700";
}

function formatActions(actions) {
  if (!actions || typeof actions !== "object") {
    return [];
  }

  return Object.entries(actions)
    .filter(([key]) => key !== "recommendation")
    .map(([key, value]) => `${key}: ${String(value)}`);
}

export default function CapturedPhotosGallery({ analysisResults, onRecordSelect }) {
  const sortedResults = useMemo(() => {
    return [...analysisResults].sort((a, b) => {
      const timeA = new Date(a.created_at || 0).getTime();
      const timeB = new Date(b.created_at || 0).getTime();
      return timeB - timeA;
    });
  }, [analysisResults]);

  if (!sortedResults.length) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
        <p className="text-slate-600 font-medium">No captured photos yet.</p>
        <p className="text-sm text-slate-500 mt-1">Capture or upload an image to see it here with analysis details.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {sortedResults.map((record) => {
        const actions = formatActions(record.actions);
        const ai = record.ai_analysis && typeof record.ai_analysis === "object" ? record.ai_analysis : null;
        const location = record.field_zone
          || (record.latitude != null && record.longitude != null
            ? `${record.latitude}, ${record.longitude}`
            : "No location");

        return (
          <article
            key={record.id}
            className="rounded-xl border border-slate-200 bg-white overflow-hidden"
          >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-0">
              <div className="border-b lg:border-b-0 lg:border-r border-slate-200">
                {record.original_image_url ? (
                  <img
                    src={record.original_image_url}
                    alt="Captured original"
                    className="w-full h-56 object-cover"
                  />
                ) : (
                  <div className="w-full h-56 flex items-center justify-center text-sm text-slate-500 bg-slate-50">
                    No original image
                  </div>
                )}
              </div>

              <div className="border-b lg:border-b-0 lg:border-r border-slate-200">
                {record.overlay_image_url ? (
                  <img
                    src={record.overlay_image_url}
                    alt="Analysis overlay"
                    className="w-full h-56 object-cover"
                  />
                ) : (
                  <div className="w-full h-56 flex items-center justify-center text-sm text-slate-500 bg-slate-50">
                    No analysis overlay
                  </div>
                )}
              </div>

              <div className="p-4 space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-slate-900">Capture Details</p>
                  <span className={`text-xs font-semibold px-2 py-1 rounded ${getHealthBadge(record.health_score)}`}>
                    Health: {record.health_score ?? "N/A"}
                  </span>
                </div>

                <div className="text-sm text-slate-600 space-y-1">
                  <p><span className="font-medium text-slate-800">Camera:</span> {record.camera_number ?? "N/A"}</p>
                  <p><span className="font-medium text-slate-800">Location/Zone:</span> {location}</p>
                  <p><span className="font-medium text-slate-800">Captured:</span> {formatDate(record.created_at)}</p>
                </div>

                <div>
                  <p className="text-xs font-semibold text-slate-700 mb-1">Actions</p>
                  {actions.length ? (
                    <ul className="list-disc ml-4 text-sm text-slate-600 space-y-1">
                      {actions.map((item, index) => (
                        <li key={`${record.id}-${index}`}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-slate-500">No action details available.</p>
                  )}
                </div>

                {ai ? (
                  <div className="rounded-md border border-blue-200 bg-blue-50 p-2">
                    <p className="text-xs font-semibold text-blue-900">
                      AI Detection: {ai.is_field_image === true ? "Field" : ai.is_field_image === false ? "Other object" : "Unknown"}
                    </p>
                    {ai.summary ? (
                      <p className="text-xs text-blue-800 mt-1">{ai.summary}</p>
                    ) : null}
                  </div>
                ) : null}

                <button
                  type="button"
                  onClick={() => onRecordSelect(record)}
                  className="w-full rounded-md bg-slate-900 hover:bg-slate-700 text-white text-sm font-semibold py-2 transition"
                >
                  Open Full Analysis
                </button>
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
