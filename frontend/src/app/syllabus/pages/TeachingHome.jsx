// src/app/syllabus/pages/TeachingHome.jsx

import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { HelpCircle } from "lucide-react";
import SubscriptionStatusCard from "../components/SubscriptionStatusCard";

const teachingServices = [
  { id: "my_subjects", route: "/teaching/my-subjects", icon: "📘" },
  { id: "timetable", route: "/teaching/timetable", icon: "🗓️" },
  { id: "master_timetable", route: "/teaching/master-timetable", icon: "🏫" },
  { id: "scheme", route: "/teaching/scheme", icon: "📑" },
  { id: "lesson_plan", route: "/teaching/lesson-plan", icon: "📝" },
  { id: "exam_results", route: "/teaching/exam-results", icon: "📊" },
  { id: "quiz", route: "/teaching/quiz", icon: "🧠" },
];

export default function TeachingHome() {
  const { t } = useTranslation("syllabus");
  const navigate = useNavigate();

  return (
    <div className="p-6 text-gray-800 dark:text-white">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-2">
        <h1 className="text-2xl font-semibold">
          {t("teaching_home.title")}
        </h1>
        <button
          onClick={() => navigate("/help#teaching")}
          className="flex items-center gap-1.5 shrink-0 px-3 py-1.5 rounded-lg text-sm font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors"
        >
          <HelpCircle className="w-4 h-4" />
          {t("teaching_home.help")}
        </button>
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-300 mb-6">
        {t("teaching_home.subtitle")}
      </p>

      <SubscriptionStatusCard />

      {/* Services Launcher */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {teachingServices.map((service) => (
          <button
            key={service.id}
            onClick={() => navigate(service.route)}
            className="
              flex flex-col items-center justify-center
              h-32 rounded-xl
              bg-white dark:bg-gray-800
              border border-gray-200 dark:border-gray-700
              shadow-sm hover:shadow-md
              transition-all duration-200
              hover:scale-[1.02]
              focus:outline-none
            "
          >
            <span className="text-4xl mb-2">{service.icon}</span>
            <span className="text-sm font-medium text-center">
              {t(`teaching_home.services.${service.id}`)}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}