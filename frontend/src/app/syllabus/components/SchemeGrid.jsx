// src/app/syllabus/components/SchemeGrid.jsx - REVISED VERSION
import React from "react";
import { Calendar, Clock, BookOpen, Activity, CheckCircle } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function SchemeGrid({ schemeData }) {
  const { t } = useTranslation("syllabus");
  const items = schemeData.schedule_items || [];

  if (items.length === 0) {
    return (
      <div className="p-12 text-center">
        <p className="text-gray-600 dark:text-gray-400">
          {t("scheme.no_data")}
        </p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((row, idx) => {
          // Check for umahiri/uwezo in different possible keys
          const mainCompetence = row.main_competence || row.umahiri_mkuu || row.uwezo_mkuu || row.mainCompetence;
          const specificCompetence = row.specific_competence || row.umahiri_mahususi || row.uwezo_maalum || row.specificCompetence;
          const studentActivity = row.student_activity || row.shughuli_za_mwanafunzi || row.learning_activity;
          const learningActivity = row.learning_activity || row.shughuli_za_kufundisha || row.teaching_activity;
          
          const isBreak = studentActivity?.includes("LIKIZO") || studentActivity?.includes("MITIHANI");
          const isCompleted = row.remarks?.includes("malizika") || row.remarks?.includes("Imemalizika");
          
          return (
            <div
              key={idx}
              className={`border rounded-lg p-4 transition-all hover:shadow-md ${
                isBreak 
                  ? 'border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20' 
                  : isCompleted
                  ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/10'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
              }`}
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 dark:text-white line-clamp-2">
                    {mainCompetence || specificCompetence || studentActivity || learningActivity || t("common.activity")}
                  </h4>
                  {specificCompetence && specificCompetence !== mainCompetence && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                      {specificCompetence}
                    </p>
                  )}
                </div>
                
                {(row.periods > 0 || row.vipindi > 0) && (
                  <span className="ml-2 px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full whitespace-nowrap">
                    {(row.periods || row.vipindi || 0)} {t("common.periods")}
                  </span>
                )}
              </div>
              
              {learningActivity && (
                <div className="mt-2 flex items-start gap-2">
                  <Activity size={14} className="text-gray-500 dark:text-gray-400 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                    {learningActivity}
                  </p>
                </div>
              )}
              
              {studentActivity && (
                <div className="mt-2 flex items-start gap-2">
                  <BookOpen size={14} className="text-gray-500 dark:text-gray-400 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-gray-500 dark:text-gray-500 line-clamp-2">
                    {studentActivity}
                  </p>
                </div>
              )}
              
              <div className="mt-4 pt-3 border-t border-gray-100 dark:border-gray-700 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                  <Calendar size={12} />
                  <span>
                    {row.month || row.mwezi} 
                    {row.week_number && row.week_number > 0 && ` • ${t("common.week")} ${row.week_number}`}
                    {row.wiki && row.wiki > 0 && ` • ${t("common.week")} ${row.wiki}`}
                  </span>
                </div>
                
                <div className="flex items-center gap-2">
                  {isBreak && (
                    <span className="text-xs px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 rounded-full">
                      🎉 {studentActivity}
                    </span>
                  )}
                  
                  {isCompleted && (
                    <span className="text-xs text-green-600 dark:text-green-400" title={t("common.completed")}>
                      <CheckCircle size={14} />
                    </span>
                  )}
                </div>
              </div>
              
              {/* Additional Info on Hover */}
              <div className="mt-3 text-xs text-gray-500 dark:text-gray-500 opacity-0 hover:opacity-100 transition-opacity">
                <div className="grid grid-cols-2 gap-2">
                  {row.methodology && (
                    <div>
                      <span className="font-medium">{t("scheme.headers.methodology")}:</span> {row.methodology}
                    </div>
                  )}
                  {row.assessment_criteria && (
                    <div>
                      <span className="font-medium">{t("scheme.headers.assessment_criteria")}:</span> {row.assessment_criteria}
                    </div>
                  )}
                  {row.mbinu && (
                    <div>
                      <span className="font-medium">{t("scheme.headers.methodology")}:</span> {row.mbinu}
                    </div>
                  )}
                  {row.vigezo_vya_upimaji && (
                    <div>
                      <span className="font-medium">{t("scheme.headers.assessment_criteria")}:</span> {row.vigezo_vya_upimaji}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Summary */}
      <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {items.length}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {t("common.total_activities")}
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
              {items.filter(item => item.periods > 0 || item.vipindi > 0)
                .reduce((sum, item) => sum + (item.periods || item.vipindi || 0), 0)}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {t("common.total_periods")}
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-lg font-bold text-green-600 dark:text-green-400">
              {items.filter(item => 
                item.remarks?.includes("malizika") || 
                item.remarks?.includes("Imemalizika") ||
                item.maoni?.includes("malizika") ||
                item.maoni?.includes("Imemalizika")
              ).length}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {t("common.completed")}
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
              {items.filter(item => 
                item.student_activity?.includes("LIKIZO") || 
                item.student_activity?.includes("MITIHANI") ||
                item.shughuli_za_mwanafunzi?.includes("LIKIZO") ||
                item.shughuli_za_mwanafunzi?.includes("MITIHANI")
              ).length}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {t("common.holidays_exams")}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}