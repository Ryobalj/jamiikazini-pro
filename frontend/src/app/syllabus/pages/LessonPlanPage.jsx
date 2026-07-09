// src/app/syllabus/pages/LessonPlanPage.jsx
import React, { useState } from "react";
import { useTranslation } from "react-i18next";

import HeaderSection from "../components/HeaderSection";
import BackgroundLoadingStatus from "../components/BackgroundLoadingStatus";
import SubjectSelectionCard from "../components/SubjectSelectionCard";
import ActivitySearchCard from "../components/ActivitySearchCard";
import LessonDetailsForm from "../components/LessonDetailsForm";
import ActionsCard from "../components/ActionsCard";
import QuickInfoCard from "../components/QuickInfoCard";

import { useLessonPlanData } from "../hooks/useLessonPlanData";
import { useBackgroundLoading } from "../hooks/useBackgroundLoading";

export default function LessonPlanPage() {
  const { t } = useTranslation(["syllabus", "common"]);
  
  // State for selected activities
  const [selectedLearningActivity, setSelectedLearningActivity] = useState(null);
  const [selectedSpecificActivity, setSelectedSpecificActivity] = useState(null);

  // Custom hooks for state management
  const {
    timetables,
    selectedTimetable,
    setSelectedTimetable,
    form,
    setForm,
    initialLoading,
    prefillData,
    currentSubjectInfo,
    canUsePage,
    error
  } = useLessonPlanData();

  const {
    backgroundLoading,
    cancelBackgroundLoading
  } = useBackgroundLoading(timetables);

  // Handle learning activity selection
  const handleLearningActivitySelect = (activity) => {
    setSelectedLearningActivity(activity);
    console.log("Selected Learning Activity:", activity);
  };

  // Handle specific activity selection
  const handleSpecificActivitySelect = (activity) => {
    setSelectedSpecificActivity(activity);
    console.log("Selected Specific Activity:", activity);
  };

  if (initialLoading) {
    return (
      <div className="flex flex-col justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-3 mt-4 text-lg">{t("common.loading")}...</span>
        <p className="text-sm text-gray-500 mt-2">{t("lesson_plan.loading_initial")}</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-6">
      <HeaderSection 
        prefillData={prefillData}
        backgroundLoading={backgroundLoading}
        cancelBackgroundLoading={cancelBackgroundLoading}
        t={t}
      />

      <BackgroundLoadingStatus 
        backgroundLoading={backgroundLoading}
        t={t}
      />

      <div className={`transition-all duration-300 ${!canUsePage ? "blur-sm opacity-50 pointer-events-none" : ""}`}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column */}
          <div className="lg:col-span-2 space-y-6">
            <SubjectSelectionCard
              timetables={timetables}
              selectedTimetable={selectedTimetable}
              setSelectedTimetable={setSelectedTimetable}
              form={form}
              setForm={setForm}
              currentSubjectInfo={currentSubjectInfo}
              t={t}
            />

            <ActivitySearchCard
              selectedTimetable={selectedTimetable}
              onLearningActivitySelect={handleLearningActivitySelect}
              onSpecificActivitySelect={handleSpecificActivitySelect}
              t={t}
            />

            <LessonDetailsForm
              form={form}
              setForm={setForm}
              currentSubjectInfo={currentSubjectInfo}
              t={t}
            />
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            <ActionsCard
              selectedTimetable={selectedTimetable}
              selectedSpecificActivity={selectedSpecificActivity}
              selectedLearningActivity={selectedLearningActivity}
              t={t}
            />

            <QuickInfoCard
              form={form}
              currentSubjectInfo={currentSubjectInfo}
              t={t}
            />

            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
                <div className="flex items-center gap-2 text-red-700 dark:text-red-400 mb-2">
                  <span className="font-medium">{t("common.error")}</span>
                </div>
                <p className="text-sm text-red-600 dark:text-red-300">{error}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}