// src/app/businesses/pages/IncomingImportRequests.jsx
//
// Business-dashboard tab: maombi ya uagizaji (import requests) kutoka kwa
// wanunuzi - biashara yenye deals_in_imports=True inadai (claim) kwa kutoa
// bei na makadirio ya siku za kusubiri.

import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Globe, Loader2, PackageCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useCurrencies } from "@/hooks/useCurrencies";

export default function IncomingImportRequests() {
  const { t } = useTranslation("businesses");
  const { id: businessId } = useParams();
  const { currencies } = useCurrencies();

  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [claimingId, setClaimingId] = useState(null);
  // Per-request claim form values: { [requestId]: { price, currency, leadDays } }
  const [claimForms, setClaimForms] = useState({});

  const fetchIncoming = () => {
    setLoading(true);
    api
      .get("/import-requests/incoming/")
      .then((res) => setRequests(res.data || []))
      .catch(() => setRequests([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchIncoming();
    const interval = setInterval(fetchIncoming, 15000);
    return () => clearInterval(interval);
  }, []);

  const setFormValue = (requestId, field, value) => {
    setClaimForms((prev) => ({
      ...prev,
      [requestId]: { ...prev[requestId], [field]: value },
    }));
  };

  const handleClaim = async (requestId) => {
    const form = claimForms[requestId] || {};
    if (!form.price || Number(form.price) <= 0) {
      toast.error(t("import_requests.price_required", "Weka bei unayotoa."));
      return;
    }
    if (!form.leadDays || Number(form.leadDays) <= 0) {
      toast.error(t("import_requests.lead_days_required", "Weka makadirio ya siku."));
      return;
    }
    setClaimingId(requestId);
    try {
      await api.post(`/import-requests/${requestId}/claim/`, {
        business_id: businessId,
        price: form.price,
        currency_code: form.currency || undefined,
        estimated_lead_days: form.leadDays,
      });
      toast.success(t("import_requests.claim_success", "Umedai ombi hili - mnunuzi ataona bei yako."));
      fetchIncoming();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("import_requests.claim_failed", "Imeshindwa kudai ombi hili."));
    } finally {
      setClaimingId(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Globe className="w-5 h-5 text-blue-600" />
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t("import_requests.incoming_heading", "Maombi ya Uagizaji")}
        </h2>
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        {t("import_requests.incoming_description", "Wanunuzi wanatafuta waagizaji - toa bei na makadirio ya siku ili kudai ombi.")}
      </p>

      {loading ? (
        <div className="flex justify-center py-10">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        </div>
      ) : requests.length === 0 ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">
          <PackageCheck className="w-10 h-10 mx-auto mb-2" />
          <p>{t("import_requests.incoming_empty", "Hakuna maombi ya uagizaji kwa sasa.")}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {requests.map((req) => {
            const form = claimForms[req.id] || {};
            return (
              <Card key={req.id}>
                <CardContent className="p-4 space-y-3">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {req.item_description} <span className="text-gray-400">×{req.quantity}</span>
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {t("import_requests.buyer_label", "Mnunuzi")}: {req.buyer_name}
                    </p>
                    {req.origin_country && (
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {t("import_requests.origin_short", "Nchi ya asili")}: {req.origin_country}
                      </p>
                    )}
                    {req.budget_amount && (
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {t("import_requests.budget_short", "Bajeti")}: {req.budget_amount} {req.budget_currency_code || "TZS"}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={form.price || ""}
                      onChange={(e) => setFormValue(req.id, "price", e.target.value)}
                      placeholder={t("import_requests.price_placeholder", "Bei unayotoa")}
                      className="w-32 p-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                    />
                    <select
                      value={form.currency || ""}
                      onChange={(e) => setFormValue(req.id, "currency", e.target.value)}
                      className="p-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                    >
                      <option value="">TZS</option>
                      {currencies.map((c) => (
                        <option key={c.code} value={c.code}>{c.code}</option>
                      ))}
                    </select>
                    <input
                      type="number"
                      min="1"
                      max="365"
                      value={form.leadDays || ""}
                      onChange={(e) => setFormValue(req.id, "leadDays", e.target.value)}
                      placeholder={t("import_requests.lead_days_placeholder", "Siku")}
                      className="w-20 p-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                    />
                    <Button
                      size="sm"
                      disabled={claimingId === req.id}
                      onClick={() => handleClaim(req.id)}
                    >
                      {claimingId === req.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("import_requests.claim", "Dai Ombi")}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
