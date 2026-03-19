export default function AnalysisModal({ record, onClose }) {
  if (!record) {
    return null;
  }

  const actions = record.actions && typeof record.actions === "object" ? Object.entries(record.actions) : [];
  const rankedActions = actions
    .filter(([key]) => key !== "recommendation")
    .map(([key, value]) => `${key}: ${String(value)}`);

  const locationTitle = record.field_zone
    ? record.field_zone
    : record.latitude != null && record.longitude != null
      ? `${record.latitude}, ${record.longitude}`
      : "Unknown location";

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-white rounded-xl border border-slate-200 shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Analysis Result</h3>
            <p className="text-sm text-slate-500">{locationTitle}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded-md bg-slate-100 text-slate-700 hover:bg-slate-200"
          >
            Close
          </button>
        </div>

        <div className="p-5 grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div>
            {record.overlay_image_url ? (
              <img
                src={record.overlay_image_url}
                alt="Analyzed overlay"
                className="w-full h-[320px] object-cover rounded-lg border border-slate-200"
              />
            ) : (
              <div className="w-full h-[320px] rounded-lg border border-dashed border-slate-300 bg-slate-50 flex items-center justify-center text-slate-500 text-sm">
                No overlay image available
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="rounded-lg border border-slate-200 p-4 bg-slate-50">
              <p className="text-xs uppercase tracking-wide text-slate-500">Health Score</p>
              <p className="text-3xl font-bold text-slate-900">{record.health_score}</p>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-slate-900 mb-2">Ranked Actions</h4>
              {rankedActions.length > 0 ? (
                <ol className="list-decimal ml-5 space-y-1 text-sm text-slate-700">
                  {rankedActions.map((action, index) => (
                    <li key={`${index}-${action}`}>{action}</li>
                  ))}
                </ol>
              ) : (
                <p className="text-sm text-slate-500">No ranked actions available.</p>
              )}
            </div>

            {record.actions?.recommendation ? (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
                {record.actions.recommendation}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
