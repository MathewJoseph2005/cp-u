import { useMemo, useRef, useState } from "react";
import { generateReportTTS } from "../lib/api";

export default function AnalysisModal({ record, onClose }) {
  const [ttsLoading, setTtsLoading] = useState(false);
  const [ttsError, setTtsError] = useState("");
  const audioRef = useRef(null);

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

  const aiAnalysis = record.ai_analysis && typeof record.ai_analysis === "object"
    ? record.ai_analysis
    : null;

  const aiGuidance = Array.isArray(aiAnalysis?.farmer_guidance)
    ? aiAnalysis.farmer_guidance
    : [];

  const aiMaintenance = Array.isArray(aiAnalysis?.maintenance_tips)
    ? aiAnalysis.maintenance_tips
    : [];

  const reportNarrationText = useMemo(() => {
    const summaryParts = [];
    summaryParts.push(`Analysis report for ${locationTitle}.`);
    summaryParts.push(`Health score is ${record.health_score ?? "not available"}.`);

    if (rankedActions.length) {
      summaryParts.push(`Ranked actions are: ${rankedActions.join(". ")}.`);
    }

    if (record.actions?.recommendation) {
      summaryParts.push(`Core recommendation: ${record.actions.recommendation}.`);
    }

    if (aiAnalysis?.summary) {
      summaryParts.push(`AI summary: ${aiAnalysis.summary}.`);
    }

    if (aiGuidance.length) {
      summaryParts.push(`AI guidance: ${aiGuidance.join(". ")}.`);
    }

    if (aiMaintenance.length) {
      summaryParts.push(`Maintenance tips: ${aiMaintenance.join(". ")}.`);
    }

    return summaryParts.join(" ");
  }, [
    locationTitle,
    record.health_score,
    rankedActions,
    record.actions?.recommendation,
    aiAnalysis?.summary,
    aiGuidance,
    aiMaintenance,
  ]);

  async function handleReadReport() {
    setTtsError("");
    setTtsLoading(true);

    try {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      const ttsResponse = await generateReportTTS({
        text: reportNarrationText,
        voice_id: 147320,
        language: "en-us",
        speech_model: "mars-flash",
        format: "mp3",
      });

      if (!ttsResponse?.audio_base64) {
        throw new Error("No audio content returned by TTS service.");
      }

      const binary = atob(ttsResponse.audio_base64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i += 1) {
        bytes[i] = binary.charCodeAt(i);
      }

      const audioBlob = new Blob([bytes], {
        type: ttsResponse.mime_type || "audio/mpeg",
      });

      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
      };
      await audio.play();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === "string" && detail.trim()) {
        setTtsError(detail);
      } else {
        setTtsError(err?.message || "Failed to generate voice narration.");
      }
    } finally {
      setTtsLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[1200] bg-slate-900/60 flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-white rounded-xl border border-slate-200 shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Analysis Result</h3>
            <p className="text-sm text-slate-500">{locationTitle}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleReadReport}
              disabled={ttsLoading}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
              title="Read report aloud"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className="w-4 h-4 fill-current" aria-hidden="true">
                <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v5a3 3 0 0 0 3 3zm5-3a1 1 0 1 1 2 0 7 7 0 0 1-6 6.92V21h3a1 1 0 1 1 0 2H8a1 1 0 1 1 0-2h3v-3.08A7 7 0 0 1 5 11a1 1 0 1 1 2 0 5 5 0 1 0 10 0z"/>
              </svg>
              {ttsLoading ? "Reading..." : "Read Report"}
            </button>

            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 rounded-md bg-slate-100 text-slate-700 hover:bg-slate-200"
            >
              Close
            </button>
          </div>
        </div>

        {ttsError ? (
          <div className="mx-5 mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {ttsError}
          </div>
        ) : null}

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

            {aiAnalysis ? (
              <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 space-y-2">
                <p className="text-sm font-semibold text-blue-900">
                  AI Field Check: {aiAnalysis.is_field_image === true ? "Field image" : aiAnalysis.is_field_image === false ? "Not a field image" : "Unknown"}
                </p>
                {aiAnalysis.summary ? (
                  <p className="text-sm text-blue-800">{aiAnalysis.summary}</p>
                ) : null}

                {aiGuidance.length ? (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-blue-900 mb-1">Improve Production</p>
                    <ul className="list-disc ml-5 space-y-1 text-sm text-blue-800">
                      {aiGuidance.map((item, index) => (
                        <li key={`guidance-${index}`}>{String(item)}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                {aiMaintenance.length ? (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-blue-900 mb-1">Maintenance</p>
                    <ul className="list-disc ml-5 space-y-1 text-sm text-blue-800">
                      {aiMaintenance.map((item, index) => (
                        <li key={`maintenance-${index}`}>{String(item)}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
