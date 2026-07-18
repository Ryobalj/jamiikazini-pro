// src/app/businesses/pages/CreditAccountPage.jsx
//
// Business-owner view of their B2B credit account: limit, outstanding balance,
// and the list of invoices raised against Net-15/Net-30 orders they placed as
// a buyer. Reuses the existing Invoice model/endpoints - only the "pay" action
// (which actually moves wallet funds) is new, distinct from the admin-only
// mark-paid action used elsewhere.

import React, { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ArrowLeft, CreditCard, FileText, Loader2, CheckCircle2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";

const STATUS_STYLES = {
  PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  PAID: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  CANCELLED: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
  OVERDUE: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};

export default function CreditAccountPage() {
  const { t } = useTranslation("payments");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();

  const [business, setBusiness] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [payingId, setPayingId] = useState(null);

  const fetchAll = useCallback(() => {
    setLoading(true);
    Promise.all([
      api.get("/kiini/dashboard-context/"),
      api.get("/payments/invoices/"),
    ])
      .then(([ctxRes, invRes]) => {
        const biz = ctxRes.data?.business || null;
        setBusiness(biz);
        const allInvoices = invRes.data?.results || invRes.data || [];
        setInvoices(
          allInvoices.filter((inv) => inv.b2b_order && inv.b2b_order.purchasing_business_id === biz?.id)
        );
      })
      .catch(() => {
        setBusiness(null);
        setInvoices([]);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const payInvoice = async (id) => {
    setPayingId(id);
    try {
      await api.post(`/payments/invoices/${id}/pay/`);
      toast.success(t("credit_account.paid", "Invoice imelipwa kikamilifu."));
      fetchAll();
    } catch (error) {
      toast.error(error.response?.data?.detail || t("credit_account.pay_failed", "Imeshindwa kulipa invoice."));
    } finally {
      setPayingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!business) {
    return (
      <div className="max-w-lg mx-auto p-6 text-center py-20">
        <p className="text-gray-500 dark:text-gray-400">
          {t("credit_account.no_business", "Huna biashara iliyothibitishwa yenye akaunti ya mkopo.")}
        </p>
      </div>
    );
  }

  const creditLimit = Number(business.credit_limit || 0);
  const availableCredit = Number(business.available_credit || 0);
  const outstanding = creditLimit - availableCredit;

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("credit_account.title", "Akaunti ya Mkopo")} - {business.name}
        </h1>
      </div>

      <Card>
        <CardHeader title={t("credit_account.summary", "Muhtasari wa Mkopo")} icon={<CreditCard className="w-5 h-5" />} divider />
        <CardContent className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">{t("credit_account.limit", "Kikomo cha Mkopo")}</p>
            <p className="font-semibold text-gray-900 dark:text-white">{formatCurrency(creditLimit)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">{t("credit_account.outstanding", "Deni Lililopo")}</p>
            <p className="font-semibold text-red-600 dark:text-red-400">{formatCurrency(outstanding)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">{t("credit_account.available", "Mkopo Uliobaki")}</p>
            <p className="font-semibold text-green-600 dark:text-green-400">{formatCurrency(availableCredit)}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader title={t("credit_account.invoices", "Invoice za Mkopo")} icon={<FileText className="w-5 h-5" />} divider />
        <CardContent>
          {invoices.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
              {t("credit_account.no_invoices", "Hakuna invoice za mkopo bado.")}
            </p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {invoices.map((inv) => (
                <div key={inv.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{inv.invoice_number}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {inv.b2b_order?.business_name} · {t("credit_account.due", "Mwisho")}: {inv.due_date}
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
                        onClick={() => payInvoice(inv.id)}
                      >
                        {payingId === inv.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <>
                            <CheckCircle2 className="w-4 h-4 mr-1" />
                            {t("credit_account.pay_now", "Lipa Sasa")}
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
