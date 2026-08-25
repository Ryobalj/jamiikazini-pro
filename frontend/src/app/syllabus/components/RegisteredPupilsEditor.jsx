// src/app/syllabus/components/RegisteredPupilsEditor.jsx
import React, { useState } from "react";
import { Pencil, Check, X } from "lucide-react";
import { toast } from "react-toastify";
import api from "@/lib/axios";

// Shared editor for a timetable entry's registered boys/girls count, since
// pupils shift in/out mid-term and this needs updating from more than one
// screen (Lesson Plan's subject summary, and its Lesson Details form).
const RegisteredPupilsEditor = ({ selectedTimetable, setSelectedTimetable, currentSubjectInfo, t }) => {
  const [editing, setEditing] = useState(false);
  const [regBoys, setRegBoys] = useState("");
  const [regGirls, setRegGirls] = useState("");
  const [saving, setSaving] = useState(false);

  const startEdit = () => {
    setRegBoys(String(currentSubjectInfo?.registeredBoys ?? 0));
    setRegGirls(String(currentSubjectInfo?.registeredGirls ?? 0));
    setEditing(true);
  };

  const cancelEdit = () => setEditing(false);

  const save = async () => {
    if (!selectedTimetable) return;
    setSaving(true);
    try {
      const res = await api.patch(`/syllabus/timetables/${selectedTimetable.id}/`, {
        registeredboys: Number(regBoys) || 0,
        registeredgirls: Number(regGirls) || 0,
      });
      setSelectedTimetable(res.data);
      setEditing(false);
      toast.success(t("common.update_success"));
    } catch (err) {
      console.error(err);
      toast.error(t("common.error"));
    } finally {
      setSaving(false);
    }
  };

  if (!currentSubjectInfo) return null;

  if (!editing) {
    return (
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600 dark:text-gray-400">
          {t("my_subjects.total_students")}:{" "}
          <span className="font-semibold text-gray-900 dark:text-white">
            {currentSubjectInfo.totalStudents}
          </span>{" "}
          <span className="text-gray-500 dark:text-gray-400">
            ({t("timetable.registered_boys")}: {currentSubjectInfo.registeredBoys}, {t("timetable.registered_girls")}: {currentSubjectInfo.registeredGirls})
          </span>
        </span>
        <button
          type="button"
          onClick={startEdit}
          className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 p-1"
          title={t("common.edit")}
        >
          <Pencil size={16} />
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-end gap-3 text-sm">
      <div>
        <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
          {t("timetable.registered_boys")}
        </label>
        <input
          type="number"
          min="0"
          value={regBoys}
          onChange={(e) => setRegBoys(e.target.value)}
          className="w-24 border border-gray-300 dark:border-gray-600 rounded-lg p-1.5 dark:bg-gray-700 dark:text-white"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
          {t("timetable.registered_girls")}
        </label>
        <input
          type="number"
          min="0"
          value={regGirls}
          onChange={(e) => setRegGirls(e.target.value)}
          className="w-24 border border-gray-300 dark:border-gray-600 rounded-lg p-1.5 dark:bg-gray-700 dark:text-white"
        />
      </div>
      <button
        type="button"
        onClick={save}
        disabled={saving}
        className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300 p-1.5 disabled:opacity-50"
        title={t("common.save")}
      >
        <Check size={18} />
      </button>
      <button
        type="button"
        onClick={cancelEdit}
        disabled={saving}
        className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 p-1.5 disabled:opacity-50"
        title={t("common.cancel")}
      >
        <X size={18} />
      </button>
    </div>
  );
};

export default RegisteredPupilsEditor;
