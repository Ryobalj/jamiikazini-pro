// src/app/syllabus/components/TimetableForm.jsx
import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";

export default function TimetableForm({
  initialData = {},
  subjects = [],
  workstations = [],
  onSubmit,
  onCancel,
}) {
  const { t } = useTranslation("syllabus");

  const [form, setForm] = useState({
    workstation: "",
    subject_version: "",
    period: 1,
    timestart: "",
    timefinish: "",
    boys: "",
    girls: "",
    status: false,
  });

  const [error, setError] = useState(null);

  // Set defaults on mount or when initialData/arrays change
  useEffect(() => {
    if (initialData && Object.keys(initialData).length > 0) {
      setForm({
        workstation: initialData.workstation || "",
        subject_version: initialData.subject_version || "",
        period: initialData.period || 1,
        timestart: initialData.timestart || "",
        timefinish: initialData.timefinish || "",
        boys: initialData.boys || "",
        girls: initialData.girls || "",
        status: initialData.status || false,
      });
    } else {
      setForm({
        workstation: workstations[0]?.id || "",
        subject_version: subjects[0]?.id || "",
        period: 1,
        timestart: "",
        timefinish: "",
        boys: "",
        girls: "",
        status: false,
      });
    }
  }, [initialData, subjects, workstations]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Basic validation
    if (!form.workstation) {
      setError(t("my_timetable.alert_select_workstation") || "Please select a workstation");
      return;
    }
    if (!form.subject_version) {
      setError(t("my_timetable.alert_select_subject") || "Please select a subject");
      return;
    }
    if (!form.timestart || !form.timefinish) {
      setError(t("my_timetable.alert_time_required") || "Start and finish time required");
      return;
    }

    setError(null);
    onSubmit({
      ...form,
      boys: Number(form.boys),
      girls: Number(form.girls),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {/* Workstation */}
      <div>
        <label className="block text-sm font-medium mb-1">
          {t("my_timetable.workstation")}
        </label>
        <select
          name="workstation"
          value={form.workstation}
          onChange={handleChange}
          required
          className="w-full rounded-lg border px-3 py-2 dark:bg-gray-800"
        >
          <option value="">{t("my_timetable.select_workstation")}</option>
          {workstations.map((ws) => (
            <option key={ws.id} value={ws.id}>
              {ws.school_name} — {ws.teacher_info?.full_name || ws.teacher_info?.email}
            </option>
          ))}
        </select>
      </div>

      {/* Subject */}
      <div>
        <label className="block text-sm font-medium mb-1">
          {t("my_timetable.subject")}
        </label>
        <select
          name="subject_version"
          value={form.subject_version}
          onChange={handleChange}
          required
          className="w-full rounded-lg border px-3 py-2 dark:bg-gray-800"
        >
          <option value="">{t("my_timetable.select_subject")}</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} — {s.className}
            </option>
          ))}
        </select>
      </div>

      {/* Period */}
      <div>
        <label className="block text-sm font-medium mb-1">{t("my_timetable.period")}</label>
        <select
          name="period"
          value={form.period}
          onChange={handleChange}
          className="w-full rounded-lg border px-3 py-2 dark:bg-gray-800"
        >
          {[...Array(10)].map((_, i) => (
            <option key={i + 1} value={i + 1}>
              {t("my_timetable.period")} {i + 1}
            </option>
          ))}
        </select>
      </div>

      {/* Time */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">{t("my_timetable.start_time")}</label>
          <input
            type="time"
            name="timestart"
            value={form.timestart}
            onChange={handleChange}
            required
            className="w-full rounded-lg border px-3 py-2 dark:bg-gray-800"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">{t("my_timetable.end_time")}</label>
          <input
            type="time"
            name="timefinish"
            value={form.timefinish}
            onChange={handleChange}
            required
            className="w-full rounded-lg border px-3 py-2 dark:bg-gray-800"
          />
        </div>
      </div>

      {/* Students */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">{t("my_timetable.boys")}</label>
          <input
            type="number"
            name="boys"
            value={form.boys}
            onChange={handleChange}
            min="0"
            className="w-full rounded-lg border px-3 py-2 dark:bg-gray-800"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">{t("my_timetable.girls")}</label>
          <input
            type="number"
            name="girls"
            value={form.girls}
            onChange={handleChange}
            min="0"
            className="w-full rounded-lg border px-3 py-2 dark:bg-gray-800"
          />
        </div>
      </div>

      {/* Status */}
      <div className="flex items-center gap-2">
        <input type="checkbox" name="status" checked={form.status} onChange={handleChange} />
        <span className="text-sm">{t("my_timetable.confirm")}</span>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-2 pt-4">
        <button type="button" onClick={onCancel} className="px-4 py-2 rounded-lg border">
          {t("common.cancel")}
        </button>
        <button type="submit" className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700">
          {t("common.save")}
        </button>
      </div>
    </form>
  );
}