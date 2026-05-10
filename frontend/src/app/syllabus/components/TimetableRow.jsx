// src/app/syllabus/components/TimetableRow.jsx
import React from "react";
import { Pencil, Trash2 } from "lucide-react";
import TimetableStatusBadge from "./TimetableStatusBadge";

export default function TimetableRow({
  row,
  t,
  onEdit,
  onDelete,
}) {
  return (
    <div
      className="
        flex flex-col sm:flex-row sm:items-center
        justify-between gap-3
        px-4 py-3
      "
    >
      <div className="flex flex-wrap gap-4 text-sm">
        <span>
          <strong>{t("my_timetable.period")}:</strong> {row.period}
        </span>

        <span>
          <strong>{t("my_timetable.time")}:</strong>{" "}
          {row.timestart} – {row.timefinish}
        </span>

        <span>
          <strong>{t("my_timetable.students")}:</strong>{" "}
          {row.boys}/{row.girls}
        </span>

        <TimetableStatusBadge
          confirmed={row.status}
          labelConfirmed={t("my_timetable.confirmed")}
          labelPending={t("my_timetable.pending")}
        />
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => onEdit(row)}
          className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
          aria-label={t("common.edit")}
        >
          <Pencil size={16} />
        </button>

        <button
          onClick={() => onDelete(row)}
          className="p-2 rounded text-red-600 hover:bg-red-100 dark:hover:bg-red-900/20"
          aria-label={t("common.delete")}
        >
          <Trash2 size={16} />
        </button>
      </div>
    </div>
  );
}