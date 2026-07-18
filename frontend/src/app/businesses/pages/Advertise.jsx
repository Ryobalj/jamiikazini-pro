// src/app/businesses/pages/Advertise.jsx

import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Megaphone, Loader2, CheckCircle2, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useProducts } from "@/hooks/useProducts";

const DURATIONS = [
  { days: 7, price: 14000 },
  { days: 14, price: 28000 },
  { days: 30, price: 60000 },
];

export default function Advertise() {
  const { id: businessId } = useParams();
  const { t } = useTranslation("businesses");
  const { products } = useProducts(businessId);

  const [days, setDays] = useState(7);
  const [productId, setProductId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [myListings, setMyListings] = useState([]);
  const [loadingListings, setLoadingListings] = useState(true);

  const fetchMine = () => {
    setLoadingListings(true);
    api
      .get("/featured-listings/mine/")
      .then((res) => setMyListings(res.data.filter((l) => l.business === businessId)))
      .catch(() => setMyListings([]))
      .finally(() => setLoadingListings(false));
  };

  useEffect(() => {
    fetchMine();
  }, [businessId]);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await api.post("/featured-listings/request/", {
        business: businessId,
        product: productId || null,
        days,
      });
      toast.success(
        t("advertise.request_success", "Ombi limetumwa. Lipa invoice ili tangazo lianze kuonekana.")
      );
      fetchMine();
    } catch (err) {
      toast.error(
        err.response?.data?.detail ||
          err.response?.data?.business?.[0] ||
          t("advertise.request_failed", "Imeshindwa kutuma ombi.")
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-2">
        <Megaphone className="w-6 h-6 text-amber-500" />
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("advertise.heading", "Tangaza Biashara Yako")}
        </h1>
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        {t(
          "advertise.description",
          "Weka bidhaa au biashara yako kwenye ukurasa wa mbele wa Jamiikazini ili wateja wengi zaidi waione."
        )}
      </p>

      <Card>
        <CardContent className="p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t("advertise.product_label", "Bidhaa ya kutangaza (hiari)")}
            </label>
            <select
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 bg-white dark:bg-gray-800 dark:border-gray-700"
            >
              <option value="">{t("advertise.whole_business", "Biashara nzima (bila bidhaa maalum)")}</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t("advertise.duration_label", "Muda wa tangazo")}
            </label>
            <div className="grid grid-cols-3 gap-2">
              {DURATIONS.map((d) => (
                <button
                  key={d.days}
                  onClick={() => setDays(d.days)}
                  className={`border rounded-lg py-2 text-sm transition ${
                    days === d.days
                      ? "border-blue-600 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400"
                      : "border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300"
                  }`}
                >
                  <div className="font-semibold">{d.days} {t("advertise.days", "siku")}</div>
                  <div className="text-xs">{d.price.toLocaleString()} TZS</div>
                </button>
              ))}
            </div>
          </div>

          <Button onClick={handleSubmit} disabled={submitting} className="w-full bg-amber-500 hover:bg-amber-600">
            {submitting ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Megaphone className="w-4 h-4 mr-1" />}
            {t("advertise.submit", "Tuma Ombi la Kutangaza")}
          </Button>
        </CardContent>
      </Card>

      <div>
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
          {t("advertise.mine_heading", "Matangazo Yako")}
        </h2>
        {loadingListings ? (
          <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
        ) : myListings.length === 0 ? (
          <p className="text-sm text-gray-400">{t("advertise.mine_empty", "Bado hujaomba tangazo lolote.")}</p>
        ) : (
          <div className="space-y-2">
            {myListings.map((l) => (
              <Card key={l.id}>
                <CardContent className="p-3 flex items-center justify-between text-sm">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {l.product_name || t("advertise.whole_business", "Biashara nzima")}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {l.start_date} - {l.end_date} · {Number(l.amount).toLocaleString()} TZS
                    </p>
                  </div>
                  {l.is_active ? (
                    <span className="flex items-center gap-1 text-green-600 text-xs font-medium">
                      <CheckCircle2 className="w-4 h-4" /> {t("advertise.status_active", "Inaonekana")}
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-amber-600 text-xs font-medium">
                      <Clock className="w-4 h-4" /> {t("advertise.status_pending", "Inasubiri Malipo")}
                    </span>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
