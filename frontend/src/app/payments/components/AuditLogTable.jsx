// src/app/payments/components/AuditLogTable.jsx

import React, { useEffect, useState } from "react";
import api from "@/lib/axios"; // instance ya axios yenye access token
import { useTranslation } from "react-i18next";

export default function AuditLogTable() {
  const { t } = useTranslation();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [otpRequired, setOtpRequired] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [otpUrl, setOtpUrl] = useState(null);
  const [otpToken, setOtpToken] = useState(null);

  const [page, setPage] = useState(1);
  const [pageCount, setPageCount] = useState(1);

  const fetchLogs = async (page = 1) => {
    setLoading(true);
    setError(null);
    try {
      const headers = otpToken ? { Authorization: `Bearer ${otpToken}` } : {};
      const res = await api.get("/payments/audit_logs/", { params: { page }, headers });

      const results = res.data.results || [];
      const count = res.data.count || 0;
      const perPage = results.length || 1;

      setLogs(results);
      setPageCount(Math.ceil(count / perPage));
      setPage(page);
      setOtpRequired(false); // success, no OTP needed
    } catch (err) {
      const data = err.response?.data;
      
    if (data?.["2fa_required"]) {
      setOtpRequired(true);
      setOtpUrl(data.otp_request_url);
    } else {
        setError(data?.detail || t("errors.failedToLoad"));
      }
    } finally {
      setLoading(false);
    }
  };

  const requestOtp = async () => {
    if (!otpUrl) return;
    try {
      await api.post(otpUrl);
      alert(t("otp.sent")); // au message UI nzuri
    } catch (err) {
      alert(err.response?.data?.detail || t("errors.failedToLoad"));
    }
  };

  const submitOtp = async () => {
    try {
      const res = await api.post("/security/otp/verify/", { code: otpCode });
      setOtpToken(res.data.otp_token);
      setOtpRequired(false);
      setOtpCode("");
      fetchLogs(page); // retry logs request
    } catch (err) {
      alert(err.response?.data?.detail || t("errors.failedToLoad"));
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  if (loading) return <p>{t("loading")}...</p>;

  if (error) {
    return (
      <p className="text-red-500">
        {error}{" "}
        <button onClick={() => fetchLogs(page)} className="underline text-blue-500">
          {t("retry")}
        </button>
      </p>
    );
  }

  if (otpRequired) {
    return (
      <div className="p-4 border rounded bg-yellow-50">
        <p className="mb-2 text-yellow-700">{t("otp.required")}</p>
        <div className="flex gap-2">
          <input
            type="text"
            value={otpCode}
            onChange={(e) => setOtpCode(e.target.value)}
            placeholder={t("otp.enter_code")}
            className="border px-2 py-1 rounded"
          />
          <button
            onClick={submitOtp}
            className="px-3 py-1 bg-green-500 text-white rounded"
          >
            {t("otp.submit")}
          </button>
          <button
            onClick={requestOtp}
            className="px-3 py-1 bg-blue-500 text-white rounded"
          >
            {t("otp.resend")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border border-gray-200">
        <thead className="bg-gray-100">
          <tr>
            <th className="px-4 py-2">{t("user")}</th>
            <th className="px-4 py-2">{t("action")}</th>
            <th className="px-4 py-2">{t("target")}</th>
            <th className="px-4 py-2">{t("description")}</th>
            <th className="px-4 py-2">{t("metadata")}</th>
            <th className="px-4 py-2">{t("ip_address")}</th>
            <th className="px-4 py-2">{t("timestamp")}</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id} className="border-b">
              <td className="px-4 py-2">{log.user_name}</td>
              <td className="px-4 py-2">{log.action_display}</td>
              <td className="px-4 py-2">{log.content_type_name || "-"}</td>
              <td className="px-4 py-2">{log.description || "-"}</td>
              <td className="px-4 py-2 text-xs break-all">
                {log.metadata ? JSON.stringify(log.metadata) : "-"}
              </td>
              <td className="px-4 py-2">{log.ip_address || "-"}</td>
              <td className="px-4 py-2">
                {new Date(log.created_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {pageCount > 1 && (
        <div className="flex justify-center gap-2 mt-4">
          <button
            disabled={page <= 1}
            onClick={() => fetchLogs(page - 1)}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            {t("prev")}
          </button>
          <span className="px-2 py-1">
            {t("page")} {page} / {pageCount}
          </span>
          <button
            disabled={page >= pageCount}
            onClick={() => fetchLogs(page + 1)}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            {t("next")}
          </button>
        </div>
      )}
    </div>
  );
}