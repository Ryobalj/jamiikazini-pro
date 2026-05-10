// src/app/kiini/pages/StaffProfiles.jsx
import React from "react";
import { useTranslation } from "react-i18next";

export default function StaffProfiles() {
  const { t } = useTranslation("kiini");

  return (
    <div className="p-4 text-gray-800 dark:text-white space-y-2">
      <h2 className="text-xl font-semibold">{t("staff.title")}</h2>
      <p>{t("staff.description")}</p>
    </div>
  );
}