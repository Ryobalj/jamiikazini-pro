// src/pages/HomePage.jsx

import React from "react";
import { useNavigate } from "react-router-dom";
import { useAppContext } from "@/context/AppContext";
import { useTranslation } from "react-i18next"; // ✅ ongeza

export default function HomePage() {
  const { user } = useAppContext();
  const navigate = useNavigate();
  const { t } = useTranslation(); // ✅ tumia i18n

  return (
    <div className="font-sans px-4 py-8 sm:px-8">
      <h1 className="text-3xl font-bold mb-2 text-blue-700 dark:text-blue-400">
        {t("home.welcome")}
      </h1>

      <p className="text-gray-600 dark:text-gray-300 max-w-xl leading-relaxed">
        {t("home.description")}
      </p>

      {!user && (
        <button
          onClick={() => navigate("/security/login/")}
          className="mt-6 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow transition"
        >
          {t("home.login_cta")}
        </button>
      )}
    </div>
  );
}