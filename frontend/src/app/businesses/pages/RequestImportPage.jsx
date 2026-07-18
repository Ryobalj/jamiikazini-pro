// src/app/businesses/pages/RequestImportPage.jsx
//
// Buyer-facing form ya kuomba bidhaa iagizwe kutoka nje (import sourcing) -
// ombi linaonekana kwa biashara zote zenye deals_in_imports=True, na
// inayodai (claim) inatoa bei na makadirio ya siku. Chini ya form kuna
// orodha ya maombi ya mtumiaji na majibu yake.

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Globe, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";
import { useCurrencies } from "@/hooks/useCurrencies";

const STATUS_STYLES = {
  PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  CLAIMED: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  FULFILLED: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  EXPIRED: "bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400",
  CANCELLED: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
};

export default function RequestImportPage() {
  const { t } = useTranslation("businesses");
  const { formatCurrency } = useCurrency();

  const { currencies } = useCurrencies();

  const [description, setDescription] = useState("");
  const [originCountry, setOriginCountry] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [budgetAmount, setBudgetAmount] = useState("");
  const [budgetCurrency, setBudgetCurrency] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [myRequests, setMyRequests] = useState([]);
  const [loadingRequests, setLoadingRequests] = useState(true);

  const fetchMyRequests = () => {
    setLoadingRequests(true);
    api
      .get("/import-requests/")
      .then((res) => setMyRequests(res.data?.results || res.data || []))
      .catch(() => setMyRequests([]))
      .finally(() => setLoadingRequests(false));
  };

  useEffect(() => {
    fetchMyRequests();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!description.trim()) return;
    setSubmitting(true);
    try {
      await api.post("/import-requests/", {
        item_description: description.trim(),
        origin_country: originCountry.trim(),
        quantity,
        budget_amount: budgetAmount || undefined,
        budget_currency_code: budgetAmount ? budgetCurrency || undefined : undefined,
      });
      toast.success(t("import_requests.request_sent", "Ombi lako la uagizaji limetumwa kwa waagizaji."));
      setDescription("");
      setOriginCountry("");
      setQuantity(1);
      setBudgetAmount("");
      fetchMyRequests();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("import_requests.request_failed", "Imeshindwa kutuma ombi. Jaribu tena."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto p-4 sm:p-6 space-y-5">
      <div className="flex items-center gap-2">
        <Globe className="w-6 h-6 text-blue-600" />
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t("import_requests.title", "Agiza Bidhaa Kutoka Nje")}
        </h1>
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        {t("import_requests.subtitle", "Eleza bidhaa unayotaka iagizwe - wafanyabiashara waagizaji watakupa bei na makadirio ya muda.")}
      </p>

      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("import_requests.description_label", "Maelezo ya Bidhaa")}
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                required
                placeholder={t("import_requests.description_placeholder", "Mfano: Simu za mkononi aina ya X, spesifikesheni...")}
                className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("import_requests.origin_label", "Nchi ya Asili (hiari)")}
              </label>
              <input
                type="text"
                value={originCountry}
                onChange={(e) => setOriginCountry(e.target.value)}
                placeholder={t("import_requests.origin_placeholder", "Mfano: China, Dubai, Uturuki")}
                className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t("import_requests.quantity_label", "Kiasi")}
                </label>
                <input
                  type="number"
                  min="1"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t("import_requests.budget_label", "Bajeti (hiari)")}
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={budgetAmount}
                  onChange={(e) => setBudgetAmount(e.target.value)}
                  className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t("import_requests.currency_label", "Sarafu")}
                </label>
                <select
                  value={budgetCurrency}
                  onChange={(e) => setBudgetCurrency(e.target.value)}
                  className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <option value="">TZS</option>
                  {currencies.map((c) => (
                    <option key={c.code} value={c.code}>{c.code}</option>
                  ))}
                </select>
              </div>
            </div>
            <Button type="submit" disabled={submitting || !description.trim()} className="w-full">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : t("import_requests.submit", "Tuma Ombi la Uagizaji")}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t("import_requests.my_requests", "Maombi Yangu ya Uagizaji")}
        </h2>
        {loadingRequests ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : myRequests.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
            {t("import_requests.no_requests", "Hujawahi kutuma ombi la uagizaji bado.")}
          </p>
        ) : (
          myRequests.map((req) => (
            <Card key={req.id}>
              <CardContent className="p-4 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium text-gray-900 dark:text-white line-clamp-2">{req.item_description}</p>
                  <span className={`shrink-0 inline-block px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_STYLES[req.status] || STATUS_STYLES.PENDING}`}>
                    {t(`import_requests.status_${req.status?.toLowerCase()}`, req.status)}
                  </span>
                </div>
                {req.origin_country && (
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {t("import_requests.origin_label", "Nchi ya Asili (hiari)")}: {req.origin_country}
                  </p>
                )}
                {req.status === "CLAIMED" && (
                  <div className="text-sm bg-green-50 dark:bg-green-900/20 rounded-lg p-2 space-y-1">
                    <p className="text-gray-700 dark:text-gray-300">
                      {t("import_requests.claimed_by", "Imedaiwa na")}: <span className="font-medium">{req.claimed_by_business_name}</span>
                    </p>
                    <p className="text-gray-700 dark:text-gray-300">
                      {t("import_requests.quoted_price", "Bei iliyotolewa")}: <span className="font-semibold">{formatCurrency(req.claimed_price)}</span>
                    </p>
                    <p className="text-gray-700 dark:text-gray-300">
                      {t("import_requests.lead_days", "Makadirio ya siku")}: {req.estimated_lead_days}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
