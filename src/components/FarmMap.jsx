<<<<<<< HEAD
import { useEffect } from "react";
import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

import { supabase } from "../lib/supabaseClient";

const DEFAULT_CENTER = [20.5937, 78.9629];

function getHealthColor(score) {
  if (score >= 75) {
    return "#16a34a";
  }
  if (score >= 45) {
    return "#ca8a04";
  }
  return "#dc2626";
}

function createColorMarker(score) {
  const color = getHealthColor(score);
  return L.divIcon({
    className: "",
    html: `<span style="display:block;width:18px;height:18px;border-radius:9999px;background:${color};border:2px solid white;box-shadow:0 0 0 2px rgba(15,23,42,.45);"></span>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
    popupAnchor: [0, -10],
  });
}

function FitToMarkers({ records }) {
  const map = useMap();

  useEffect(() => {
    if (!records.length) {
      return;
    }

    const points = records
      .filter((item) => Number.isFinite(item.latitude) && Number.isFinite(item.longitude))
      .map((item) => [item.latitude, item.longitude]);

    if (!points.length) {
      return;
    }

    if (points.length === 1) {
      map.setView(points[0], 15);
      return;
    }

    map.fitBounds(points, { padding: [32, 32] });
  }, [map, records]);
=======
import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import { buildApiUrl, fetchAnalysisResults } from "../lib/api";
import "leaflet/dist/leaflet.css";

const AREA_COLORS = [
  "#ef4444",
  "#f97316",
  "#eab308",
  "#22c55e",
  "#0ea5e9",
  "#6366f1",
  "#ec4899",
  "#14b8a6",
  "#84cc16",
  "#f43f5e",
];

function getImageUrl(url) {
  const value = typeof url === "string" ? url.trim() : "";
  if (!value) {
    return "";
  }

  if (/^https?:\/\//i.test(value) || value.startsWith("data:")) {
    return value;
  }

  if (value.startsWith("/")) {
    return buildApiUrl(value);
  }

  return buildApiUrl(`/${value}`);
}

function getAffectedPercentage(record) {
  const redRatioRaw = record?.actions?.red_ratio;
  const redRatio = Number(redRatioRaw);
  if (Number.isFinite(redRatio)) {
    return Math.max(0, Math.min(100, Math.round(redRatio * 100)));
  }

  const score = Number(record?.health_score);
  if (Number.isFinite(score)) {
    return Math.max(0, Math.min(100, Math.round(100 - score)));
  }
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d

  return null;
}

<<<<<<< HEAD
function FarmMap({ records, setRecords, onMarkerSelect }) {
  useEffect(() => {
    let isMounted = true;

    async function loadRecords() {
      const tables = ["AnalysisResult", "analyzer_analysisresult"];

      for (const tableName of tables) {
        const { data, error } = await supabase
          .from(tableName)
          .select("id,farm_name,health_score,actions,latitude,longitude,original_image_url,overlay_image_url,created_at")
          .order("id", { ascending: false });

        if (error) {
          console.error(`Supabase fetch error from ${tableName}:`, error.message);
          continue;
        }

        if (isMounted && Array.isArray(data)) {
          const normalized = data.map((item) => ({
            ...item,
            latitude: item.latitude == null ? null : Number(item.latitude),
            longitude: item.longitude == null ? null : Number(item.longitude),
            health_score: Number(item.health_score),
          }));
          setRecords(normalized);
        }
        return;
      }
    }

    loadRecords();
    return () => {
      isMounted = false;
    };
  }, [setRecords]);

  const markerRecords = records.filter(
    (item) => Number.isFinite(item.latitude) && Number.isFinite(item.longitude)
  );

  return (
    <div className="h-[26rem] w-full overflow-hidden rounded-xl border border-slate-200 shadow-sm md:h-[36rem]">
      <MapContainer center={DEFAULT_CENTER} zoom={5} className="h-full w-full">
=======
export default function FarmMap({
  analysisResults,
  setAnalysisResults,
  selectedMarker,
  setSelectedMarker,
  mapHeightClassName = "h-[500px]",
  onRecordSelect,
  autoFetch = true,
}) {
  const [error, setError] = useState("");

  useEffect(() => {
    if (!autoFetch) {
      return undefined;
    }

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
  }, [autoFetch, setAnalysisResults]);

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

  const affectedAreas = useMemo(() => {
    const sorted = [...validResults].sort((a, b) => {
      const aTime = Date.parse(a?.created_at || "") || 0;
      const bTime = Date.parse(b?.created_at || "") || 0;
      return aTime - bTime;
    });

    return sorted.map((record, index) => ({
      ...record,
      areaIndex: index + 1,
      areaColor: AREA_COLORS[index % AREA_COLORS.length],
    }));
  }, [validResults]);

  const center = useMemo(() => {
    if (affectedAreas.length > 0) {
      return [affectedAreas[0].latitude, affectedAreas[0].longitude];
    }
    return [20, 0];
  }, [affectedAreas]);

  return (
    <div className={`w-full ${mapHeightClassName} rounded-xl overflow-hidden border border-slate-200`}>
      {error ? <p className="p-3 text-sm text-red-600 bg-red-50">{error}</p> : null}
      <MapContainer center={center} zoom={5} className="w-full h-full">
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

<<<<<<< HEAD
        <FitToMarkers records={markerRecords} />

        {markerRecords.map((record) => (
          <Marker
            key={record.id}
            position={[record.latitude, record.longitude]}
            icon={createColorMarker(record.health_score)}
            eventHandlers={{
              click: () => onMarkerSelect(record),
            }}
          >
            <Popup>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-900">{record.farm_name}</p>
                <p className="text-xs text-slate-600">Health Score: {record.health_score}</p>
              </div>
            </Popup>
          </Marker>
        ))}
=======
        {affectedAreas.map((record) => {
          const isSelected = selectedMarker?.id === record.id;
          const affectedPercentage = getAffectedPercentage(record);
          const originalImageUrl = getImageUrl(record.original_image_url);
          const overlayImageUrl = getImageUrl(record.overlay_image_url);

          return (
          <CircleMarker
            key={record.id || `${record.latitude}-${record.longitude}-${record.areaIndex}`}
            center={[record.latitude, record.longitude]}
            radius={isSelected ? 12 : 9}
            pathOptions={{
              color: record.areaColor,
              fillColor: record.areaColor,
              fillOpacity: isSelected ? 0.9 : 0.65,
              weight: isSelected ? 4 : 2,
            }}
            eventHandlers={{
              click: () => {
                setSelectedMarker(record);
                if (onRecordSelect) {
                  onRecordSelect(record);
                }
              },
            }}
          >
            <Popup>
              <div className="text-sm space-y-2 min-w-[220px]">
                <p className="font-semibold" style={{ color: record.areaColor }}>
                  Affected Area {record.areaIndex}
                </p>
                <p>Health: {record.health_score ?? "N/A"}</p>
                {affectedPercentage != null ? <p>Affected: {affectedPercentage}%</p> : null}
                <p>
                  {record.latitude}, {record.longitude}
                </p>
                {record.field_zone ? <p>Zone: {record.field_zone}</p> : null}
                {originalImageUrl ? (
                  <img
                    src={originalImageUrl}
                    alt={`Affected area ${record.areaIndex}`}
                    className="w-full h-28 object-cover rounded border border-slate-200"
                  />
                ) : null}
                {overlayImageUrl ? (
                  <img
                    src={overlayImageUrl}
                    alt={`Overlay for area ${record.areaIndex}`}
                    className="w-full h-28 object-cover rounded border border-slate-200"
                  />
                ) : null}
                {selectedMarker?.id === record.id ? (
                  <p className="text-emerald-700">Selected</p>
                ) : null}
              </div>
            </Popup>
          </CircleMarker>
          );
        })}
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
      </MapContainer>
    </div>
  );
}
<<<<<<< HEAD

export default FarmMap;
=======
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
