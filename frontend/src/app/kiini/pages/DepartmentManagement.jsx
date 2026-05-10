// src/app/kiini/pages/DepartmentManagement.jsx
import React from "react";
import { useTranslation } from "react-i18next";

export default function DepartmentManagement() {
  const { t } = useTranslation("kiini");

  return (
    <div className="p-4 text-gray-800 dark:text-white space-y-2">
      <h2 className="text-xl font-semibold">{t("departments.title")}</h2>
      <p>{t("departments.description")}</p>
    </div>
  );
}