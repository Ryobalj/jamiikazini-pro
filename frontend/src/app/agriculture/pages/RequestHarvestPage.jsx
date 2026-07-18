// src/app/agriculture/pages/RequestHarvestPage.jsx
//
// Mnunuzi anaomba mkataba wa awali wa mazao (forward contract) - bei ya kila
// kilo inakubaliwa mapema, lakini malipo ya mwisho yanategemea uzito halisi
// utakaopimwa wakati wa kupokea (weight-at-delivery), si kiasi kilichokadiriwa.

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Wheat, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";

const STATUS_STYLES = {
  PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  ACCEPTED: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  SETTLED: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  DISPUTED: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  CANCELLED: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
};

export default function RequestHarvestPage() {
  const { t } = useTranslation("agriculture");
  const { formatCurrency } = useCurrency();

  const [cropDescription, setCropDescription] = useState("");
  const [estimatedWeight, setEstimatedWeight] = useState("");
  const [pricePerKg, setPricePerKg] = useState("");
  const [windowStart, setWindowStart] = useState("");
  const [windowEnd, setWindowEnd] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [contracts, setContracts] = useState([]);
  const [loadingContracts, setLoadingContracts] = useState(true);
  const [actingId, setActingId] = useState(null);
  const [deliveryInputs, setDeliveryInputs] = useState({});

  const fetchContracts = () => {
    setLoadingContracts(true);
    api
      .get("/agriculture/contracts/")
      .then((res) => setContracts(Array.isArray(res.data) ? res.data : res.data?.results || []))
      .catch(() => setContracts([]))
      .finally(() => setLoadingContracts(false));
  };

  useEffect(() => {
    fetchContracts();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!cropDescription.trim() || !estimatedWeight || !pricePerKg || !windowStart || !windowEnd) {
      toast.error(t("fill_all_fields", "Jaza taarifa zote."));
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/agriculture/contracts/", {
        crop_description: cropDescription.trim(),
        estimated_weight_kg: estimatedWeight,
        agreed_price_per_kg: pricePerKg,
        delivery_window_start: windowStart,
        delivery_window_end: windowEnd,
      });
      toast.success(t("contract_sent", "Mkataba wako umetumwa kwa wauzaji wa mazao."));
      setCropDescription(""); setEstimatedWeight(""); setPricePerKg(""); setWindowStart(""); setWindowEnd("");
      fetchContracts();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("contract_failed", "Imeshindwa kutuma mkataba."));
    } finally {
      setSubmitting(false);
    }
  };

  const runAction = async (id, action, payload, successMsg) => {
    setActingId(id);
    try {
      await api.post(`/agriculture/contracts/${id}/${action}/`, payload || {});
      toast.success(successMsg);
      fetchContracts();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("action_failed", "Imeshindwa. Jaribu tena."));
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-4 sm:p-6 space-y-5">
      <div className="flex items-center gap-2">
        <Wheat className="w-6 h-6 text-green-600" />
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t("title", "Mkataba wa Awali wa Mazao")}
        </h1>
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        {t("subtitle", "Kubaliana bei ya kila kilo mapema - malipo ya mwisho yatategemea uzito halisi utakaopimwa wakati wa kupokea.")}
      </p>

      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="text" value={cropDescription} onChange={(e) => setCropDescription(e.target.value)}
              placeholder={t("crop_placeholder", "Mfano: Mahindi, Mchele...")}
              className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
            />
            <div className="grid grid-cols-2 gap-3">
              <input
                type="number" min="0" step="0.001" value={estimatedWeight} onChange={(e) => setEstimatedWeight(e.target.value)}
                placeholder={t("estimated_weight_label", "Makadirio ya Uzito (kg)")}
                className="p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
              />
              <input
                type="number" min="0" step="0.01" value={pricePerKg} onChange={(e) => setPricePerKg(e.target.value)}
                placeholder={t("price_per_kg_label", "Bei kwa Kilo")}
                className="p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                  {t("window_start_label", "Kuanzia")}
                </label>
                <input
                  type="date" value={windowStart} onChange={(e) => setWindowStart(e.target.value)}
                  className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                  {t("window_end_label", "Hadi")}
                </label>
                <input
                  type="date" value={windowEnd} onChange={(e) => setWindowEnd(e.target.value)}
                  className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                />
              </div>
            </div>
            {estimatedWeight && pricePerKg && (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t("deposit_estimate", "Amana (30%) itakayoshikiliwa ukikubaliwa")}: {formatCurrency((Number(estimatedWeight) * Number(pricePerKg) * 0.3).toFixed(2))}
              </p>
            )}
            <Button type="submit" disabled={submitting} className="w-full">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {t("submit", "Tuma Mkataba")}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t("my_contracts", "Mikataba Yangu")}
        </h2>
        {loadingContracts ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-green-600" />
          </div>
        ) : contracts.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
            {t("no_contracts", "Hujawahi kutuma mkataba wa mazao bado.")}
          </p>
        ) : (
          contracts.map((c) => (
            <Card key={c.id}>
              <CardContent className="p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-gray-900 dark:text-white">{c.crop_description}</p>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_STYLES[c.status]}`}>
                    {t(`status_${c.status?.toLowerCase()}`, c.status)}
                  </span>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {c.estimated_weight_kg} kg × {formatCurrency(c.agreed_price_per_kg)}/kg ≈ {formatCurrency(c.estimated_total)}
                </p>
                {c.seller_name && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t("seller_label", "Muuzaji")}: {c.seller_name}
                  </p>
                )}

                {c.status === "PENDING" && (
                  <Button size="sm" variant="secondary" disabled={actingId === c.id} onClick={() => runAction(c.id, "cancel", null, t("cancelled_success", "Mkataba umeghairiwa."))}>
                    {t("cancel", "Ghairi")}
                  </Button>
                )}

                {c.status === "ACCEPTED" && (
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <input
                      type="number" min="0" step="0.001"
                      value={deliveryInputs[c.id] || ""}
                      onChange={(e) => setDeliveryInputs((prev) => ({ ...prev, [c.id]: e.target.value }))}
                      placeholder={t("delivered_weight_placeholder", "Uzito halisi (kg)")}
                      className="w-40 p-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                    />
                    <Button
                      size="sm"
                      disabled={actingId === c.id || !!c.buyer_confirmed_at}
                      onClick={() => runAction(
                        c.id, "confirm-delivery", { delivered_weight_kg: deliveryInputs[c.id] },
                        t("confirmed_success", "Umethibitisha uzito - inasubiri muuzaji.")
                      )}
                    >
                      {c.buyer_confirmed_at
                        ? t("already_confirmed", "Umeshathibitisha - Inasubiri Muuzaji")
                        : t("confirm_delivery", "Thibitisha Uzito Uliopokea")}
                    </Button>
                    <Button size="sm" variant="secondary" disabled={actingId === c.id} onClick={() => runAction(c.id, "cancel", null, t("cancelled_success", "Mkataba umeghairiwa - amana imerudishwa."))}>
                      {t("cancel", "Ghairi")}
                    </Button>
                  </div>
                )}

                {c.status === "DISPUTED" && (
                  <p className="text-xs text-red-500 dark:text-red-400">
                    {t("dispute_notice", "Uzito uliothibitishwa haulingani - fedha zimeshikiliwa mpaka utatuzi wa admin.")}
                  </p>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
