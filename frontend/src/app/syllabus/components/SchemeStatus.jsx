// src/app/syllabus/components/SchemeStatus.jsx
import React from "react";
import { CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function SchemeStatus({ schemeData }) {
  const { t } = useTranslation("syllabus");
  
  const {
    hasWorkstation,
    hasSubjects,
    selectedSubject,
    selectedCalendar,
    timetableSubjects
  } = schemeData;

  return (
    <div className="flex flex-wrap gap-4 mt-4">
      {/* Workstation Status */}
      <div className={`flex items-center gap-2 text-sm ${hasWorkstation ? 'text-green-600' : 'text-red-600'}`}>
        <div className={`w-2 h-2 rounded-full ${hasWorkstation ? 'bg-green-500' : 'bg-red-500'}`}></div>
        {hasWorkstation ? (
          <>
            <CheckCircle size={14} />
            <span>{t("workstation.active")}</span>
          </>
        ) : (
          <>
            <XCircle size={14} />
            <span>{t("workstation.not_found")}</span>
          </>
        )}
      </div>

      {/* Subjects Status */}
      <div className={`flex items-center gap-2 text-sm ${hasSubjects ? 'text-green-600' : 'text-yellow-600'}`}>
        <div className={`w-2 h-2 rounded-full ${hasSubjects ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
        {hasSubjects ? (
          <>
            <CheckCircle size={14} />
            <span>{timetableSubjects.length} {t("my_subjects.subjects")}</span>
          </>
        ) : (
          <>
            <AlertCircle size={14} />
            <span>{t("my_subjects.no_subjects")}</span>
          </>
        )}
      </div>

      {/* Subject Selection Status */}
      <div className={`flex items-center gap-2 text-sm ${selectedSubject ? 'text-green-600' : 'text-gray-500'}`}>
        <div className={`w-2 h-2 rounded-full ${selectedSubject ? 'bg-green-500' : 'bg-gray-400'}`}></div>
        {selectedSubject ? t("scheme.requirement_subject") : t("scheme.select_subject")}
      </div>

      {/* Calendar Selection Status */}
      <div className={`flex items-center gap-2 text-sm ${selectedCalendar ? 'text-green-600' : 'text-gray-500'}`}>
        <div className={`w-2 h-2 rounded-full ${selectedCalendar ? 'bg-green-500' : 'bg-gray-400'}`}></div>
        {selectedCalendar ? t("scheme.requirement_calendar") : t("scheme.select_calendar")}
      </div>
    </div>
  );
}