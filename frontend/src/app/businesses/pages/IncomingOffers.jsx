// src/app/businesses/pages/IncomingOffers.jsx

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Tag, Loader2, PackageCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";

export default function IncomingOffers() {
  const { t } = useTranslation("businesses");
  const { formatCurrency } = useCurrency();

  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [respondingId, setRespondingId] = useState(null);
  const [counterPrices, setCounterPrices] = useState({});

  const fetchIncoming = () => {
    setLoading(true);
    api
      .get("/product-offers/incoming/")
      .then((res) => setOffers(res.data || []))
      .catch(() => setOffers([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchIncoming();
    const interval = setInterval(fetchIncoming, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleRespond = async (offerId, decision) => {
    setRespondingId(offerId);
    try {
      const payload = { decision };
      if (decision === "COUNTER") {
        const price = counterPrices[offerId];
        if (!price || Number(price) <= 0) {
          toast.error(t("offers.counter_price_required", "Weka bei mbadala."));
          setRespondingId(null);
          return;
        }
        payload.counter_unit_price = price;
      }
      await api.post(`/product-offers/${offerId}/respond/`, payload);
      toast.success(t("offers.responded", "Umejibu ofa hii."));
      fetchIncoming();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("offers.respond_failed", "Imeshindwa kujibu ofa."));
    } finally {
      setRespondingId(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Tag className="w-5 h-5 text-purple-600" />
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t("offers.heading", "Ofa za Bei")}
        </h2>
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        {t("offers.description", "Wanunuzi wanapendekeza bei tofauti kwa bidhaa zako - kubali, kataa, au toa ofa mbadala.")}
      </p>

      {loading ? (
        <div className="flex justify-center py-10">
          <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
        </div>
      ) : offers.length === 0 ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">
          <PackageCheck className="w-10 h-10 mx-auto mb-2" />
          <p>{t("offers.empty", "Hakuna ofa za bei kwa sasa.")}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {offers.map((offer) => (
            <Card key={offer.id}>
              <CardContent className="p-4 space-y-3">
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {offer.product_name} <span className="text-gray-400">×{offer.quantity}</span>
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t("offers.buyer_label", "Mnunuzi")}: {offer.buyer_name}
                  </p>
                  <div className="flex items-center gap-3 mt-1 text-sm">
                    <span className="text-gray-400 line-through">{formatCurrency(offer.current_price)}</span>
                    <span className="font-semibold text-purple-600 dark:text-purple-400">
                      {formatCurrency(offer.proposed_unit_price)}
                    </span>
                  </div>
                  {offer.note && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">"{offer.note}"</p>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    className="bg-green-600 hover:bg-green-700"
                    disabled={respondingId === offer.id}
                    onClick={() => handleRespond(offer.id, "ACCEPT")}
                  >
                    {t("offers.accept", "Kubali")}
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={respondingId === offer.id}
                    onClick={() => handleRespond(offer.id, "REJECT")}
                  >
                    {t("offers.reject", "Kataa")}
                  </Button>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={counterPrices[offer.id] || ""}
                    onChange={(e) => setCounterPrices((prev) => ({ ...prev, [offer.id]: e.target.value }))}
                    placeholder={t("offers.counter_price_placeholder", "Bei mbadala")}
                    className="w-32 p-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                  />
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={respondingId === offer.id}
                    onClick={() => handleRespond(offer.id, "COUNTER")}
                  >
                    {respondingId === offer.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("offers.counter", "Toa Ofa Mbadala")}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
