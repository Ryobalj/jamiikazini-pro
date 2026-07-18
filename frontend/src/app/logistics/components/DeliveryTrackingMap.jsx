// src/app/logistics/components/DeliveryTrackingMap.jsx

import React, { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import { useTranslation } from "react-i18next";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const courierIcon = new L.DivIcon({
  html: '<div style="background:#2563eb;width:16px;height:16px;border-radius:50%;border:2px solid white;box-shadow:0 0 4px rgba(0,0,0,0.5);"></div>',
  className: "",
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

function toLatLng(point) {
  if (!point?.coordinates) return null;
  const [lon, lat] = point.coordinates;
  return [lat, lon];
}

function FitBounds({ points }) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 0) return;
    if (points.length === 1) {
      map.setView(points[0], 14);
    } else {
      map.fitBounds(points, { padding: [30, 30] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(points)]);
  return null;
}

export default function DeliveryTrackingMap({ pickupLocation, dropoffLocation, courierLocation }) {
  const { t } = useTranslation("orders");

  const pickup = toLatLng(pickupLocation);
  const dropoff = toLatLng(dropoffLocation);
  const courier = toLatLng(courierLocation);
  const points = [pickup, dropoff, courier].filter(Boolean);

  if (points.length === 0) return null;

  return (
    <div className="w-full h-72 rounded overflow-hidden border">
      <MapContainer center={points[0]} zoom={13} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <FitBounds points={points} />
        {pickup && (
          <Marker position={pickup}>
            <Popup>{t("map_pickup", "Sehemu ya Kuchukua")}</Popup>
          </Marker>
        )}
        {dropoff && (
          <Marker position={dropoff}>
            <Popup>{t("map_dropoff", "Sehemu ya Kufikisha")}</Popup>
          </Marker>
        )}
        {courier && (
          <Marker position={courier} icon={courierIcon}>
            <Popup>{t("map_courier", "Dereva")}</Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  );
}
