// src/app/syllabus/components/LessonDetailsForm.jsx
import React, { useState, useEffect } from "react";
import { Save } from "lucide-react";
import { toast } from "react-toastify";
import api from "@/lib/axios";

const LessonDetailsForm = ({ form, setForm, currentSubjectInfo, selectedTimetable, setSelectedTimetable, t }) => {
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value
    }));
  };

  // Registered boys/girls come straight from the selected timetable entry
  // and are editable right here, since pupils shift in/out mid-term.
  const [regBoys, setRegBoys] = useState("");
  const [regGirls, setRegGirls] = useState("");
  const [savingRegistered, setSavingRegistered] = useState(false);

  useEffect(() => {
    setRegBoys(String(currentSubjectInfo?.registeredBoys ?? ""));
    setRegGirls(String(currentSubjectInfo?.registeredGirls ?? ""));
  }, [selectedTimetable?.id, currentSubjectInfo?.registeredBoys, currentSubjectInfo?.registeredGirls]);

  const registeredDirty =
    Boolean(selectedTimetable) &&
    ((Number(regBoys) || 0) !== (currentSubjectInfo?.registeredBoys ?? 0) ||
      (Number(regGirls) || 0) !== (currentSubjectInfo?.registeredGirls ?? 0));

  const saveRegistered = async () => {
    if (!selectedTimetable) return;
    setSavingRegistered(true);
    try {
      const res = await api.patch(`/syllabus/timetables/${selectedTimetable.id}/`, {
        registeredboys: Number(regBoys) || 0,
        registeredgirls: Number(regGirls) || 0,
      });
      setSelectedTimetable(res.data);
      toast.success(t("common.update_success"));
    } catch (err) {
      console.error(err);
      toast.error(t("common.error"));
    } finally {
      setSavingRegistered(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {t("lesson_plan.lesson_details")}
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {t("lesson_plan.date")} *
          </label>
          <input
            type="date"
            name="date"
            value={form.date}
            onChange={handleChange}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2.5 dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
            required
          />
        </div>

        {/* Period */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {t("lesson_plan.period")} *
          </label>
          <input
            type="number"
            name="period"
            min="1"
            max="10"
            value={form.period}
            onChange={handleChange}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2.5 dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
          />
        </div>

        {/* Start Time */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {t("lesson_plan.start_time")}
          </label>
          <input
            type="time"
            name="timestart"
            value={form.timestart}
            onChange={handleChange}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2.5 dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
          />
        </div>

        {/* End Time */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {t("lesson_plan.end_time")}
          </label>
          <input
            type="time"
            name="timefinish"
            value={form.timefinish}
            onChange={handleChange}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2.5 dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
          />
        </div>

        {/* Boys Registered */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {t("timetable.registered_boys")}
          </label>
          <input
            type="number"
            min="0"
            value={regBoys}
            onChange={(e) => setRegBoys(e.target.value)}
            disabled={!selectedTimetable}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2.5 dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent disabled:opacity-50"
          />
        </div>

        {/* Girls Registered */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {t("timetable.registered_girls")}
          </label>
          <input
            type="number"
            min="0"
            value={regGirls}
            onChange={(e) => setRegGirls(e.target.value)}
            disabled={!selectedTimetable}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2.5 dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent disabled:opacity-50"
          />
        </div>

        {registeredDirty && (
          <div className="md:col-span-2 -mt-2">
            <button
              type="button"
              onClick={saveRegistered}
              disabled={savingRegistered}
              className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 disabled:opacity-50"
            >
              <Save size={16} />
              {savingRegistered ? t("common.saving") : t("common.save_changes")}
            </button>
          </div>
        )}

        {/* Boys Present */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {t("lesson_plan.boys")}
          </label>
          <input
            type="number"
            name="boys_attended"
            min="0"
            value={form.boys_attended}
            onChange={handleChange}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2.5 dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
            placeholder={currentSubjectInfo?.registeredBoys || "0"}
          />
        </div>

        {/* Girls Present */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {t("lesson_plan.girls")}
          </label>
          <input
            type="number"
            name="girls_attended"
            min="0"
            value={form.girls_attended}
            onChange={handleChange}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2.5 dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
            placeholder={currentSubjectInfo?.registeredGirls || "0"}
          />
        </div>

        {/* Students Who Understood */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {t("lesson_plan.understood_students")}
          </label>
          <input
            type="number"
            name="managed_count"
            min="0"
            value={form.managed_count}
            onChange={handleChange}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2.5 dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
          />
        </div>
      </div>

      {/* Checkboxes */}
      <div className="mt-6 space-y-3">
        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            name="is_song"
            checked={form.is_song}
            onChange={handleChange}
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
          />
          <span className="text-gray-700 dark:text-gray-300">{t("lesson_plan.is_song")}</span>
        </label>
        
        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            name="repeat_next"
            checked={form.repeat_next}
            onChange={handleChange}
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
          />
          <span className="text-gray-700 dark:text-gray-300">{t("lesson_plan.repeat_next")}</span>
        </label>
      </div>
    </div>
  );
};

export default LessonDetailsForm;