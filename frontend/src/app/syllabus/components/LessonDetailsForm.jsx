// src/app/syllabus/components/LessonDetailsForm.jsx
import React from "react";

const LessonDetailsForm = ({ form, setForm, currentSubjectInfo, t }) => {
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({ 
      ...prev, 
      [name]: type === "checkbox" ? checked : value 
    }));
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