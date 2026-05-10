// src/app/syllabus/components/BackgroundLoadingStatus.jsx
import React from "react";
import { RefreshCw } from "lucide-react";

const BackgroundLoadingStatus = ({ backgroundLoading, t }) => {
  if (!backgroundLoading.loading) return null;

  return (
    <div className="mb-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <RefreshCw size={20} className="text-blue-600 dark:text-blue-400 animate-spin" />
          <div>
            <h3 className="font-medium text-blue-800 dark:text-blue-300">
              {t("lesson_plan.background_loading")}
            </h3>
            <p className="text-sm text-blue-600 dark:text-blue-400">
              {t("lesson_plan.loading_subjects", { 
                completed: backgroundLoading.completed, 
                total: backgroundLoading.total 
              })}
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm font-medium text-blue-700 dark:text-blue-300">
            {Math.round(backgroundLoading.progress)}%
          </div>
          <div className="text-xs text-blue-600 dark:text-blue-400">
            {t("lesson_plan.optimizing_data")}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BackgroundLoadingStatus;