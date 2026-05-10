// src/app/syllabus/components/TimetableGroup.jsx
import React from "react";
import { Edit, Trash2 } from "lucide-react";

export default function TimetableGroup({ group, t, onEdit, onDelete }) {
  return (
    <div className="mb-4 border rounded-lg p-4">
      <h2 className="font-semibold mb-2">
        {group.subjectName} — {group.className}
      </h2>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm border-collapse">
          <thead className="bg-gray-100 dark:bg-gray-800">
            <tr>
              <th className="border px-2 py-1">{t("my_timetable.period")}</th>
              <th className="border px-2 py-1">{t("my_timetable.start_time")}</th>
              <th className="border px-2 py-1">{t("my_timetable.end_time")}</th>
              <th className="border px-2 py-1">{t("my_timetable.boys")}</th>
              <th className="border px-2 py-1">{t("my_timetable.girls")}</th>
              <th className="border px-2 py-1">{t("my_timetable.status")}</th>
              <th className="border px-2 py-1">{t("common.actions")}</th>
            </tr>
          </thead>
          <tbody>
            {group.rows.map((row) => (
              <tr key={row.id} className="hover:bg-gray-50 dark:hover:bg-gray-900">
                <td className="border px-2 py-1">{row.period}</td>
                <td className="border px-2 py-1">{row.timestart}</td>
                <td className="border px-2 py-1">{row.timefinish}</td>
                <td className="border px-2 py-1">{row.boys}</td>
                <td className="border px-2 py-1">{row.girls}</td>
                <td className="border px-2 py-1">{row.status ? "✔️" : "❌"}</td>
                <td className="border px-2 py-1 flex gap-2">
                  <button onClick={() => onEdit(row)}>
                    <Edit size={16} />
                  </button>
                  <button onClick={() => onDelete(row)}>
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}