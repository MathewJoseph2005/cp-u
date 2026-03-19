import { useMemo } from "react";

function getHealthTone(score) {
  if (score < 40) {
    return "border-red-500 bg-red-50 text-red-700";
  }
  if (score <= 70) {
    return "border-yellow-500 bg-yellow-50 text-yellow-700";
  }
  return "border-emerald-500 bg-emerald-50 text-emerald-700";
}

const cameraCells = [1, 2, 3, 4, 5, 6, 7, 8, 9];

export default function CameraGrid({ analysisResults, onRecordSelect }) {
  const cameraRecords = useMemo(
    () =>
      analysisResults.filter(
        (item) => Number.isInteger(item.camera_number) && item.camera_number >= 1 && item.camera_number <= 9
      ),
    [analysisResults]
  );

  const latestRecordByCamera = useMemo(() => {
    const byCamera = new Map();

    for (const record of cameraRecords) {
      const cameraNumber = record.camera_number;
      const existing = byCamera.get(cameraNumber);

      if (!existing) {
        byCamera.set(cameraNumber, record);
        continue;
      }

      const existingTime = new Date(existing.created_at || 0).getTime();
      const currentTime = new Date(record.created_at || 0).getTime();
      if (currentTime >= existingTime) {
        byCamera.set(cameraNumber, record);
      }
    }

    return byCamera;
  }, [cameraRecords]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <h2 className="text-lg font-semibold text-slate-900 mb-1">Camera Field Grid</h2>
      <p className="text-xs text-slate-500 mb-4">
        Click a camera tag to view the same analysis modal used in Drone View.
      </p>

      <div className="grid grid-cols-3 grid-rows-3 gap-4">
        {cameraCells.map((cameraNumber) => {
          const record = latestRecordByCamera.get(cameraNumber);

          return (
            <div
              key={cameraNumber}
              className="min-h-[110px] rounded-lg border border-slate-200 bg-slate-50 p-3 flex flex-col justify-between"
            >
              <p className="text-xs font-medium text-slate-500">Camera {cameraNumber}</p>

              {record ? (
                <button
                  type="button"
                  onClick={() => onRecordSelect(record)}
                  className={`animate-pulse rounded-md border px-3 py-2 text-xs font-semibold text-left ${getHealthTone(record.health_score ?? 0)}`}
                >
                  <span className="block">Tag: CAM-{cameraNumber}</span>
                  <span className="block">Health: {record.health_score}</span>
                </button>
              ) : (
                <div className="rounded-md border border-dashed border-slate-300 px-3 py-2 text-[11px] text-slate-400">
                  No analysis yet
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
