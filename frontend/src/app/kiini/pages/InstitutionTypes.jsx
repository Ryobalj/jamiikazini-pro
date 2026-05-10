// src/app/kiini/pages/InstitutionTypes.jsx
import React from "react";
import { useTranslation } from "react-i18next";

export default function InstitutionTypes() {
  const { t } = useTranslation("kiini");

  return (
    <div className="p-4 text-gray-800 dark:text-white space-y-2">
      <h2 className="text-xl font-semibold">{t("types.title")}</h2>
      <p>{t("types.description")}</p>
    </div>
  );
}