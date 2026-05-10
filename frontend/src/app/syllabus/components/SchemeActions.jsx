// src/app/syllabus/components/SchemeActions.jsx
import React from "react";
import { 
  Eye, 
  FileText, 
  Download, 
  Trash2, 
  LayoutGrid, 
  List,
  FileCheck,
  EyeOff,
  RefreshCw
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

export default function SchemeActions({
  schemeData,
  viewMode,
  setViewMode
}) {
  const { t } = useTranslation("syllabus");
  
  // Extract functions and states from schemeData
  const { 
    isFormValid, 
    loading, 
    pdfLoading, 
    previewLoading,
    schemeInfo,
    handleFetchScheme,
    handlePreviewScheme,
    handleDownloadPDF,
    clearScheme,
    fetchInitialData
  } = schemeData;

  // Helper function to handle generation with feedback
  const handleGenerateWithFeedback = async () => {
    if (!isFormValid) {
      toast.warning(t("scheme.select_subject_and_calendar"), {
        position: "bottom-right",
        autoClose: 3000,
      });
      return;
    }

    try {
      await handleFetchScheme();
    } catch (error) {
      console.error("Generation failed:", error);
    }
  };

  // Helper function to handle preview with feedback
  const handlePreviewWithFeedback = async () => {
    if (!isFormValid) {
      toast.warning(t("scheme.select_subject_and_calendar"), {
        position: "bottom-right",
        autoClose: 3000,
      });
      return;
    }

    try {
      await handlePreviewScheme();
    } catch (error) {
      console.error("Preview failed:", error);
    }
  };

  // Helper function to handle PDF download with feedback
  const handleDownloadWithFeedback = async () => {
    if (!isFormValid) {
      toast.warning(t("scheme.select_subject_and_calendar"), {
        position: "bottom-right",
        autoClose: 3000,
      });
      return;
    }

    try {
      await handleDownloadPDF();
    } catch (error) {
      console.error("Download failed:", error);
    }
  };

  // Check if we have existing scheme data
  const hasExistingScheme = schemeInfo?.schemeData;
  const isPreview = schemeInfo?.schemeData?._preview?.is_preview;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      {/* Header with quick stats */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${isFormValid ? 'bg-green-100 dark:bg-green-900/30' : 'bg-gray-100 dark:bg-gray-900'}`}>
            {isFormValid ? (
              <FileCheck size={20} className="text-green-600 dark:text-green-400" />
            ) : (
              <FileText size={20} className="text-gray-500 dark:text-gray-400" />
            )}
          </div>
          <div>
            <h3 className="font-medium text-gray-900 dark:text-white">
              {isFormValid ? t("scheme.ready_to_generate") : t("scheme.select_subject_and_calendar")}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {isFormValid 
                ? t("scheme.can_start_generating") 
                : t("scheme.select_first")
              }
            </p>
          </div>
        </div>

        {/* Quick Stats */}
        {hasExistingScheme && (
          <div className="flex items-center gap-3 text-sm">
            <div className="px-3 py-1.5 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full">
              {schemeInfo.schemeData.schedule_items?.length || 0} {t("common.activities")}
            </div>
            <div className="px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-full">
              {schemeInfo.schemeData.period_calculation?.total_periods || 0} {t("common.periods")}
            </div>
            {isPreview && (
              <div className="px-3 py-1.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 rounded-full">
                {t("common.preview")}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Main Action Buttons */}
      <div className="flex flex-wrap justify-between items-center gap-4">
        {/* Primary Actions */}
        <div className="flex flex-wrap gap-3">
          {/* Generate Button */}
          <button
            onClick={handleGenerateWithFeedback}
            disabled={loading || !isFormValid}
            className="inline-flex items-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:shadow-md active:scale-95"
            title={t("scheme.generate_scheme")}
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                {t("scheme.generating")}
              </>
            ) : hasExistingScheme && !isPreview ? (
              <>
                <RefreshCw size={18} />
                {t("common.refresh")}
              </>
            ) : (
              <>
                <FileText size={18} />
                {t("scheme.generate_scheme")}
              </>
            )}
          </button>

          {/* Download PDF Button */}
          <button
            onClick={handleDownloadWithFeedback}
            disabled={pdfLoading || !isFormValid || !hasExistingScheme}
            className="inline-flex items-center gap-2 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:shadow-md active:scale-95"
            title={t("scheme.download_pdf")}
          >
            {pdfLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                {t("common.downloading")}
              </>
            ) : (
              <>
                <Download size={18} />
                {t("scheme.download_pdf")}
              </>
            )}
          </button>
        </div>

        {/* View Mode & Tools */}
        <div className="flex items-center gap-3">
          {/* View Toggle */}
          <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-900 p-1 rounded-lg">
            <button
              onClick={() => setViewMode("table")}
              className={`px-3 py-2 rounded-md transition-all duration-200 ${
                viewMode === "table" 
                  ? "bg-white dark:bg-gray-800 shadow-sm text-blue-600 dark:text-blue-400" 
                  : "hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
              }`}
              title={t("common.view_table")}
            >
              <List size={18} />
            </button>
            <button
              onClick={() => setViewMode("grid")}
              className={`px-3 py-2 rounded-md transition-all duration-200 ${
                viewMode === "grid" 
                  ? "bg-white dark:bg-gray-800 shadow-sm text-blue-600 dark:text-blue-400" 
                  : "hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
              }`}
              title={t("common.view_grid")}
            >
              <LayoutGrid size={18} />
            </button>
          </div>

          {/* Refresh Data Button */}
          <button
            onClick={fetchInitialData}
            disabled={loading || pdfLoading || previewLoading}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title={t("common.refresh")}
          >
            <RefreshCw size={18} className={`text-gray-600 dark:text-gray-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex flex-wrap gap-4 text-xs">
          <div className={`flex items-center gap-2 ${isFormValid ? 'text-green-600 dark:text-green-400' : 'text-gray-500'}`}>
            <div className={`w-2 h-2 rounded-full ${isFormValid ? 'bg-green-500' : 'bg-gray-400'}`}></div>
            {isFormValid ? t("scheme.ready_to_generate") : t("scheme.waiting_for_selection")}
          </div>
          
          {hasExistingScheme && (
            <>
              <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
                <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                {isPreview ? t("scheme.preview_created") : t("scheme.full_scheme_created")}
              </div>
              
              <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400">
                <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                {schemeInfo.schemeData.period_calculation?.total_periods || 0} {t("common.periods")}
              </div>
            </>
          )}
          
          {(loading || pdfLoading || previewLoading) && (
            <div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400">
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-yellow-500"></div>
              {loading ? t("common.loading") : pdfLoading ? t("common.downloading") : t("scheme.generating_preview")}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}