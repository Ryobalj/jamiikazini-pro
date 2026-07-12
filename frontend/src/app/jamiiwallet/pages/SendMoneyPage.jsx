// src/app/jamiiwallet/pages/SendMoneyPage.jsx

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";
import api from "@/lib/axios";
import { Send, ArrowLeft, Loader2, Wallet as WalletIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useCurrency } from "@/context/CurrencyContext";

export default function SendMoneyPage() {
  const { t } = useTranslation("jamiiwallet");
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { formatCurrency } = useCurrency();

  const [balance, setBalance] = useState(null);
  const [loadingWallet, setLoadingWallet] = useState(true);
  const [recipient, setRecipient] = useState(searchParams.get("recipient") || "");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api
      .get("/jamiiwallet/wallet/")
      .then((res) => setBalance(res.data?.balance ?? 0))
      .catch(() => setBalance(null))
      .finally(() => setLoadingWallet(false));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!recipient.trim()) {
      toast.error(t("send.errors.recipient_required") || "Weka namba ya simu au barua pepe ya mpokeaji.");
      return;
    }
    const numericAmount = parseFloat(amount);
    if (!numericAmount || numericAmount <= 0) {
      toast.error(t("send.errors.amount_required") || "Weka kiasi sahihi.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.post("/jamiiwallet/transfer/", {
        recipient_identifier: recipient.trim(),
        amount: numericAmount,
        note: note.trim(),
      });
      toast.success(
        t("send.success", { name: res.data?.recipient_name }) ||
          `Umetuma pesa kwa ${res.data?.recipient_name || "mpokeaji"} kikamilifu.`
      );
      navigate("/jamiiwallet");
    } catch (error) {
      const errors = error.response?.data?.errors || error.response?.data;
      const firstError =
        (errors && typeof errors === "object" && Object.values(errors)[0]) ||
        error.response?.data?.detail;
      toast.error(
        (Array.isArray(firstError) ? firstError[0] : firstError) ||
          t("send.errors.failed") ||
          "Imeshindwa kutuma pesa. Jaribu tena."
      );
    } finally {
      setSubmitting(false);
    }
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

      <Card>
        <CardHeader
          title={t("send.title") || "Tuma Pesa"}
          subtitle={
            !loadingWallet && balance !== null
              ? `${t("send.available_balance") || "Salio lililopo"}: ${formatCurrency(balance)}`
              : undefined
          }
          icon={<Send className="w-5 h-5" />}
          divider
        />
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("send.recipient") || "Mpokeaji (namba ya simu au barua pepe)"}
              </label>
              <input
                type="text"
                value={recipient}
                onChange={(e) => setRecipient(e.target.value)}
                placeholder="+255XXXXXXXXX au email@mfano.com"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("send.amount") || "Kiasi"}
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
                {t("send.note") || "Ujumbe (hiari)"}
              </label>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={2}
                maxLength={255}
                placeholder={t("send.note_placeholder") || "Mfano: malipo ya chakula"}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
              />
            </div>

            <Button
              type="submit"
              disabled={submitting}
              className="w-full bg-purple-600 hover:bg-purple-700"
            >
              {submitting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Send className="w-4 h-4 mr-2" />
              )}
              {submitting ? t("send.sending") || "Inatuma..." : t("send.submit") || "Tuma Pesa"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
