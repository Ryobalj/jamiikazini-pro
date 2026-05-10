// src/app/kiini/pages/KiiniDashboard.jsx
import React from "react";
import { useTranslation } from "react-i18next";

export default function KiiniDashboard() {
  const { t } = useTranslation("kiini");

  return (
    <div className="p-4 text-gray-800 dark:text-white space-y-2">
      <h1 className="text-2xl font-semibold">{t("dashboard.title")}</h1>
      <p>{t("dashboard.welcomeMessage")}</p>
    </div>
  );
}