// src/app/syllabus/components/SchemeSelection.jsx
import React from "react";
import { BookOpen, Calendar, RefreshCw } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function SchemeSelection({ 
  schemeData
}) {
  const { t } = useTranslation("syllabus");

  const {
    timetableSubjects,
    calendars,
    selectedSubject,
    setSelectedSubject,
    selectedCalendar,
    setSelectedCalendar,
    selectedSubjectInfo,
    selectedCalendarInfo,
    fetchInitialData,
    loading,
    pdfLoading
  } = schemeData;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <BookOpen size={20} />
            {t("scheme.selection")}
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {t("scheme.subtitle")}
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={fetchInitialData}
            disabled={loading || pdfLoading}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            title={t("common.refresh")}
          >
            <RefreshCw size={18} className="text-gray-600 dark:text-gray-400" />
          </button>
        </div>
      </div>

      {/* Selection Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Subject Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t("scheme.subject")} *
          </label>
          <select
            value={selectedSubject}
            onChange={(e) => {
              setSelectedSubject(e.target.value);
              schemeData.setSchemeData(null);
              schemeData.setPreviewMode(false);
            }}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-3 dark:bg-gray-700"
            disabled={loading || pdfLoading}
          >
            <option value="">{t("scheme.select_subject")}</option>
            {timetableSubjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} — {s.className}
              </option>
            ))}
          </select>
          
          {selectedSubjectInfo && (
            <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-gray-600">{t("scheme.subject")}:</span>
                  <span className="font-semibold">{selectedSubjectInfo.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-600">{t("my_subjects.class")}:</span>
                  <span className="font-semibold">{selectedSubjectInfo.className}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-600">{t("my_subjects.syllabus")}:</span>
                  <span className="font-semibold">{selectedSubjectInfo.syllabus_year}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-600">{t("scheme.periods_per_week")}:</span>
                  <span className="font-semibold">{selectedSubjectInfo.periods_per_week}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Calendar Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t("scheme.annual_calendar")} *
          </label>
          <select
            value={selectedCalendar}
            onChange={(e) => {
              setSelectedCalendar(e.target.value);
              schemeData.setSchemeData(null);
              schemeData.setPreviewMode(false);
            }}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-3 dark:bg-gray-700"
            disabled={loading || pdfLoading}
          >
            <option value="">{t("scheme.select_calendar")}</option>
            {calendars.map((c) => (
              <option key={c.id} value={c.id}>
                {c.year} - {c.institute || t("scheme.calendar")}
              </option>
            ))}
          </select>
          
          {selectedCalendarInfo && (
            <div className="mt-3 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-medium">{selectedCalendarInfo.year}</span>
                  <p className="text-xs text-gray-600">
                    {selectedCalendarInfo.total_learning_days} {t("common.learning_days")}
                  </p>
                </div>
                <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-800 text-green-800 dark:text-green-200 rounded-full">
                  {selectedCalendarInfo.term_start_date?.split('-')[0] || 'Jan'} - 
                  {selectedCalendarInfo.annual_break_start_date?.split('-')[0] || 'Dec'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}