// src/app/realestate/pages/MyInquiriesPage.jsx

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import { ArrowLeft, Home, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useCurrency } from "@/context/CurrencyContext";

const STATUS_STYLES = {
  PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  RESERVED: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  COMPLETED: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  CANCELLED: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
  REJECTED: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};

export default function MyInquiriesPage() {
  const { t } = useTranslation("realestate");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();

  const [inquiries, setInquiries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState(null);

  const fetchInquiries = () => {
    setLoading(true);
    api
      .get("/realestate/inquiries/")
      .then((res) => setInquiries(Array.isArray(res.data) ? res.data : res.data?.results || []))
      .catch(() => setInquiries([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchInquiries();
  }, []);

  const runAction = async (id, action, successMsg) => {
    setActingId(id);
    try {
      await api.post(`/realestate/inquiries/${id}/${action}/`);
      toast.success(successMsg);
      fetchInquiries();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("action_failed", "Imeshindwa. Jaribu tena."));
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-6 space-y-4">
      <button
        onClick={() => navigate("/realestate")}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
      >
        <ArrowLeft className="w-4 h-4" /> {t("back", "Rudi")}
      </button>

      <h1 className="text-xl font-bold text-gray-900 dark:text-white">
        {t("my_inquiries_title", "Maombi Yangu")}
      </h1>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
        </div>
      ) : inquiries.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-16">
          {t("no_inquiries", "Hujawahi kutuma ombi lolote bado.")}
        </p>
      ) : (
        <div className="space-y-3">
          {inquiries.map((inq) => (
            <Card key={inq.id}>
              <CardContent className="p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-gray-900 dark:text-white flex items-center gap-1.5">
                    <Home className="w-4 h-4" /> {inq.property_address || t("property", "Mali")}
                  </p>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_STYLES[inq.status]}`}>
                    {t(`status_${inq.status?.toLowerCase()}`, inq.status)}
                  </span>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {inq.property_owner_name} - {formatCurrency(inq.reservation_amount)}
                </p>

                {inq.status === "PENDING" && (
                  <div className="flex gap-2 pt-1">
                    <Button size="sm" disabled={actingId === inq.id} onClick={() => runAction(inq.id, "reserve", t("reserved_success", "Umeshikilia mali hii kwa mafanikio."))}>
                      {actingId === inq.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("reserve", "Shikilia (Lipa)")}
                    </Button>
                    <Button size="sm" variant="secondary" disabled={actingId === inq.id} onClick={() => runAction(inq.id, "cancel", t("cancelled_success", "Ombi limeghairiwa."))}>
                      {t("cancel", "Ghairi")}
                    </Button>
                  </div>
                )}

                {inq.status === "RESERVED" && (
                  <div className="flex gap-2 pt-1">
                    <Button
                      size="sm"
                      disabled={actingId === inq.id || !!inq.buyer_confirmed_at}
                      onClick={() => runAction(inq.id, "confirm-handover", t("confirmed_success", "Umethibitisha - inasubiri upande wa pili."))}
                    >
                      {inq.buyer_confirmed_at
                        ? t("already_confirmed", "Umeshathibitisha - Inasubiri Mmiliki")
                        : t("confirm_handover", "Thibitisha Umepokea")}
                    </Button>
                    <Button size="sm" variant="secondary" disabled={actingId === inq.id} onClick={() => runAction(inq.id, "cancel", t("cancelled_success", "Ombi limeghairiwa - fedha zimerudishwa."))}>
                      {t("cancel", "Ghairi")}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
