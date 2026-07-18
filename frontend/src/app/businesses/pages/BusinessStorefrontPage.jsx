// src/app/businesses/pages/BusinessStorefrontPage.jsx

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Store, Loader2, Star, Phone, Mail, Globe, ShieldCheck,
  MessageCircle, ShoppingCart, Wrench, User as UserIcon, PackageX, Building2, Tag,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useCart } from "@/context/CartContext";
import { useCurrency } from "@/context/CurrencyContext";

const THEME_BY_TYPE = {
  products: { icon: Store, label: "storefront.type_products" },
  services: { icon: Wrench, label: "storefront.type_services" },
  informal: { icon: UserIcon, label: "storefront.type_informal" },
};

// Mirrors businesses.models.product.WHOLE_UNIT_TYPES - units that can't be fractional.
const WHOLE_UNIT_TYPES = new Set(["pcs", "box", "pack", "dozen", "pair", "set", "session", "gunia", "debe", "fungu", "roli", "bale"]);

export default function BusinessStorefrontPage() {
  const { id: businessId } = useParams();
  const { t } = useTranslation("businesses");
  const navigate = useNavigate();
  const { addItem } = useCart();
  const { formatCurrency } = useCurrency();

  const [business, setBusiness] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [messaging, setMessaging] = useState(false);
  const [quantities, setQuantities] = useState({});
  const [offerFormFor, setOfferFormFor] = useState(null);
  const [offerPrices, setOfferPrices] = useState({});
  const [submittingOffer, setSubmittingOffer] = useState(false);

  const quantityFor = (product) => quantities[product.id] ?? 1;

  useEffect(() => {
    if (!businessId) return;
    setLoading(true);
    api
      .get(`/store/${businessId}/`)
      .then((res) => setBusiness(res.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [businessId]);

  const handleMessageSeller = async () => {
    setMessaging(true);
    try {
      const res = await api.post("/jamiichat/conversations/start-with-business/", {
        business_id: businessId,
        message: "Habari, ningependa kupata maelezo zaidi.",
      });
      navigate(`/jamiichat/${res.data.id}`);
    } catch (err) {
      toast.error(err.response?.data?.business_id?.[0] || "Imeshindwa kuanzisha mazungumzo.");
    } finally {
      setMessaging(false);
    }
  };

  const handleAddToCart = (product) => {
    addItem(product, businessId, business.name, quantityFor(product));
    toast.success(t("storefront.added_to_cart", "Imeongezwa kwenye kikapu"));
  };

  const handleSubmitOffer = async (product) => {
    const price = offerPrices[product.id];
    if (!price || Number(price) <= 0) {
      toast.error(t("storefront.offer_price_required", "Weka bei unayopendekeza."));
      return;
    }
    setSubmittingOffer(true);
    try {
      await api.post("/product-offers/", {
        product: product.id,
        quantity: quantityFor(product),
        proposed_unit_price: price,
      });
      toast.success(t("storefront.offer_sent", "Ofa yako imetumwa kwa muuzaji."));
      setOfferFormFor(null);
      setOfferPrices((prev) => ({ ...prev, [product.id]: "" }));
    } catch (err) {
      toast.error(err.response?.data?.proposed_unit_price?.[0] || err.response?.data?.quantity?.[0] || t("storefront.offer_failed", "Imeshindwa kutuma ofa."));
    } finally {
      setSubmittingOffer(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !business) {
    return (
      <div className="text-center py-20">
        <Store className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
        <p className="text-gray-500 dark:text-gray-400">
          {t("storefront.not_found", "Biashara hii haipatikani.")}
        </p>
      </div>
    );
  }

  const theme = THEME_BY_TYPE[business.storefront_type] || THEME_BY_TYPE.products;
  const ThemeIcon = theme.icon;
  const hasProducts = business.products?.length > 0;
  const hasServices = business.services?.length > 0;

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row sm:items-start gap-4">
            <div className="w-16 h-16 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
              <ThemeIcon className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{business.name}</h1>
                {business.is_verified && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                    <ShieldCheck className="w-3 h-3" /> {t("storefront.verified", "Imethibitishwa")}
                  </span>
                )}
              </div>
              {business.category_name && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{business.category_name}</p>
              )}
              {business.institution && (
                <button
                  onClick={() => navigate(`/institutions/${business.institution.id}/public`)}
                  className="inline-flex items-center gap-1 text-xs text-purple-600 dark:text-purple-400 hover:underline mt-1"
                >
                  <Building2 className="w-3.5 h-3.5" />
                  {t("storefront.part_of", "Sehemu ya {{name}}", { name: business.institution.name })}
                </button>
              )}
              {business.description && (
                <p className="text-gray-600 dark:text-gray-300 mt-2">{business.description}</p>
              )}

              <div className="flex flex-wrap gap-4 mt-3 text-sm text-gray-500 dark:text-gray-400">
                {business.phone && (
                  <span className="flex items-center gap-1"><Phone className="w-3.5 h-3.5" /> {business.phone}</span>
                )}
                {business.email && (
                  <span className="flex items-center gap-1"><Mail className="w-3.5 h-3.5" /> {business.email}</span>
                )}
                {business.website && (
                  <span className="flex items-center gap-1"><Globe className="w-3.5 h-3.5" /> {business.website}</span>
                )}
              </div>

              {business.review_summary?.count > 0 && (
                <div className="flex items-center gap-1 mt-2">
                  <Star className="w-4 h-4 text-yellow-400 fill-current" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {business.review_summary.average}
                  </span>
                  <span className="text-xs text-gray-500">
                    ({business.review_summary.count})
                  </span>
                </div>
              )}
            </div>

            <Button
              onClick={handleMessageSeller}
              disabled={messaging}
              className="bg-purple-600 hover:bg-purple-700 flex-shrink-0"
            >
              {messaging ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <MessageCircle className="w-4 h-4 mr-1" />}
              {t("storefront.message_seller", "Wasiliana na Muuzaji")}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Products */}
      {hasProducts && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            {t("storefront.products_heading", "Bidhaa")}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {business.products.map((product) => (
              <Card key={product.id} className="overflow-hidden">
                {product.image ? (
                  <img src={product.image} alt={product.name} className="w-full h-40 object-cover" />
                ) : (
                  <div className="w-full h-40 bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                    <Store className="w-8 h-8 text-gray-300 dark:text-gray-600" />
                  </div>
                )}
                <CardContent className="p-3">
                  <p className="font-medium text-gray-900 dark:text-white truncate">{product.name}</p>
                  <p className="text-blue-600 dark:text-blue-400 font-semibold mt-1">
                    {formatCurrency(product.final_price ?? product.price)}
                  </p>
                  {product.quantity_in_stock > 0 ? (
                    <>
                      <div className="flex items-center gap-2 mt-2">
                        <input
                          type="number"
                          min={WHOLE_UNIT_TYPES.has(product.unit) ? "1" : "0.1"}
                          step={WHOLE_UNIT_TYPES.has(product.unit) ? "1" : "0.1"}
                          value={quantityFor(product)}
                          onChange={(e) =>
                            setQuantities((prev) => ({ ...prev, [product.id]: Number(e.target.value) }))
                          }
                          className="w-16 p-1.5 text-sm text-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg"
                        />
                        <span className="text-xs text-gray-500 dark:text-gray-400">{product.unit || "pcs"}</span>
                      </div>
                      <Button
                        size="sm"
                        className="w-full mt-2"
                        onClick={() => handleAddToCart(product)}
                      >
                        <ShoppingCart className="w-4 h-4 mr-1" /> {t("storefront.add_to_cart", "Ongeza Kikapuni")}
                      </Button>
                      <button
                        type="button"
                        onClick={() => setOfferFormFor(offerFormFor === product.id ? null : product.id)}
                        className="w-full mt-1.5 flex items-center justify-center gap-1 text-xs text-purple-600 dark:text-purple-400 hover:underline"
                      >
                        <Tag className="w-3.5 h-3.5" /> {t("storefront.make_offer", "Toa Ofa")}
                      </button>
                      {offerFormFor === product.id && (
                        <div className="mt-2 p-2 rounded-lg bg-purple-50 dark:bg-purple-900/20 space-y-2">
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={offerPrices[product.id] || ""}
                            onChange={(e) => setOfferPrices((prev) => ({ ...prev, [product.id]: e.target.value }))}
                            placeholder={t("storefront.offer_price_placeholder", "Bei unayopendekeza")}
                            className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                          />
                          <Button
                            size="sm"
                            className="w-full bg-purple-600 hover:bg-purple-700"
                            disabled={submittingOffer}
                            onClick={() => handleSubmitOffer(product)}
                          >
                            {submittingOffer ? <Loader2 className="w-4 h-4 animate-spin" /> : t("storefront.send_offer", "Tuma Ofa")}
                          </Button>
                        </div>
                      )}
                    </>
                  ) : (
                    <p className="text-xs text-red-500 mt-2 flex items-center gap-1">
                      <PackageX className="w-3.5 h-3.5" /> {t("storefront.out_of_stock", "Haipo Stock")}
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Services */}
      {hasServices && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            {t("storefront.services_heading", "Huduma")}
          </h2>
          <div className="space-y-2">
            {business.services.map((service) => (
              <Card key={service.id}>
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{service.name}</p>
                    {service.description && (
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">{service.description}</p>
                    )}
                  </div>
                  <p className="text-blue-600 dark:text-blue-400 font-semibold whitespace-nowrap ml-4">
                    {formatCurrency(service.price)}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {!hasProducts && !hasServices && (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">
          <PackageX className="w-10 h-10 mx-auto mb-2" />
          <p>{t("storefront.no_catalog", "Biashara hii bado haijaongeza bidhaa au huduma.")}</p>
        </div>
      )}
    </div>
  );
}
