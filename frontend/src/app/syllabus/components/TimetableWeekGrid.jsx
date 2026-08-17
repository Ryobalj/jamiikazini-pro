// src/app/syllabus/components/TimetableWeekGrid.jsx
import React, { useMemo } from "react";

const DAYS = [1, 2, 3, 4, 5, 6];

export default function TimetableWeekGrid({ timetables, t, onEdit }) {
  const dayLabel = (day) =>
    t(`timetable.days.${["", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"][day]}`);

  const periods = useMemo(() => {
    const set = new Set(
      timetables.filter((row) => row.period).map((row) => row.period)
    );
    for (let p = 1; p <= 8; p++) set.add(p);
    return Array.from(set).sort((a, b) => a - b);
  }, [timetables]);

  const cellFor = (day, period) =>
    timetables.find((row) => row.day_of_week === day && row.period === period);

  return (
    <div className="mb-6 overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <table className="min-w-full text-sm border-collapse">
        <thead className="bg-gray-100 dark:bg-gray-800">
          <tr>
            <th className="border px-2 py-2 text-left">{t("timetable.period")}</th>
            {DAYS.map((day) => (
              <th key={day} className="border px-2 py-2">{dayLabel(day)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {periods.map((period) => (
            <tr key={period}>
              <td className="border px-2 py-2 font-medium text-center bg-gray-50 dark:bg-gray-900">
                {period}
              </td>
              {DAYS.map((day) => {
                const cell = cellFor(day, period);
                return (
                  <td
                    key={day}
                    className={`border px-2 py-2 text-center ${
                      cell ? "cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20" : ""
                    }`}
                    onClick={() => cell && onEdit?.(cell)}
                  >
                    {cell ? (
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">
                          {cell.subject_display || cell.subject_name}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {cell.class_level_display}
                        </div>
                      </div>
                    ) : (
                      <span className="text-gray-300 dark:text-gray-700">—</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
