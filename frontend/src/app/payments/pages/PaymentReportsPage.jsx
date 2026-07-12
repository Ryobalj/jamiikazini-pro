// src/app/payments/pages/PaymentReportsPage.jsx

import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import api from "@/lib/axios";
import { BarChart3, Loader2, PlusCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";

const REPORT_TYPES = [
  { value: "TRANSACTION_SUMMARY", label: "Muhtasari wa Malipo" },
  { value: "REVENUE_ANALYSIS", label: "Uchambuzi wa Mapato" },
  { value: "DAILY_SUMMARY", label: "Muhtasari wa Kila Siku" },
];

const STATUS_STYLES = {
  GENERATING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  COMPLETED: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  FAILED: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  CANCELLED: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
};

export default function PaymentReportsPage() {
  const { t } = useTranslation("payments");

  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reportType, setReportType] = useState(REPORT_TYPES[0].value);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchReports = useCallback(() => {
    setLoading(true);
    api
      .get("/payments/payment-reports/my-reports/")
      .then((res) => setReports(res.data?.results || res.data || []))
      .catch(() => setReports([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!startDate || !endDate) {
      toast.error(t("reports.errors.dates_required") || "Chagua tarehe ya kuanzia na kumalizia.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/payments/payment-reports/", {
        report_type: reportType,
        start_date: startDate,
        end_date: endDate,
      });
      toast.success(t("reports.created") || "Ripoti inatengenezwa...");
      fetchReports();
    } catch (error) {
      const errors = error.response?.data;
      const firstError = errors && typeof errors === "object" ? Object.values(errors)[0] : null;
      toast.error((Array.isArray(firstError) ? firstError[0] : firstError) || t("reports.errors.failed") || "Imeshindwa.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <Card>
        <CardHeader title={t("reports.generate") || "Tengeneza Ripoti"} icon={<BarChart3 className="w-5 h-5" />} divider />
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-3">
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            >
              {REPORT_TYPES.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
            <div className="grid grid-cols-2 gap-3">
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
              />
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <Button type="submit" disabled={submitting} className="bg-purple-600 hover:bg-purple-700">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <PlusCircle className="w-4 h-4 mr-2" />}
              {t("reports.submit") || "Tengeneza"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader
          title={t("reports.title") || "Ripoti Zangu"}
          actions={
            <Button size="sm" variant="ghost" onClick={fetchReports}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          }
          divider
        />
        <CardContent>
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin mx-auto text-gray-400" />
          ) : reports.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("reports.empty") || "Hakuna ripoti bado."}
            </p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {reports.map((r) => (
                <div key={r.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{r.report_type}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {new Date(r.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                      STATUS_STYLES[r.status] || STATUS_STYLES.GENERATING
                    }`}
                  >
                    {r.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
