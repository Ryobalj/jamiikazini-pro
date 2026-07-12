// src/app/payments/pages/InvoicesPage.jsx

import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import api from "@/lib/axios";
import { FileText, Loader2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useCurrency } from "@/context/CurrencyContext";

const STATUS_STYLES = {
  PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  PAID: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  CANCELLED: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
  OVERDUE: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};

export default function InvoicesPage() {
  const { t } = useTranslation("payments");
  const { formatCurrency } = useCurrency();

  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [payingId, setPayingId] = useState(null);

  const fetchInvoices = useCallback(() => {
    setLoading(true);
    api
      .get("/payments/invoices/")
      .then((res) => setInvoices(res.data?.results || res.data || []))
      .catch(() => setInvoices([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  const markPaid = async (id) => {
    setPayingId(id);
    try {
      await api.post(`/payments/invoices/${id}/mark-paid/`);
      toast.success(t("invoices.marked_paid") || "Invoice imewekwa kama imelipwa.");
      fetchInvoices();
    } catch (error) {
      toast.error(error.response?.data?.detail || t("invoices.errors.failed") || "Imeshindwa.");
    } finally {
      setPayingId(null);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <Card>
        <CardHeader title={t("invoices.title") || "Invoices"} icon={<FileText className="w-5 h-5" />} divider />
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : invoices.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
              {t("invoices.empty") || "Hakuna invoice bado."}
            </p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {invoices.map((inv) => (
                <div key={inv.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{inv.invoice_number}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {t("invoices.due") || "Mwisho"}: {inv.due_date}
                    </p>
                    <span
                      className={`inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${
                        STATUS_STYLES[inv.status] || STATUS_STYLES.PENDING
                      }`}
                    >
                      {inv.status_display || inv.status}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900 dark:text-white">{formatCurrency(inv.total_amount)}</p>
                    {inv.status === "PENDING" && (
                      <Button
                        size="sm"
                        className="mt-1 bg-green-600 hover:bg-green-700"
                        disabled={payingId === inv.id}
                        onClick={() => markPaid(inv.id)}
                      >
                        {payingId === inv.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <>
                            <CheckCircle2 className="w-4 h-4 mr-1" />
                            {t("invoices.mark_paid") || "Weka Imelipwa"}
                          </>
                        )}
                      </Button>
                    )}
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
