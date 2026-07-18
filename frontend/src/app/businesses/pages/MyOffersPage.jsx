// src/app/businesses/pages/MyOffersPage.jsx
//
// Buyer-facing view of offers they've sent (Toa Ofa from a storefront) - lets
// them track status and respond to a seller's counter-offer.

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowLeft, Tag, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";
import { useCart } from "@/context/CartContext";

const STATUS_STYLES = {
  PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  ACCEPTED: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  REJECTED: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
  COUNTERED: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  EXPIRED: "bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400",
};

export default function MyOffersPage() {
  const { t } = useTranslation("businesses");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();
  const { addItem } = useCart();

  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [decidingId, setDecidingId] = useState(null);

  const fetchOffers = () => {
    setLoading(true);
    api
      .get("/product-offers/")
      .then((res) => setOffers(res.data?.results || res.data || []))
      .catch(() => setOffers([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchOffers();
  }, []);

  const handleDecide = async (offerId, decision) => {
    setDecidingId(offerId);
    try {
      await api.post(`/product-offers/${offerId}/decide/`, { decision });
      toast.success(
        decision === "ACCEPT"
          ? t("offers.counter_accepted", "Umekubali ofa mbadala.")
          : t("offers.counter_rejected", "Umekataa ofa mbadala.")
      );
      fetchOffers();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("offers.respond_failed", "Imeshindwa kujibu ofa."));
    } finally {
      setDecidingId(null);
    }
  };

  const handleAddAcceptedToCart = (offer) => {
    addItem(
      { id: offer.product, name: offer.product_name, price: offer.proposed_unit_price, unit: "pcs", offerId: offer.id },
      offer.business_id,
      offer.business_name,
      Number(offer.quantity)
    );
    toast.success(t("offers.added_to_cart", "Imeongezwa kikapuni kwa bei ya ofa."));
  };

  return (
    <div className="max-w-2xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <Tag className="w-5 h-5 text-purple-600" />
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">
            {t("offers.my_offers_title", "Ofa Zangu")}
          </h1>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
        </div>
      ) : offers.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-12">
          {t("offers.no_offers_sent", "Hujawahi kutuma ofa yoyote bado.")}
        </p>
      ) : (
        <div className="space-y-3">
          {offers.map((offer) => (
            <Card key={offer.id}>
              <CardContent className="p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-gray-900 dark:text-white">{offer.product_name}</p>
                  <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_STYLES[offer.status] || STATUS_STYLES.PENDING}`}>
                    {t(`offers.status_${offer.status?.toLowerCase()}`, offer.status)}
                  </span>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{offer.business_name}</p>
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-gray-400 line-through">{formatCurrency(offer.current_price)}</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {formatCurrency(offer.proposed_unit_price)}
                  </span>
                  {offer.counter_unit_price && (
                    <span className="font-semibold text-purple-600 dark:text-purple-400">
                      → {formatCurrency(offer.counter_unit_price)}
                    </span>
                  )}
                </div>

                {offer.status === "COUNTERED" && (
                  <div className="flex gap-2 pt-1">
                    <Button
                      size="sm"
                      className="bg-green-600 hover:bg-green-700"
                      disabled={decidingId === offer.id}
                      onClick={() => handleDecide(offer.id, "ACCEPT")}
                    >
                      {decidingId === offer.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("offers.accept_counter", "Kubali Ofa Mbadala")}
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={decidingId === offer.id}
                      onClick={() => handleDecide(offer.id, "REJECT")}
                    >
                      {t("offers.reject", "Kataa")}
                    </Button>
                  </div>
                )}

                {offer.status === "ACCEPTED" && !offer.consumed && (
                  <Button size="sm" className="mt-1" onClick={() => handleAddAcceptedToCart(offer)}>
                    {t("offers.add_to_cart_at_offer_price", "Ongeza Kikapuni kwa Bei ya Ofa")}
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
