// src/app/syllabus/components/SubscriptionStatusCard.jsx
import React, { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { CheckCircle, XCircle, Wallet, FlaskConical } from "lucide-react";
import api from "@/lib/axios";
import { useAppContext } from "@/context/AppContext";
import { runWalletGatedRequest } from "@/lib/pendingPurchase";

export default function SubscriptionStatusCard() {
  const { t } = useTranslation("syllabus");
  const navigate = useNavigate();
  const { user } = useAppContext();
  const isAdmin = user?.role === "ADMIN";

  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [subscribing, setSubscribing] = useState(false);

  const fetchStatus = useCallback(async () => {
    if (!localStorage.getItem("access_token")) {
      // Anonymous visitor (e.g. on the public /teaching page) — skip the
      // authenticated call entirely so it can't trigger a login redirect.
      setStatus(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const res = await api.get("/syllabus/subscription/");
      setStatus(res.data);
    } catch (err) {
      // No workstation yet, or another error — just hide the card quietly.
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleSubscribe = async (adminTestPrice = false) => {
    setSubscribing(true);
    try {
      const result = await runWalletGatedRequest(
        api,
        navigate,
        { url: "/syllabus/subscription/", data: adminTestPrice ? { admin_test_price: true } : {} },
        { successPath: "/teaching", successMessageKey: "syllabus:subscription.subscribe_success" }
      );
      if (result.ok) {
        toast.success(t("subscription.subscribe_success"));
        await fetchStatus();
      }
      // insufficientBalance case: runWalletGatedRequest already redirected
      // to /jamiiwallet and stashed this exact request to resume after top-up.
    } catch (err) {
      toast.error(t("subscription.load_error"));
    } finally {
      setSubscribing(false);
    }
  };

  if (loading || !status) return null;

  const isActive = status.is_valid;

  return (
    <div
      className={`rounded-xl border p-4 mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 ${
        isActive
          ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
          : "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800"
      }`}
    >
      <div className="flex items-center gap-3">
        {isActive ? (
          <CheckCircle className="text-green-600 dark:text-green-400 shrink-0" size={22} />
        ) : (
          <XCircle className="text-amber-600 dark:text-amber-400 shrink-0" size={22} />
        )}
        <div>
          <p className="font-medium text-sm text-gray-800 dark:text-gray-100">
            {t("subscription.title")}:{" "}
            <span className={isActive ? "text-green-700 dark:text-green-400" : "text-amber-700 dark:text-amber-400"}>
              {isActive ? t("subscription.active") : t("subscription.inactive")}
            </span>
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {isActive && status.current_period_end
              ? `${t("subscription.expires_on")}: ${status.current_period_end}`
              : `${t("subscription.monthly_fee")}: ${status.monthly_fee}`}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => navigate("/jamiiwallet")}
          className="text-xs px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center gap-1"
        >
          <Wallet size={14} />
          {t("subscription.go_to_wallet")}
        </button>
        {!isActive && (
          <button
            onClick={() => handleSubscribe(false)}
            disabled={subscribing}
            className="text-xs px-3 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 disabled:opacity-60 text-white font-medium"
          >
            {subscribing ? t("subscription.renewing") : t("subscription.subscribe_now")}
          </button>
        )}
        {!isActive && isAdmin && (
          <button
            onClick={() => handleSubscribe(true)}
            disabled={subscribing}
            title={t("subscription.admin_test_price_hint")}
            className="text-xs px-3 py-2 rounded-lg border border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 disabled:opacity-60 font-medium flex items-center gap-1"
          >
            <FlaskConical size={14} />
            {t("subscription.admin_test_price_button")}
          </button>
        )}
      </div>
    </div>
  );
}
