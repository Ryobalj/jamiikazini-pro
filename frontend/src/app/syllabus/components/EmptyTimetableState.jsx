// src/app/syllabus/components/EmptyTimetableState.jsx
import React from "react";

export default function EmptyTimetableState({ t, onAdd }) {
  return (
    <div className="border border-dashed rounded-lg p-6 text-center text-gray-500">
      <p>{t("my_timetable.no_data")}</p>
      {onAdd && (
        <button
          onClick={onAdd}
          className="mt-4 px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
        >
          {t("my_timetable.add")}
        </button>
      )}
    </div>
  );
}