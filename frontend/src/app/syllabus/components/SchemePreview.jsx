// src/app/syllabus/components/SchemePreview.jsx
import React from "react";
import { FileText, Download, Copy, Calendar, User, School } from "lucide-react";
import { useTranslation } from "react-i18next";
import SchemeTable from "./SchemeTable";
import SchemeGrid from "./SchemeGrid";

export default function SchemePreview({
  schemeData,
  viewMode,
  onDownloadPDF,
  pdfLoading
}) {
  const { t } = useTranslation("syllabus");
  const isPreview = schemeData._preview?.is_preview;
  const totalItems = schemeData.schedule_items?.length || 0;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <FileText size={20} />
              {isPreview ? t("scheme.preview_scheme") : t("scheme.title")}
            </h2>
            <div className="flex flex-wrap items-center gap-3 mt-1">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {schemeData.subject_name} - {schemeData.class_level_name} ({schemeData.year})
              </p>
              {isPreview && (
                <span className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full">
                  {t("common.preview")}: {schemeData._preview.preview_weeks}/{schemeData._preview.total_weeks} {t("common.weeks")}
                </span>
              )}
            </div>
            <div className="flex items-center gap-3 mt-2 text-xs">
              <span className="flex items-center gap-1 text-gray-500">
                <User size={12} />
                {schemeData.teacher_name || t("lesson_plan.teacher_name")}
              </span>
              <span className="flex items-center gap-1 text-gray-500">
                <School size={12} />
                {schemeData.school_name || t("lesson_plan.school_name")}
              </span>
              <span className="flex items-center gap-1 text-gray-500">
                <Calendar size={12} />
                {schemeData.academic_year || schemeData.year}
              </span>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-3">
            <div className="text-sm px-3 py-1.5 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full">
              <span className="font-medium">{t("common.weeks")}:</span> {schemeData.period_calculation?.available_weeks || 0}
            </div>
            <div className="text-sm px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-full">
              <span className="font-medium">{t("common.periods")}:</span> {schemeData.period_calculation?.total_periods || 0}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      {totalItems > 0 ? (
        viewMode === "table" ? (
          <SchemeTable schemeData={schemeData} />
        ) : (
          <SchemeGrid schemeData={schemeData} />
        )
      ) : (
        <div className="p-12 text-center">
          <p className="text-gray-600 dark:text-gray-400">
            {t("scheme.no_data")}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          {totalItems} {t("common.entries")}
        </div>
        <div className="flex gap-3">
          <button
            onClick={onDownloadPDF}
            disabled={pdfLoading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            <Download size={16} />
            {t("scheme.download_pdf")}
          </button>
          <button
            onClick={() => navigator.clipboard.writeText(JSON.stringify(schemeData, null, 2))}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-600 text-white text-sm rounded-lg hover:bg-gray-700"
          >
            <Copy size={16} />
            {t("common.copy")} JSON
          </button>
        </div>
      </div>
    </div>
  );
}