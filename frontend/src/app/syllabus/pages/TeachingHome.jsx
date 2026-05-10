// src/app/syllabus/pages/TeachingHome.jsx

import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

const teachingServices = [
  { id: "my_subjects", route: "/teaching/my-subjects", icon: "📘" },
  { id: "timetable", route: "/teaching/timetable", icon: "🗓️" },
  { id: "scheme", route: "/teaching/scheme", icon: "📑" },
  { id: "lesson_plan", route: "/teaching/lesson-plan", icon: "📝" },
];

export default function TeachingHome() {
  const { t } = useTranslation("syllabus");
  const navigate = useNavigate();

  return (
    <div className="p-6 text-gray-800 dark:text-white">
      {/* Header */}
      <h1 className="text-2xl font-semibold mb-2">
        {t("teaching_home.title")}
      </h1>

      <p className="text-sm text-gray-600 dark:text-gray-300 mb-6">
        {t("teaching_home.subtitle")}
      </p>

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