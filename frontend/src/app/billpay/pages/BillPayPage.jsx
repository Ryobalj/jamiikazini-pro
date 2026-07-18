// src/app/billpay/pages/BillPayPage.jsx

import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import { Zap, Smartphone, Tv, Droplet, ArrowLeft, Loader2, CheckCircle2, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useCurrency } from "@/context/CurrencyContext";

const CATEGORY_ICONS = {
  ELECTRICITY: Zap,
  AIRTIME: Smartphone,
  TV: Tv,
  WATER: Droplet,
};

export default function BillPayPage() {
  const { t } = useTranslation("billpay");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();

  const [balance, setBalance] = useState(null);
  const [loadingWallet, setLoadingWallet] = useState(true);
  const [billers, setBillers] = useState([]);
  const [loadingBillers, setLoadingBillers] = useState(true);

  const [category, setCategory] = useState(null);
  const [billerId, setBillerId] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [amount, setAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api
      .get("/jamiiwallet/wallet/")
      .then((res) => setBalance(res.data?.balance ?? 0))
      .catch(() => setBalance(null))
      .finally(() => setLoadingWallet(false));

    api
      .get("/billpay/billers/")
      .then((res) => setBillers(Array.isArray(res.data) ? res.data : res.data?.results || []))
      .catch(() => setBillers([]))
      .finally(() => setLoadingBillers(false));
  }, []);

  const categories = useMemo(() => {
    const seen = new Set();
    return billers
      .map((b) => b.category)
      .filter((c) => (seen.has(c) ? false : seen.add(c)));
  }, [billers]);

  const billersInCategory = useMemo(
    () => billers.filter((b) => b.category === category),
    [billers, category]
  );

  const handleReset = () => {
    setCategory(null);
    setBillerId("");
    setAccountNumber("");
    setAmount("");
    setResult(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!billerId) {
      toast.error(t("errors.biller_required", "Chagua huduma unayotaka kulipia."));
      return;
    }
    if (!accountNumber.trim()) {
      toast.error(t("errors.account_required", "Weka namba ya mita/simu/akaunti."));
      return;
    }
    const numericAmount = parseFloat(amount);
    if (!numericAmount || numericAmount <= 0) {
      toast.error(t("errors.amount_required", "Weka kiasi sahihi."));
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.post("/billpay/payments/", {
        biller: billerId,
        account_number: accountNumber.trim(),
        amount: numericAmount,
      });
      setResult(res.data);
      setBalance((prev) => (prev !== null ? prev - numericAmount : prev));
      toast.success(t("success", "Malipo yamekamilika!"));
    } catch (error) {
      const detail = error.response?.data?.detail || error.response?.data?.account_number?.[0];
      toast.error(typeof detail === "string" ? detail : t("errors.failed", "Malipo yameshindwa. Jaribu tena."));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopy = (value) => {
    navigator.clipboard?.writeText(value);
    toast.success(t("copied", "Imenakiliwa."));
  };

  if (result) {
    return (
      <div className="max-w-lg mx-auto px-4 sm:px-6 py-6">
        <Card>
          <CardContent className="p-6 text-center space-y-4">
            <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto" />
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              {t("success", "Malipo yamekamilika!")}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("paid_to", "Umelipa")} {result.biller_name} - {formatCurrency(result.amount)}
            </p>
            {result.token_or_receipt && (
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  {t("token_label", "Namba ya Tokeni")}
                </p>
                <div className="flex items-center justify-center gap-2">
                  <code className="text-lg font-mono font-semibold text-gray-900 dark:text-white">
                    {result.token_or_receipt}
                  </code>
                  <button onClick={() => handleCopy(result.token_or_receipt)} className="text-gray-400 hover:text-gray-600">
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
            {result.external_reference && (
              <p className="text-xs text-gray-400">
                {t("reference_label", "Kumbukumbu")}: {result.external_reference}
              </p>
            )}
            <div className="flex gap-2 justify-center pt-2">
              <Button variant="secondary" onClick={handleReset}>
                {t("pay_another", "Lipia Huduma Nyingine")}
              </Button>
              <Button onClick={() => navigate("/jamiiwallet")}>
                {t("back_to_wallet", "Rudi kwenye Wallet")}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto px-4 sm:px-6 py-6">
      <button
        onClick={() => navigate("/jamiiwallet")}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        {t("back", "Rudi")}
      </button>

      <Card>
        <CardHeader
          title={t("title", "Malipo ya Huduma")}
          subtitle={
            !loadingWallet && balance !== null
              ? `${t("available_balance", "Salio lililopo")}: ${formatCurrency(balance)}`
              : undefined
          }
          icon={<Zap className="w-5 h-5" />}
          divider
        />
        <CardContent className="space-y-4">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {t("description", "Lipa LUKU, muda wa maongezi, DSTV, na huduma nyingine moja kwa moja kutoka JamiiWallet yako.")}
          </p>

          {loadingBillers ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
            </div>
          ) : (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t("category_label", "Chagua Aina ya Huduma")}
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {categories.map((cat) => {
                    const Icon = CATEGORY_ICONS[cat] || Zap;
                    return (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => {
                          setCategory(cat);
                          setBillerId("");
                        }}
                        className={`flex items-center gap-2 p-3 rounded-lg border text-sm ${
                          category === cat
                            ? "border-purple-600 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400"
                            : "border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300"
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                        {t(`category_${cat.toLowerCase()}`, cat)}
                      </button>
                    );
                  })}
                </div>
              </div>

              {category && (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      {t("biller_label", "Mtoa Huduma")}
                    </label>
                    <select
                      value={billerId}
                      onChange={(e) => setBillerId(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value="">{t("biller_placeholder", "Chagua...")}</option>
                      {billersInCategory.map((b) => (
                        <option key={b.id} value={b.id}>{b.name}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      {t("account_label", "Namba ya Mita/Simu/Akaunti")}
                    </label>
                    <input
                      type="text"
                      value={accountNumber}
                      onChange={(e) => setAccountNumber(e.target.value)}
                      placeholder={t("account_placeholder", "Andika namba...")}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      {t("amount_label", "Kiasi")}
                    </label>
                    <input
                      type="number"
                      min="1"
                      step="0.01"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      placeholder="0.00"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>

                  <Button type="submit" disabled={submitting || !billerId} className="w-full">
                    {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                    {submitting ? t("submitting", "Inalipa...") : t("submit", "Lipa Sasa")}
                  </Button>
                </form>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
