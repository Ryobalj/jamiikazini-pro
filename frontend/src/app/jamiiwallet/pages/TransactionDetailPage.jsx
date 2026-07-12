// src/app/jamiiwallet/pages/TransactionDetailPage.jsx

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import api from "@/lib/axios";
import {
  ArrowLeft,
  Loader2,
  ArrowDownCircle,
  ArrowUpCircle,
  Copy,
} from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useCurrency } from "@/context/CurrencyContext";

const STATUS_STYLES = {
  PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  COMPLETED: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  FAILED: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  REVERSED: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
};

export default function TransactionDetailPage() {
  const { t } = useTranslation("jamiiwallet");
  const navigate = useNavigate();
  const { id } = useParams();
  const { formatCurrency } = useCurrency();

  const [txn, setTxn] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    api
      .get(`/jamiiwallet/transactions/${id}/`)
      .then((res) => setTxn(res.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [id]);

  const copyReference = () => {
    if (txn?.reference) {
      navigator.clipboard.writeText(txn.reference);
      toast.success(t("transactions.reference_copied") || "Reference imenakiliwa.");
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error || !txn) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <p className="text-center text-gray-500 dark:text-gray-400">
          {t("transactions.not_found") || "Muamala haukupatikana."}
        </p>
      </div>
    );
  }

  const isIn = txn.direction === "in";
  const Icon = isIn ? ArrowDownCircle : ArrowUpCircle;

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <button
        onClick={() => navigate("/jamiiwallet/transactions")}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        {t("back") || "Rudi"}
      </button>

      <Card>
        <CardContent className="pt-6 text-center">
          <Icon className={`w-14 h-14 mx-auto mb-3 ${isIn ? "text-green-500" : "text-red-500"}`} />
          <p
            className={`text-3xl font-bold ${
              isIn ? "text-green-600 dark:text-green-400" : "text-gray-900 dark:text-white"
            }`}
          >
            {isIn ? "+" : "-"}
            {formatCurrency(txn.amount)}
          </p>
          <span
            className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-medium ${
              STATUS_STYLES[txn.status] || STATUS_STYLES.PENDING
            }`}
          >
            {txn.status}
          </span>
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader title={t("transactions.details") || "Maelezo"} divider />
        <CardContent className="space-y-3">
          <Row label={t("transactions.type") || "Aina"} value={txn.transaction_type} />
          {txn.counterparty_name && (
            <Row
              label={isIn ? (t("transactions.from") || "Kutoka") : (t("transactions.to") || "Kwenda")}
              value={txn.counterparty_name}
            />
          )}
          <Row
            label={t("transactions.reference") || "Reference"}
            value={
              <button onClick={copyReference} className="flex items-center gap-1 hover:text-purple-600">
                {txn.reference} <Copy className="w-3.5 h-3.5" />
              </button>
            }
          />
          <Row label={t("transactions.date") || "Tarehe"} value={new Date(txn.created_at).toLocaleString()} />
          {txn.metadata?.note && (
            <Row label={t("transactions.note") || "Ujumbe"} value={txn.metadata.note} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
      <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
      <span className="text-sm font-medium text-gray-900 dark:text-white">{value}</span>
    </div>
  );
}
