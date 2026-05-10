import React from "react";
import { useTranslation } from "react-i18next";

export default function Settings() {
  const { t } = useTranslation();

  return (
    <div className="p-4 space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
        {t("tabs.settings")}
      </h1>

      {/* Maelezo ya akaunti au biashara */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border dark:border-gray-700">
        <h2 className="text-lg font-medium text-gray-800 dark:text-gray-100 mb-2">
          {t("user.profile")}
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {t("user_home.description")}
        </p>
      </div>

      {/* Mipangilio ya lugha */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border dark:border-gray-700">
        <h2 className="text-lg font-medium text-gray-800 dark:text-gray-100 mb-2">
          {t("tabs.settings")} – 🌍 {t("search.placeholder")}
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {t("auth_login.recaptcha_not_ready")}
        </p>
      </div>

      {/* Placeholder kwa future settings */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border dark:border-gray-700">
        <h2 className="text-lg font-medium text-gray-800 dark:text-gray-100 mb-2">
          🔒 {t("auth.password")}
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {t("auth_register.errors.password_length")}
        </p>
      </div>
    </div>
  );
}