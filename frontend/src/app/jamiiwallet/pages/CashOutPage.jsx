// src/app/jamiiwallet/pages/CashOutPage.jsx

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import { Banknote, ArrowLeft, Loader2, ShieldCheck, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useCurrency } from "@/context/CurrencyContext";

export default function CashOutPage() {
  const { t } = useTranslation("jamiiwallet");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();

  const [balance, setBalance] = useState(null);
  const [loadingWallet, setLoadingWallet] = useState(true);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedBusiness, setSelectedBusiness] = useState(null);
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

  useEffect(() => {
    if (selectedBusiness || query.trim().length < 2) {
      setResults([]);
      return;
    }
    setSearching(true);
    const handle = setTimeout(() => {
      api
        .get("/businesses/", { params: { search: query.trim() } })
        .then((res) => {
          const data = Array.isArray(res.data) ? res.data : res.data?.results || [];
          setResults(data.filter((b) => b.is_verified));
        })
        .catch(() => setResults([]))
        .finally(() => setSearching(false));
    }, 350);
    return () => clearTimeout(handle);
  }, [query, selectedBusiness]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedBusiness) {
      toast.error(t("cashout.errors.business_required") || "Chagua biashara utakayotolea fedha.");
      return;
    }
    const numericAmount = parseFloat(amount);
    if (!numericAmount || numericAmount <= 0) {
      toast.error(t("send.errors.amount_required") || "Weka kiasi sahihi.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.post("/jamiiwallet/cash-out/", {
        business_id: selectedBusiness.id,
        amount: numericAmount,
        note: note.trim(),
      });
      toast.success(
        t("cashout.success", { name: res.data?.business_name }) ||
          `Umetoa fedha kupitia ${res.data?.business_name || "biashara"} kikamilifu.`
      );
      navigate("/jamiiwallet");
    } catch (error) {
      const errors = error.response?.data?.errors || error.response?.data;
      const firstError =
        (errors && typeof errors === "object" && Object.values(errors)[0]) ||
        error.response?.data?.detail;
      toast.error(
        (Array.isArray(firstError) ? firstError[0] : firstError) ||
          t("cashout.errors.failed") ||
          "Imeshindwa kutoa fedha. Jaribu tena."
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
          title={t("cashout.title") || "Toa Fedha Taslimu"}
          subtitle={
            !loadingWallet && balance !== null
              ? `${t("send.available_balance") || "Salio lililopo"}: ${formatCurrency(balance)}`
              : undefined
          }
          icon={<Banknote className="w-5 h-5" />}
          divider
        />
        <CardContent>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
            {t("cashout.description") ||
              "Tembelea biashara yoyote iliyothibitishwa ndani ya JamiiKazini upewe fedha taslimu - hakuna ada kwa sasa."}
          </p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("cashout.business_label") || "Tafuta Biashara"}
              </label>
              {selectedBusiness ? (
                <div className="flex items-center justify-between p-2.5 border border-blue-600 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm">
                  <span className="flex items-center gap-1.5 text-blue-700 dark:text-blue-400">
                    <ShieldCheck className="w-4 h-4" /> {selectedBusiness.name}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedBusiness(null);
                      setQuery("");
                    }}
                    className="text-xs text-gray-500 hover:text-red-500"
                  >
                    {t("cashout.change") || "Badilisha"}
                  </button>
                </div>
              ) : (
                <>
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder={t("cashout.business_placeholder") || "Andika jina la biashara..."}
                      className="w-full pl-9 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>
                  {searching && (
                    <div className="flex items-center gap-2 text-xs text-gray-400 mt-1.5">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" /> {t("cashout.searching") || "Inatafuta..."}
                    </div>
                  )}
                  {results.length > 0 && (
                    <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
                      {results.map((b) => (
                        <button
                          key={b.id}
                          type="button"
                          onClick={() => setSelectedBusiness(b)}
                          className="w-full flex items-center justify-between text-left p-2 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
                        >
                          <span className="text-gray-700 dark:text-gray-300">{b.name}</span>
                          <ShieldCheck className="w-3.5 h-3.5 text-green-500" />
                        </button>
                      ))}
                    </div>
                  )}
                </>
              )}
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
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
              />
            </div>

            <Button type="submit" disabled={submitting} className="w-full bg-purple-600 hover:bg-purple-700">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Banknote className="w-4 h-4 mr-2" />}
              {submitting ? t("cashout.submitting") || "Inatuma..." : t("cashout.submit") || "Toa Fedha"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
