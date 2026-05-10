import React from "react";
import { useTranslation } from "react-i18next";

export default function Services() {
  const { t } = useTranslation();

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-semibold">
        {t("business_dashboard.stats.services")}
      </h1>

      {/* Placeholder ya huduma */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((item) => (
          <div
            key={item}
            className="rounded-xl border dark:border-gray-700 p-4 shadow-sm bg-white dark:bg-gray-800"
          >
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">
              {t("business_dashboard.stats.services")} #{item}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t("business_dashboard.top_services.empty")}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}