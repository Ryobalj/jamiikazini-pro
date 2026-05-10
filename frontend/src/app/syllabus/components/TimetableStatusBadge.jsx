// src/app/syllabus/components/TimetableStatusBadge.jsx
import React from "react";

export default function TimetableStatusBadge({ confirmed, labelConfirmed, labelPending }) {
  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-medium
        ${
          confirmed
            ? "bg-green-100 text-green-700"
            : "bg-yellow-100 text-yellow-700"
        }`}
    >
      {confirmed ? labelConfirmed : labelPending}
    </span>
  );
}