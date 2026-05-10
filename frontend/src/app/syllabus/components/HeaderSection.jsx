// src/app/syllabus/components/HeaderSection.jsx
import React from "react";
import { ArrowLeft, CheckCircle, XCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";

const HeaderSection = ({ prefillData, backgroundLoading, cancelBackgroundLoading, t }) => {
  const navigate = useNavigate();

  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          title={t("common.back")}
        >
          <ArrowLeft size={20} className="text-gray-600 dark:text-gray-400" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t("lesson_plan.title")}
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {t("lesson_plan.subtitle")}
          </p>
        </div>
      </div>
      
      <div className="flex flex-col items-end gap-2">
        {prefillData && (
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {t("lesson_plan.prefilled_from")}: {prefillData.subject_name}
          </div>
        )}
        
        {backgroundLoading.loading && (
          <div className="flex items-center gap-2">
            <div className="w-48 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${backgroundLoading.progress}%` }}
              ></div>
            </div>
            <span className="text-xs text-gray-600 dark:text-gray-400">
              {backgroundLoading.completed}/{backgroundLoading.total}
            </span>
            <button
              onClick={cancelBackgroundLoading}
              className="text-xs text-red-600 hover:text-red-800"
              title={t("common.cancel")}
            >
              <XCircle size={14} />
            </button>
          </div>
        )}
        
        {backgroundLoading.status === 'completed' && (
          <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
            <CheckCircle size={16} />
            <span>{t("lesson_plan.background_complete")}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default HeaderSection;