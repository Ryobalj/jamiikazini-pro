// src/app/jamiiwallet/pages/AccountsPage.jsx

import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import {
  ArrowLeft,
  Loader2,
  TrendingUp,
  TrendingDown,
  PlusCircle,
  PiggyBank,
  Wallet as WalletIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useCurrency } from "@/context/CurrencyContext";

const CATEGORIES = [
  { value: "FOOD", label: "Chakula" },
  { value: "TRANSPORT", label: "Usafiri" },
  { value: "RENT", label: "Kodi ya Nyumba/Ofisi" },
  { value: "UTILITIES", label: "Umeme/Maji/Mtandao" },
  { value: "SUPPLIES", label: "Malighafi/Vifaa" },
  { value: "SALARIES", label: "Mishahara" },
  { value: "TAX", label: "Kodi ya Serikali" },
  { value: "HEALTH", label: "Afya" },
  { value: "EDUCATION", label: "Elimu" },
  { value: "OTHER", label: "Nyingine" },
];

const PERIODS = [
  { value: "WEEKLY", label: "Kila Wiki" },
  { value: "MONTHLY", label: "Kila Mwezi" },
  { value: "YEARLY", label: "Kila Mwaka" },
];

export default function AccountsPage() {
  const { t } = useTranslation("jamiiwallet");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();

  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  const [expenseAmount, setExpenseAmount] = useState("");
  const [expenseCategory, setExpenseCategory] = useState("FOOD");
  const [expenseNote, setExpenseNote] = useState("");
  const [savingExpense, setSavingExpense] = useState(false);

  const [budgetAmount, setBudgetAmount] = useState("");
  const [budgetCategory, setBudgetCategory] = useState("");
  const [budgetPeriod, setBudgetPeriod] = useState("MONTHLY");
  const [savingBudget, setSavingBudget] = useState(false);

  const fetchSummary = useCallback(() => {
    setLoading(true);
    api
      .get("/jamiiwallet/wallet/summary/")
      .then((res) => setSummary(res.data))
      .catch(() => setSummary(null))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  const handleAddExpense = async (e) => {
    e.preventDefault();
    const amount = parseFloat(expenseAmount);
    if (!amount || amount <= 0) {
      toast.error(t("accounts.errors.amount_required") || "Weka kiasi sahihi.");
      return;
    }
    setSavingExpense(true);
    try {
      await api.post("/jamiiwallet/expenses/", {
        amount,
        category: expenseCategory,
        note: expenseNote.trim(),
      });
      toast.success(t("accounts.expense_added") || "Gharama imeandikwa.");
      setExpenseAmount("");
      setExpenseNote("");
      fetchSummary();
    } catch (error) {
      toast.error(error.response?.data?.detail || t("accounts.errors.failed") || "Imeshindwa.");
    } finally {
      setSavingExpense(false);
    }
  };

  const handleAddBudget = async (e) => {
    e.preventDefault();
    const amount = parseFloat(budgetAmount);
    if (!amount || amount <= 0) {
      toast.error(t("accounts.errors.amount_required") || "Weka kiasi sahihi.");
      return;
    }
    setSavingBudget(true);
    try {
      await api.post("/jamiiwallet/budgets/", {
        amount,
        category: budgetCategory || null,
        period: budgetPeriod,
      });
      toast.success(t("accounts.budget_added") || "Bajeti imewekwa.");
      setBudgetAmount("");
      fetchSummary();
    } catch (error) {
      toast.error(error.response?.data?.detail || t("accounts.errors.failed") || "Imeshindwa.");
    } finally {
      setSavingBudget(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <button
        onClick={() => navigate("/jamiiwallet")}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
      >
        <ArrowLeft className="w-4 h-4" />
        {t("back") || "Rudi"}
      </button>

      <Card>
        <CardHeader title={t("accounts.title") || "Hesabu Zangu"} icon={<WalletIcon className="w-5 h-5" />} divider />
        <CardContent>
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin mx-auto text-gray-400" />
          ) : summary ? (
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-green-500" />
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{t("accounts.income") || "Mapato"}</p>
                  <p className="font-semibold text-green-600 dark:text-green-400">
                    {formatCurrency(summary.total_income)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <TrendingDown className="w-6 h-6 text-red-500" />
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{t("accounts.expense") || "Matumizi"}</p>
                  <p className="font-semibold text-red-600 dark:text-red-400">
                    {formatCurrency(summary.total_expense)}
                  </p>
                </div>
              </div>
              <div className="col-span-2 pt-3 border-t border-gray-100 dark:border-gray-700">
                <p className="text-xs text-gray-500 dark:text-gray-400">{t("accounts.net") || "Salio la Hesabu"}</p>
                <p
                  className={`font-bold text-lg ${
                    summary.net >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {formatCurrency(summary.net)}
                </p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("accounts.load_failed") || "Imeshindwa kupakia hesabu."}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader title={t("accounts.add_expense") || "Andika Gharama"} icon={<TrendingDown className="w-5 h-5" />} divider />
        <CardContent>
          <form onSubmit={handleAddExpense} className="space-y-3">
            <input
              type="number"
              min="1"
              step="0.01"
              value={expenseAmount}
              onChange={(e) => setExpenseAmount(e.target.value)}
              placeholder={t("accounts.amount") || "Kiasi"}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            />
            <select
              value={expenseCategory}
              onChange={(e) => setExpenseCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
            <input
              type="text"
              value={expenseNote}
              onChange={(e) => setExpenseNote(e.target.value)}
              placeholder={t("accounts.note") || "Ujumbe (hiari)"}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            />
            <Button type="submit" disabled={savingExpense} className="bg-purple-600 hover:bg-purple-700">
              {savingExpense ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <PlusCircle className="w-4 h-4 mr-2" />}
              {t("accounts.save") || "Hifadhi"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader title={t("accounts.budgets") || "Bajeti Zangu"} icon={<PiggyBank className="w-5 h-5" />} divider />
        <CardContent className="space-y-4">
          <form onSubmit={handleAddBudget} className="space-y-3">
            <input
              type="number"
              min="1"
              step="0.01"
              value={budgetAmount}
              onChange={(e) => setBudgetAmount(e.target.value)}
              placeholder={t("accounts.budget_amount") || "Kiwango cha juu"}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            />
            <select
              value={budgetCategory}
              onChange={(e) => setBudgetCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            >
              <option value="">{t("accounts.all_categories") || "Makundi Yote"}</option>
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
            <select
              value={budgetPeriod}
              onChange={(e) => setBudgetPeriod(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            >
              {PERIODS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
            <Button type="submit" disabled={savingBudget} className="bg-purple-600 hover:bg-purple-700">
              {savingBudget ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <PlusCircle className="w-4 h-4 mr-2" />}
              {t("accounts.set_budget") || "Weka Bajeti"}
            </Button>
          </form>

          {summary?.budgets?.length > 0 && (
            <div className="divide-y divide-gray-100 dark:divide-gray-700 pt-2">
              {summary.budgets.map((b) => {
                const pct = Math.min(100, (b.spent_amount / b.amount) * 100 || 0);
                return (
                  <div key={b.id} className="py-3">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-700 dark:text-gray-300">
                        {b.category_display || t("accounts.all_categories") || "Makundi Yote"}
                      </span>
                      <span className={b.is_over_budget ? "text-red-500 font-medium" : "text-gray-500 dark:text-gray-400"}>
                        {formatCurrency(b.spent_amount)} / {formatCurrency(b.amount)}
                      </span>
                    </div>
                    <div className="w-full h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${b.is_over_budget ? "bg-red-500" : "bg-purple-600"}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
