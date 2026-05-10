// src/components/LocationPicker.jsx
import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix marker icon issue in Leaflet + React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require("leaflet/dist/images/marker-icon-2x.png"),
  iconUrl: require("leaflet/dist/images/marker-icon.png"),
  shadowUrl: require("leaflet/dist/images/marker-shadow.png"),
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