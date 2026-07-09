// src/pages/auth/VerifyEmail.jsx

import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "@/lib/axios";

export default function VerifyEmail() {
  const { user_id, token } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [message, setMessage] = useState(t("auth_verify_email.verifying"));
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function verify() {
      try {
        const res = await api.get(`/auth/verify-email/${user_id}/${token}/`);
        setMessage(
          res.data.message || t("auth_verify_email.success")
        );
      } catch {
        setError(t("auth_verify_email.error"));
      } finally {
        setLoading(false);
      }
    }

    verify();
  }, [user_id, token, t]);

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white dark:bg-gray-800 rounded shadow text-center">
      <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-white">
        {t("auth_verify_email.title")}
      </h2>

      {loading ? (
        <p className="text-blue-500">{t("auth_verify_email.loading")}</p>
      ) : error ? (
        <p className="text-red-600">{error}</p>
      ) : (
        <>
          <p className="text-green-600 mb-4">{message}</p>
          <button
            onClick={() => navigate("/security/login")}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            {t("auth_verify_email.to_login")}
          </button>
        </>
      )}
    </div>
  );
}