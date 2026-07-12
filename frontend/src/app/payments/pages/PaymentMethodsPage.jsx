// src/app/payments/pages/PaymentMethodsPage.jsx

import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import api from "@/lib/axios";
import { CreditCard, Loader2, PlusCircle, Trash2, Star, Smartphone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";

const MNO_OPTIONS = [
  { value: "YAS", label: "Tigo / Yas" },
  { value: "AIRTEL", label: "Airtel Money" },
  { value: "HALOTEL", label: "HaloPesa" },
];

// NB: Kadi za malipo hazijengwi hapa kwa makusudi - tazama AddCardPage.jsx
// (Task #26: PaymentMethod inahitaji token ya gateway, si namba ya kadi moja
// kwa moja - PCI-DSS). Hapa tunaruhusu tu njia za PawaPay (simu+MNO), ambazo
// hazina hatari hiyo (si data nyeti ya kadi).
export default function PaymentMethodsPage() {
  const { t } = useTranslation("payments");

  const [methods, setMethods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mno, setMno] = useState("YAS");
  const [phone, setPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [busyId, setBusyId] = useState(null);

  const fetchMethods = useCallback(() => {
    setLoading(true);
    api
      .get("/payments/payment-methods/")
      .then((res) => setMethods(res.data?.results || res.data || []))
      .catch(() => setMethods([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchMethods();
  }, [fetchMethods]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!phone.trim()) {
      toast.error(t("payment_methods.errors.phone_required") || "Weka namba ya simu.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/payments/payment-methods/", {
        method_type: "PAWAPAY",
        mno,
        phone: phone.trim(),
        account_identifier: phone.trim(),
      });
      toast.success(t("payment_methods.added") || "Njia ya malipo imeongezwa.");
      setPhone("");
      fetchMethods();
    } catch (error) {
      const errors = error.response?.data;
      const firstError = errors && typeof errors === "object" ? Object.values(errors)[0] : null;
      toast.error((Array.isArray(firstError) ? firstError[0] : firstError) || t("payment_methods.errors.failed") || "Imeshindwa.");
    } finally {
      setSubmitting(false);
    }
  };

  const setDefault = async (id) => {
    setBusyId(id);
    try {
      await api.post(`/payments/payment-methods/${id}/set-default/`);
      fetchMethods();
    } catch {
      toast.error(t("payment_methods.errors.failed") || "Imeshindwa.");
    } finally {
      setBusyId(null);
    }
  };

  const handleDelete = async (id) => {
    setBusyId(id);
    try {
      await api.delete(`/payments/payment-methods/${id}/`);
      setMethods((prev) => prev.filter((m) => m.id !== id));
    } catch {
      toast.error(t("payment_methods.errors.delete_failed") || "Imeshindwa kufuta.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <Card>
        <CardHeader title={t("payment_methods.add") || "Ongeza Njia ya Malipo"} icon={<Smartphone className="w-5 h-5" />} divider />
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-3">
            <select
              value={mno}
              onChange={(e) => setMno(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            >
              {MNO_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <input
              type="text"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+255XXXXXXXXX"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            />
            <Button type="submit" disabled={submitting} className="bg-purple-600 hover:bg-purple-700">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <PlusCircle className="w-4 h-4 mr-2" />}
              {t("payment_methods.submit") || "Ongeza"}
            </Button>
          </form>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-3">
            {t("payment_methods.card_hint") || "Unataka kuongeza kadi ya benki?"}{" "}
            <Link to="/jamiiwallet/add-card" className="text-purple-600 dark:text-purple-400 hover:underline">
              {t("payment_methods.card_link") || "Bofya hapa"}
            </Link>
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader title={t("payment_methods.title") || "Njia za Malipo"} divider />
        <CardContent>
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin mx-auto text-gray-400" />
          ) : methods.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("payment_methods.empty") || "Hakuna njia za malipo bado."}
            </p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {methods.map((m) => (
                <div key={m.id} className="flex items-center justify-between py-3">
                  <div className="flex items-center gap-2">
                    {m.method_type === "CREDIT_CARD" ? (
                      <CreditCard className="w-5 h-5 text-gray-400" />
                    ) : (
                      <Smartphone className="w-5 h-5 text-purple-500" />
                    )}
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {m.mno_display || m.method_type_display}
                        {m.is_default && <Star className="w-3.5 h-3.5 inline ml-1 text-yellow-500 fill-yellow-500" />}
                      </p>
                      {m.last4 && <p className="text-sm text-gray-500 dark:text-gray-400">•••• {m.last4}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {!m.is_default && (
                      <Button size="sm" variant="outline" disabled={busyId === m.id} onClick={() => setDefault(m.id)}>
                        {t("payment_methods.set_default") || "Weka Default"}
                      </Button>
                    )}
                    <Button size="sm" variant="outline" disabled={busyId === m.id} onClick={() => handleDelete(m.id)}>
                      {busyId === m.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4 text-red-500" />}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
