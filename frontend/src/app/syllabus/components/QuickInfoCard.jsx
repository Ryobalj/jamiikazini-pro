// src/app/syllabus/components/QuickInfoCard.jsx
import React from "react";
import { Calendar, Clock, Users } from "lucide-react";

const QuickInfoCard = ({ form, currentSubjectInfo, t }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {t("lesson_plan.quick_info")}
      </h2>
      
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Calendar className="text-gray-500" size={18} />
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">{t("lesson_plan.selected_date")}</div>
            <div className="font-medium">{form.date}</div>
          </div>
        </div>
        
        {currentSubjectInfo && (
          <>
            <div className="flex items-center gap-3">
              <Users className="text-gray-500" size={18} />
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">{t("my_subjects.total_students")}</div>
                <div className="font-medium">{currentSubjectInfo.totalStudents}</div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Clock className="text-gray-500" size={18} />
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">{t("lesson_plan.duration")}</div>
                <div className="font-medium">
                  {form.timestart} - {form.timefinish}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default QuickInfoCard;