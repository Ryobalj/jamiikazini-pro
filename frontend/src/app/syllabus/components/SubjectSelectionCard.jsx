// src/app/syllabus/components/SubjectSelectionCard.jsx
import React from "react";

const SubjectSelectionCard = ({
  timetables,
  selectedTimetable,
  setSelectedTimetable,
  setForm,
  currentSubjectInfo,
  loadActivitiesForTimetable,
  t
}) => {
  const handleTimetableChange = (e) => {
    const timetable = timetables.find(t => t.id === Number(e.target.value));
    setSelectedTimetable(timetable);
    
    if (timetable) {
      setForm(prev => ({
        ...prev,
        boys_attended: timetable.registeredboys || "",
        girls_attended: timetable.registeredgirls || "",
      }));
      
      loadActivitiesForTimetable(timetable.id);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {t("lesson_plan.lesson_details")}
      </h2>
      
      {/* Timetable Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {t("lesson_plan.subject")} *
        </label>
        <select
          className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-3 dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
          onChange={handleTimetableChange}
          value={selectedTimetable?.id || ""}
        >
          <option value="">{t("lesson_plan.select_subject")}</option>
          {timetables.map((timetableItem) => (
            <option key={timetableItem.id} value={timetableItem.id}>
              {timetableItem.subject_name} - {timetableItem.class_level_name}
            </option>
          ))}
        </select>
        
        {/* Selected Subject Info */}
        {currentSubjectInfo && (
          <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">{t("lesson_plan.subject")}:</span>
                <span className="font-semibold ml-2">{currentSubjectInfo.subject}</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">{t("my_subjects.class")}:</span>
                <span className="font-semibold ml-2">{currentSubjectInfo.class}</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">{t("my_subjects.total_students")}:</span>
                <span className="font-semibold ml-2">{currentSubjectInfo.totalStudents}</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">{t("my_subjects.periods_per_week")}:</span>
                <span className="font-semibold ml-2">{currentSubjectInfo.periods}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SubjectSelectionCard;