// src/components/LocationPicker.jsx
import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
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

export default function LocationPicker({ lat, lon, setLat, setLon }) {
  const [position, setPosition] = useState([lat || -6.7924, lon || 39.2083]); // Default: Dar es Salaam

  function LocationMarker() {
    useMapEvents({
      click(e) {
        const { lat, lng } = e.latlng;
        setPosition([lat, lng]);
        setLat(lat);
        setLon(lng);
      },
    });

    return <Marker position={position} />;
  }

  useEffect(() => {
    if (!lat || !lon) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude } = pos.coords;
          setPosition([latitude, longitude]);
          setLat(latitude);
          setLon(longitude);
        },
        () => {
          // fail silently if no GPS
        }
      );
    }
  }, []);

  return (
    <div className="w-full h-72 mt-2 rounded overflow-hidden border">
      <MapContainer center={position} zoom={13} style={{ height: "100%", width: "100%" }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <LocationMarker />
      </MapContainer>
    </div>
  );
}