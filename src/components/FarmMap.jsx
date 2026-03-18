import { useEffect, useMemo, useState } from "react";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import { fetchAnalysisResults } from "../lib/supabase";
import "leaflet/dist/leaflet.css";

const markerShadow = "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png";

const redIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const yellowIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-yellow.png",
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const greenIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function getMarkerIcon(score) {
  if (score < 40) return redIcon;
  if (score <= 70) return yellowIcon;
  return greenIcon;
}

export default function FarmMap({
  analysisResults,
  setAnalysisResults,
  selectedMarker,
  setSelectedMarker,
}) {
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadResults() {
      try {
        setError("");
        const rows = await fetchAnalysisResults();
        if (mounted) {
          setAnalysisResults(rows);
        }
      } catch (err) {
        if (mounted) {
          setError(err.message || "Failed to load map data.");
        }
      }
    }

    loadResults();

    return () => {
      mounted = false;
    };
  }, [setAnalysisResults]);

  const validResults = useMemo(
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

  const center = useMemo(() => {
    if (validResults.length > 0) {
      return [validResults[0].latitude, validResults[0].longitude];
    }
    return [20, 0];
  }, [validResults]);

  return (
    <div className="w-full h-[500px] rounded-xl overflow-hidden border border-slate-200">
      {error ? <p className="p-3 text-sm text-red-600 bg-red-50">{error}</p> : null}
      <MapContainer center={center} zoom={5} className="w-full h-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {validResults.map((record) => (
          <Marker
            key={record.id}
            position={[record.latitude, record.longitude]}
            icon={getMarkerIcon(record.health_score ?? 0)}
            eventHandlers={{
              click: () => setSelectedMarker(record),
            }}
          >
            <Popup>
              <div className="text-sm">
                <p className="font-semibold">Health: {record.health_score}</p>
                <p>
                  {record.latitude}, {record.longitude}
                </p>
                {selectedMarker?.id === record.id ? (
                  <p className="text-emerald-700">Selected</p>
                ) : null}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
