// src/app/payments/pages/admin/AdminAuditPage.jsx

import React, { useState } from "react";
import AuditLogTable from "../../components/AuditLogTable";
import api from "@/lib/axios";
import { useTranslation } from "react-i18next";


export default function AdminAuditPage() {
  const { t } = useTranslation();
  const [otpSent, setOtpSent] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const requestOtp = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.post("/security/otp/request/");
      setOtpSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || t("failed_to_request_otp"));
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async () => {
    if (!otp) return setError(t("enter_otp"));
    setLoading(true);
    setError(null);
    try {
      await api.post("/security/otp/verify/", { otp });
      setOtpVerified(true);
    } catch (err) {
      setError(err.response?.data?.detail || t("failed_to_verify_otp"));
    } finally {
      setLoading(false);
    }
  };

  if (!otpSent) {
    return (
      <div className="max-w-md mx-auto mt-20 p-6 bg-white rounded shadow">
        <h1 className="text-xl font-bold mb-4">{t("2fa_required")}</h1>
        <p className="mb-4">{t("otp_request_message")}</p>
        {error && <p className="text-red-500 mb-2">{error}</p>}
        <button
          onClick={requestOtp}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {loading ? t("loading") + "..." : t("request_otp")}
        </button>
      </div>
    );
  }

  if (otpSent && !otpVerified) {
    return (
      <div className="max-w-md mx-auto mt-20 p-6 bg-white rounded shadow">
        <h1 className="text-xl font-bold mb-4">{t("enter_otp")}</h1>
        {error && <p className="text-red-500 mb-2">{error}</p>}
        <input
          type="text"
          value={otp}
          onChange={(e) => setOtp(e.target.value)}
          className="border px-3 py-2 w-full mb-4 rounded"
          placeholder={t("otp_placeholder")}
        />
        <button
          onClick={verifyOtp}
          disabled={loading}
          className="px-4 py-2 bg-green-600 text-white rounded disabled:opacity-50"
        >
          {loading ? t("loading") + "..." : t("verify_otp")}
        </button>
      </div>
    );
  }

  // Baada ya successful OTP verification
  return (
    <div className="max-w-6xl mx-auto mt-4">
      <h1 className="text-2xl font-bold mb-4">{t("audit_logs")}</h1>
      <AuditLogTable />
    </div>
  );
}