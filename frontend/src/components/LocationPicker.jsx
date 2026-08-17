// src/components/LocationPicker.jsx

import React, { useCallback, useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer, Marker, useMap, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { Search, LocateFixed, Loader2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

// Fix marker icon issue in Leaflet + React (ESM imports; require() breaks under Vite)
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const DAR_ES_SALAAM = [-6.7924, 39.2083];

async function reverseGeocode(lat, lon) {
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=18`
    );
    const data = await res.json();
    return data?.display_name || "";
  } catch {
    return "";
  }
}

function FlyToPosition({ position }) {
  const map = useMap();
  useEffect(() => {
    if (position) map.flyTo(position, 15);
  }, [position, map]);
  return null;
}

export default function LocationPicker({ lat, lon, setLat, setLon, onAddressChange, placeholder }) {
  const { t } = useTranslation("logistics");
  const [position, setPosition] = useState(lat && lon ? [lat, lon] : null);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searching, setSearching] = useState(false);
  const [locating, setLocating] = useState(false);
  const [locateError, setLocateError] = useState("");
  const debounceRef = useRef(null);

  const applyPosition = useCallback(
    async (newLat, newLon, label) => {
      setPosition([newLat, newLon]);
      setLat(newLat);
      setLon(newLon);
      setLocateError("");
      if (label) {
        setQuery(label);
        onAddressChange?.(label);
      } else {
        const address = await reverseGeocode(newLat, newLon);
        if (address) {
          setQuery(address);
          onAddressChange?.(address);
        }
      }
    },
    [setLat, setLon, onAddressChange]
  );

  function LocationMarker() {
    useMapEvents({
      click(e) {
        setShowSuggestions(false);
        applyPosition(e.latlng.lat, e.latlng.lng, null);
      },
    });
    return position ? <Marker position={position} /> : null;
  }

  // Best-effort auto-detect on first mount only, if the parent didn't already
  // supply a position - stays quiet on failure since the search box and the
  // "use my location" button both give the user an explicit way to recover.
  useEffect(() => {
    if (lat && lon) return;
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => applyPosition(pos.coords.latitude, pos.coords.longitude, null),
      () => {}
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Pick up a position the parent supplies *after* mount (e.g. a saved last
  // drop-off address arriving from an async fetch) - the initial useState
  // above only runs once, so without this the map would never move.
  useEffect(() => {
    if (lat == null || lon == null) return;
    setPosition((prev) => (prev && prev[0] === lat && prev[1] === lon ? prev : [lat, lon]));
  }, [lat, lon]);

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      setLocateError(t("location_picker.gps_unavailable", "Kifaa chako hakiwezi kutambua eneo (GPS)."));
      return;
    }
    setLocating(true);
    setLocateError("");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        applyPosition(pos.coords.latitude, pos.coords.longitude, null);
        setLocating(false);
      },
      (err) => {
        setLocating(false);
        if (err.code === 1) {
          setLocateError(t("location_picker.location_denied", "Umekataa ruhusa ya eneo. Tafuta au bonyeza kwenye ramani badala yake."));
        } else if (err.code === 3) {
          setLocateError(t("location_picker.location_timeout", "Imechukua muda mrefu kupata eneo. Jaribu tena."));
        } else {
          setLocateError(t("location_picker.location_failed", "Imeshindwa kupata eneo lako."));
        }
      }
    );
  };

  const handleSearchChange = (value) => {
    setQuery(value);
    setShowSuggestions(true);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (value.trim().length < 3) {
      setSuggestions([]);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await fetch(
          `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(value)}&limit=5`
        );
        const data = await res.json();
        setSuggestions(Array.isArray(data) ? data : []);
      } catch {
        setSuggestions([]);
      } finally {
        setSearching(false);
      }
    }, 400);
  };

  const handleSelectSuggestion = (s) => {
    setSuggestions([]);
    setShowSuggestions(false);
    applyPosition(parseFloat(s.lat), parseFloat(s.lon), s.display_name);
  };

  return (
    <div className="space-y-2">
      <div className="relative">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            <input
              type="text"
              value={query}
              onChange={(e) => handleSearchChange(e.target.value)}
              onFocus={() => setShowSuggestions(true)}
              placeholder={placeholder || t("location_picker.search_placeholder", "Tafuta eneo...")}
              className="w-full pl-8 pr-8 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white"
            />
            {searching && (
              <Loader2 className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-gray-400" />
            )}
          </div>
          <button
            type="button"
            onClick={handleUseMyLocation}
            disabled={locating}
            title={t("location_picker.use_my_location", "Tumia Eneo Langu")}
            className="flex items-center justify-center w-9 h-9 flex-shrink-0 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 disabled:opacity-50"
          >
            {locating ? <Loader2 className="w-4 h-4 animate-spin" /> : <LocateFixed className="w-4 h-4" />}
          </button>
        </div>

        {showSuggestions && suggestions.length > 0 && (
          <ul className="absolute z-[1000] w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-56 overflow-y-auto">
            {suggestions.map((s) => (
              <li key={s.place_id}>
                <button
                  type="button"
                  onClick={() => handleSelectSuggestion(s)}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  {s.display_name}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {locateError && <p className="text-xs text-red-500">{locateError}</p>}

      <div className="w-full h-72 rounded overflow-hidden border relative z-0">
        <MapContainer center={position || DAR_ES_SALAAM} zoom={position ? 15 : 6} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          <LocationMarker />
          <FlyToPosition position={position} />
        </MapContainer>
      </div>
    </div>
  );
}
