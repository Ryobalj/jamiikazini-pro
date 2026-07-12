// src/app/jamiiwallet/pages/TransactionsListPage.jsx

import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import {
  ArrowLeft,
  Loader2,
  ArrowDownCircle,
  ArrowUpCircle,
  ChevronRight,
} from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useCurrency } from "@/context/CurrencyContext";

const TYPE_LABELS = {
  TOP_UP: "topup",
  WITHDRAWAL: "withdraw",
  TRANSFER: "transfer",
  PAYMENT: "payment",
  REFUND: "refund",
};

const STATUS_STYLES = {
  PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  COMPLETED: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  FAILED: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  REVERSED: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
};

const FILTERS = [
  { value: "", label: "all" },
  { value: "TOP_UP", label: "topup" },
  { value: "WITHDRAWAL", label: "withdraw" },
  { value: "TRANSFER", label: "transfer" },
];

export default function TransactionsListPage() {
  const { t } = useTranslation("jamiiwallet");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();

  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  const fetchTransactions = useCallback((type) => {
    setLoading(true);
    const params = type ? { transaction_type: type } : {};
    api
      .get("/jamiiwallet/transactions/", { params })
      .then((res) => setTransactions(res.data?.results || res.data || []))
      .catch(() => setTransactions([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchTransactions(filter);
  }, [filter, fetchTransactions]);

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
        <CardHeader title={t("transactions.title") || "Miamala Yote"} divider />
        <CardContent>
          <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
            {FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setFilter(f.value)}
                className={`px-3 py-1.5 rounded-full text-sm whitespace-nowrap transition-colors ${
                  filter === f.value
                    ? "bg-purple-600 text-white"
                    : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
                }`}
              >
                {t(`transactions.filters.${f.label}`) || f.label}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : transactions.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
              {t("transactions.empty") || "Hakuna miamala bado."}
            </p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {transactions.map((txn) => {
                const isIn = txn.direction === "in";
                const Icon = isIn ? ArrowDownCircle : ArrowUpCircle;
                return (
                  <button
                    key={txn.id}
                    onClick={() => navigate(`/jamiiwallet/transactions/${txn.id}`)}
                    className="w-full flex items-center justify-between py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 -mx-2 px-2 rounded-lg transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Icon
                        className={`w-8 h-8 ${
                          isIn ? "text-green-500" : "text-red-500"
                        }`}
                      />
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {txn.counterparty_name ||
                            t(`transactions.types.${TYPE_LABELS[txn.transaction_type] || "other"}`) ||
                            txn.transaction_type}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(txn.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-right">
                        <p
                          className={`font-semibold ${
                            isIn ? "text-green-600 dark:text-green-400" : "text-gray-900 dark:text-white"
                          }`}
                        >
                          {isIn ? "+" : "-"}
                          {formatCurrency(txn.amount)}
                        </p>
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-medium ${
                            STATUS_STYLES[txn.status] || STATUS_STYLES.PENDING
                          }`}
                        >
                          {txn.status}
                        </span>
                      </div>
                      <ChevronRight className="w-4 h-4 text-gray-400" />
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
