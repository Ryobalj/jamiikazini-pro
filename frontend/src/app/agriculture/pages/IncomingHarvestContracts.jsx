// src/app/agriculture/pages/IncomingHarvestContracts.jsx
//
// Business-dashboard tab: mikataba ya awali ya mazao (harvest contracts)
// kutoka kwa wanunuzi - biashara yenye deals_in_agriculture=True inadai
// (claim) na baadaye inathibitisha uzito halisi wakati wa kupokea.

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { Wheat, Loader2, PackageCheck } from "lucide-react";
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

export default function IncomingHarvestContracts() {
  const { t } = useTranslation("agriculture");
  const { id: businessId } = useParams();
  const { formatCurrency } = useCurrency();

  const [incoming, setIncoming] = useState([]);
  const [accepted, setAccepted] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState(null);
  const [deliveryInputs, setDeliveryInputs] = useState({});

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      api.get("/agriculture/contracts/incoming/").then((r) => r.data).catch(() => []),
      api.get("/agriculture/contracts/").then((r) => r.data?.results || r.data || []).catch(() => []),
    ]).then(([pending, mine]) => {
      setIncoming(pending);
      setAccepted(mine.filter((c) => c.status === "ACCEPTED" && c.seller_name));
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleClaim = async (contractId) => {
    setActingId(contractId);
    try {
      await api.post(`/agriculture/contracts/${contractId}/claim/`, { business_id: businessId });
      toast.success(t("claim_success", "Umedai mkataba huu - amana imeshikiliwa."));
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("claim_failed", "Imeshindwa kudai mkataba huu."));
    } finally {
      setActingId(null);
    }
  };

  const handleConfirmDelivery = async (contractId) => {
    const weight = deliveryInputs[contractId];
    if (!weight) {
      toast.error(t("delivered_weight_required", "Weka uzito halisi."));
      return;
    }
    setActingId(contractId);
    try {
      await api.post(`/agriculture/contracts/${contractId}/confirm-delivery/`, { delivered_weight_kg: weight });
      toast.success(t("confirmed_success", "Umethibitisha uzito - inasubiri mnunuzi."));
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("action_failed", "Imeshindwa. Jaribu tena."));
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Wheat className="w-5 h-5 text-green-600" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("incoming_heading", "Mikataba ya Mazao Inayopatikana")}
          </h2>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
          {t("incoming_description", "Wanunuzi wanatafuta wauzaji wa mazao - dai mkataba ili kuuza kwao.")}
        </p>

        {loading ? (
          <div className="flex justify-center py-10">
            <Loader2 className="w-6 h-6 animate-spin text-green-600" />
          </div>
        ) : incoming.length === 0 ? (
          <div className="text-center py-8 text-gray-400 dark:text-gray-500">
            <PackageCheck className="w-8 h-8 mx-auto mb-2" />
            <p>{t("incoming_empty", "Hakuna mikataba ya mazao kwa sasa.")}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {incoming.map((c) => (
              <Card key={c.id}>
                <CardContent className="p-4 space-y-2">
                  <p className="font-medium text-gray-900 dark:text-white">{c.crop_description}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{c.buyer_name}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {c.estimated_weight_kg} kg × {formatCurrency(c.agreed_price_per_kg)}/kg
                  </p>
                  <p className="text-xs text-gray-400">
                    {t("delivery_window_label", "Kipindi cha Kupokea")}: {c.delivery_window_start} - {c.delivery_window_end}
                  </p>
                  <Button size="sm" disabled={actingId === c.id} onClick={() => handleClaim(c.id)}>
                    {actingId === c.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("claim", "Dai Mkataba")}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
          {t("my_accepted_heading", "Mikataba Niliyodai")}
        </h2>
        {accepted.length === 0 ? (
          <p className="text-sm text-gray-400">{t("no_accepted", "Hakuna mikataba uliyodai bado.")}</p>
        ) : (
          <div className="space-y-3">
            {accepted.map((c) => (
              <Card key={c.id}>
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-gray-900 dark:text-white">{c.crop_description}</p>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_STYLES[c.status]}`}>
                      {t(`status_${c.status?.toLowerCase()}`, c.status)}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      type="number" min="0" step="0.001"
                      value={deliveryInputs[c.id] || ""}
                      onChange={(e) => setDeliveryInputs((prev) => ({ ...prev, [c.id]: e.target.value }))}
                      placeholder={t("delivered_weight_placeholder", "Uzito halisi (kg)")}
                      className="w-40 p-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                    />
                    <Button
                      size="sm"
                      disabled={actingId === c.id || !!c.seller_confirmed_at}
                      onClick={() => handleConfirmDelivery(c.id)}
                    >
                      {c.seller_confirmed_at
                        ? t("already_confirmed_seller", "Umeshathibitisha - Inasubiri Mnunuzi")
                        : t("confirm_delivery", "Thibitisha Uzito Uliopokea")}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
