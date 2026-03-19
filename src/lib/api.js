import axios from "axios";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const envApiBaseUrl = (import.meta.env.VITE_API_BASE_URL || "").trim().replace(/\/$/, "");
const apiBaseUrl = envApiBaseUrl || DEFAULT_API_BASE_URL;

export function buildApiUrl(path) {
  if (!path.startsWith("/")) {
    return `${apiBaseUrl}/${path}`;
  }
  return `${apiBaseUrl}${path}`;
}

const apiClient = axios.create({
  baseURL: apiBaseUrl || undefined,
});

// Fetch analysis results from Django API (MongoDB backend)
export async function fetchAnalysisResults(phone = "") {
  const cleanedPhone = String(phone || "").trim();
  const params = cleanedPhone ? { phone: cleanedPhone } : undefined;

  const response = await apiClient.get("/api/results/", { params });
  return Array.isArray(response.data) ? response.data : [];
}

export async function generateReportTTS(payload) {
  const response = await apiClient.post("/api/tts/report/", payload, {
    headers: { "Content-Type": "application/json" },
  });
  return response?.data && typeof response.data === "object" ? response.data : null;
}
