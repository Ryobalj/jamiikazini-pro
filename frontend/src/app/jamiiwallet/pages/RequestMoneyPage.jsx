// src/app/jamiiwallet/pages/RequestMoneyPage.jsx

import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import {
  ArrowDown,
  ArrowLeft,
  Loader2,
  Check,
  X,
  Clock,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useCurrency } from "@/context/CurrencyContext";

const STATUS_STYLES = {
  PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  ACCEPTED: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  DECLINED: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  CANCELLED: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
};

const STATUS_ICONS = {
  PENDING: Clock,
  ACCEPTED: CheckCircle,
  DECLINED: XCircle,
  CANCELLED: XCircle,
};

export default function RequestMoneyPage() {
  const { t } = useTranslation("jamiiwallet");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();

  const [payer, setPayer] = useState("");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [requests, setRequests] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [respondingId, setRespondingId] = useState(null);

  const fetchRequests = useCallback(() => {
    setLoadingList(true);
    api
      .get("/jamiiwallet/requests/")
      .then((res) => {
        const data = res.data?.results || res.data || [];
        setRequests(data);
      })
      .catch(() => setRequests([]))
      .finally(() => setLoadingList(false));
  }, []);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!payer.trim()) {
      toast.error(t("request.errors.payer_required") || "Weka namba ya simu au barua pepe ya mlipaji.");
      return;
    }
    const numericAmount = parseFloat(amount);
    if (!numericAmount || numericAmount <= 0) {
      toast.error(t("request.errors.amount_required") || "Weka kiasi sahihi.");
      return;
    }

    setSubmitting(true);
    try {
      await api.post("/jamiiwallet/requests/", {
        payer_identifier: payer.trim(),
        amount: numericAmount,
        note: note.trim(),
      });
      toast.success(t("request.success") || "Ombi limetumwa.");
      setPayer("");
      setAmount("");
      setNote("");
      fetchRequests();
    } catch (error) {
      const errors = error.response?.data?.errors || error.response?.data;
      const firstError =
        (errors && typeof errors === "object" && Object.values(errors)[0]) ||
        error.response?.data?.detail;
      toast.error(
        (Array.isArray(firstError) ? firstError[0] : firstError) ||
          t("request.errors.failed") ||
          "Imeshindwa kutuma ombi. Jaribu tena."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const respond = async (id, action) => {
    setRespondingId(id);
    try {
      await api.post(`/jamiiwallet/requests/${id}/${action}/`);
      toast.success(
        action === "accept"
          ? t("request.accepted") || "Umekubali ombi na pesa imetumwa."
          : t("request.declined") || "Umekataa ombi."
      );
      fetchRequests();
    } catch (error) {
      toast.error(error.response?.data?.detail || t("request.errors.action_failed") || "Imeshindwa.");
    } finally {
      setRespondingId(null);
    }
  };

  const incoming = requests.filter((r) => r.direction === "incoming");
  const outgoing = requests.filter((r) => r.direction === "outgoing");

  const renderRequestRow = (r, showActions) => {
    const StatusIcon = STATUS_ICONS[r.status] || Clock;
    return (
      <div
        key={r.id}
        className="flex items-center justify-between py-3 border-b border-gray-100 dark:border-gray-700 last:border-0"
      >
        <div>
          <p className="font-medium text-gray-900 dark:text-white">
            {showActions ? r.requester_name : r.payer_name}
          </p>
          {r.note && <p className="text-sm text-gray-500 dark:text-gray-400">{r.note}</p>}
          <p className="text-lg font-semibold text-purple-600 dark:text-purple-400">
            {formatCurrency(r.amount)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {showActions && r.status === "PENDING" ? (
            <>
              <Button
                size="sm"
                className="bg-green-600 hover:bg-green-700"
                disabled={respondingId === r.id}
                onClick={() => respond(r.id, "accept")}
              >
                {respondingId === r.id ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Check className="w-4 h-4" />
                )}
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={respondingId === r.id}
                onClick={() => respond(r.id, "decline")}
              >
                <X className="w-4 h-4" />
              </Button>
            </>
          ) : (
            <span
              className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                STATUS_STYLES[r.status] || STATUS_STYLES.PENDING
              }`}
            >
              <StatusIcon className="w-3 h-3" />
              {t(`request.status.${r.status.toLowerCase()}`) || r.status}
            </span>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <button
        onClick={() => navigate("/jamiiwallet")}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        {t("back") || "Rudi"}
      </button>

      <Card className="mb-6">
        <CardHeader
          title={t("request.title") || "Omba Pesa"}
          icon={<ArrowDown className="w-5 h-5" />}
          divider
        />
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("request.payer") || "Mlipaji (namba ya simu au barua pepe)"}
              </label>
              <input
                type="text"
                value={payer}
                onChange={(e) => setPayer(e.target.value)}
                placeholder="+255XXXXXXXXX au email@mfano.com"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("request.amount") || "Kiasi"}
              </label>
              <input
                type="number"
                min="1"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("request.note") || "Ujumbe (hiari)"}
              </label>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={2}
                maxLength={255}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
              />
            </div>
            <Button type="submit" disabled={submitting} className="w-full bg-purple-600 hover:bg-purple-700">
              {submitting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <ArrowDown className="w-4 h-4 mr-2" />
              )}
              {submitting ? t("request.sending") || "Inatuma..." : t("request.submit") || "Tuma Ombi"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader title={t("request.incoming") || "Maombi Uliyopokea"} divider />
        <CardContent>
          {loadingList ? (
            <Loader2 className="w-5 h-5 animate-spin mx-auto text-gray-400" />
          ) : incoming.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("request.no_incoming") || "Hakuna maombi uliyopokea."}
            </p>
          ) : (
            incoming.map((r) => renderRequestRow(r, true))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader title={t("request.outgoing") || "Maombi Uliyotuma"} divider />
        <CardContent>
          {loadingList ? (
            <Loader2 className="w-5 h-5 animate-spin mx-auto text-gray-400" />
          ) : outgoing.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("request.no_outgoing") || "Hujatuma ombi lolote."}
            </p>
          ) : (
            outgoing.map((r) => renderRequestRow(r, false))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
