// src/app/cart/components/CheckoutBusinessSection.jsx
//
// One seller's worth of checkout config (fulfillment/delivery/notes), scoped
// to a single business group from CartContext.itemsByBusiness. CheckoutPage
// renders one of these per seller and aggregates their payloads for a single
// bulk order-creation request.

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Loader2, Truck, Store, Briefcase, Wallet, Banknote } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";

export default function CheckoutBusinessSection({ group, onChange, myBusiness }) {
  const { t } = useTranslation("cart");
  const { formatCurrency } = useCurrency();

  const [notes, setNotes] = useState("");
  const [fulfillmentType, setFulfillmentType] = useState("PICKUP");
  const [dropoffLocation, setDropoffLocation] = useState(null);
  const [dropoffAddress, setDropoffAddress] = useState("");
  const [weightKg, setWeightKg] = useState("1");
  const [volumeCbm, setVolumeCbm] = useState("");
  const [quotes, setQuotes] = useState([]);
  const [loadingQuotes, setLoadingQuotes] = useState(false);
  const [selectedVehicleType, setSelectedVehicleType] = useState(null);
  const [businessLocation, setBusinessLocation] = useState(null);
  const [buyingAsBusiness, setBuyingAsBusiness] = useState(false);
  const [paymentTerms, setPaymentTerms] = useState("IMMEDIATE");
  const [paymentMethod, setPaymentMethod] = useState("WALLET");
  const [businessIsVerified, setBusinessIsVerified] = useState(false);

  // A business can't buy from itself as a B2B credit purchase.
  const canBuyAsBusiness = myBusiness && myBusiness.id !== group.businessId && Number(myBusiness.available_credit) > 0;
  // Cash-on-pickup has no escrow protection - only offered for verified sellers, PICKUP only.
  const canPayCash = businessIsVerified && fulfillmentType === "PICKUP";

  useEffect(() => {
    api
      .get(`/store/${group.businessId}/`)
      .then((res) => {
        setBusinessLocation(res.data?.location || null);
        setBusinessIsVerified(!!res.data?.is_verified);
      })
      .catch(() => {
        setBusinessLocation(null);
        setBusinessIsVerified(false);
      });
  }, [group.businessId]);

  useEffect(() => {
    if (fulfillmentType !== "DELIVERY" || dropoffLocation) return;
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setDropoffLocation({ lat: position.coords.latitude, lng: position.coords.longitude });
      },
      () => {}
    );
  }, [fulfillmentType, dropoffLocation]);

  useEffect(() => {
    if (fulfillmentType !== "DELIVERY" || !dropoffLocation || !businessLocation) return;
    setLoadingQuotes(true);
    api
      .get("/logistics/delivery-quote/", {
        params: {
          pickup_lat: businessLocation.latitude,
          pickup_lng: businessLocation.longitude,
          dropoff_lat: dropoffLocation.lat,
          dropoff_lng: dropoffLocation.lng,
          weight_kg: weightKg ? Number(weightKg) : undefined,
          volume_cbm: volumeCbm ? Number(volumeCbm) : undefined,
        },
      })
      .then((res) => {
        const newQuotes = res.data?.quotes || [];
        setQuotes(newQuotes);
        const stillValid = newQuotes.some((q) => q.vehicle_type === selectedVehicleType);
        if (newQuotes.length && !stillValid) {
          setSelectedVehicleType(newQuotes[0].vehicle_type);
        } else if (!newQuotes.length) {
          setSelectedVehicleType(null);
        }
      })
      .catch(() => setQuotes([]))
      .finally(() => setLoadingQuotes(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fulfillmentType, dropoffLocation, businessLocation, weightKg, volumeCbm]);

  const selectedQuote = quotes.find((q) => q.vehicle_type === selectedVehicleType);
  const deliveryFee = fulfillmentType === "DELIVERY" ? Number(selectedQuote?.estimated_fare || 0) : 0;
  const groupTotal = group.subtotal + deliveryFee;
  const creditDeliveryConflict =
    canBuyAsBusiness && buyingAsBusiness && paymentTerms !== "IMMEDIATE" && fulfillmentType === "DELIVERY";
  const payingCash = canPayCash && paymentMethod === "CASH";
  const cashCreditConflict = payingCash && canBuyAsBusiness && buyingAsBusiness && paymentTerms !== "IMMEDIATE";
  const isValid =
    !creditDeliveryConflict &&
    !cashCreditConflict &&
    (fulfillmentType === "PICKUP" || (!!dropoffLocation && !!selectedVehicleType));

  useEffect(() => {
    const payload = {
      business: group.businessId,
      notes,
      fulfillment_type: fulfillmentType,
      items: group.items.map((i) =>
        i.offerId
          ? { product: i.productId, quantity: i.quantity, offer: i.offerId }
          : { product: i.productId, quantity: i.quantity }
      ),
    };
    if (fulfillmentType === "DELIVERY") {
      payload.delivery = {
        vehicle_type: selectedVehicleType,
        dropoff_lat: dropoffLocation?.lat,
        dropoff_lng: dropoffLocation?.lng,
        dropoff_address_text: dropoffAddress,
        weight_kg: weightKg ? Number(weightKg) : undefined,
        volume_cbm: volumeCbm ? Number(volumeCbm) : undefined,
      };
    }
    if (canBuyAsBusiness && buyingAsBusiness) {
      payload.purchasing_business = myBusiness.id;
      payload.payment_terms = paymentTerms;
    }
    if (payingCash) {
      payload.payment_method = "CASH";
    }
    onChange(group.businessId, { payload, total: groupTotal, isValid, fulfillmentType, deliveryFee, paymentMethod: payingCash ? "CASH" : "WALLET" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    group,
    notes,
    fulfillmentType,
    dropoffLocation,
    dropoffAddress,
    weightKg,
    volumeCbm,
    selectedVehicleType,
    groupTotal,
    payingCash,
    isValid,
    canBuyAsBusiness,
    buyingAsBusiness,
    paymentTerms,
  ]);

  return (
    <Card>
      <CardHeader
        title={group.businessName}
        icon={<Store className="w-4 h-4" />}
      />
      <CardContent className="space-y-4">
        <div className="space-y-2">
          {group.items.map((item) => (
            <div key={item.productId} className="flex justify-between text-sm">
              <span className="text-gray-700 dark:text-gray-300">
                {item.quantity} {item.unit && item.unit !== "pcs" ? item.unit : ""} × {item.name}
              </span>
              <span className="text-gray-900 dark:text-white font-medium">
                {formatCurrency(item.price * item.quantity)}
              </span>
            </div>
          ))}
          {fulfillmentType === "DELIVERY" && deliveryFee > 0 && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-700 dark:text-gray-300">{t("delivery_fee", "Bei ya Usafiri")}</span>
              <span className="text-gray-900 dark:text-white font-medium">{formatCurrency(deliveryFee)}</span>
            </div>
          )}
          <div className="flex justify-between pt-2 mt-2 border-t border-gray-100 dark:border-gray-700 font-semibold text-sm">
            <span>{t("total", "Jumla")}</span>
            <span>{formatCurrency(groupTotal)}</span>
          </div>
        </div>

        {canBuyAsBusiness && (
          <div className="border-t border-gray-100 dark:border-gray-700 pt-3 space-y-3">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={buyingAsBusiness}
                onChange={(e) => setBuyingAsBusiness(e.target.checked)}
                className="rounded border-gray-300"
              />
              <Briefcase className="w-4 h-4 text-gray-500" />
              <span className="text-gray-700 dark:text-gray-300">
                {t("buying_as_business", "Ninanunua kama {{name}}", { name: myBusiness.name })}
              </span>
            </label>
            {buyingAsBusiness && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t("payment_terms_label", "Masharti ya Malipo")}
                </label>
                <select
                  value={paymentTerms}
                  onChange={(e) => setPaymentTerms(e.target.value)}
                  className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                >
                  <option value="IMMEDIATE">{t("payment_terms_immediate", "Lipa Sasa")}</option>
                  <option value="NET_15">{t("payment_terms_net15", "Mkopo - Siku 15")}</option>
                  <option value="NET_30">{t("payment_terms_net30", "Mkopo - Siku 30")}</option>
                </select>
                <p className="text-xs text-gray-400 mt-1">
                  {t("available_credit_label", "Mkopo unaopatikana")}: {formatCurrency(myBusiness.available_credit)}
                </p>
                {fulfillmentType === "DELIVERY" && paymentTerms !== "IMMEDIATE" && (
                  <p className="text-xs text-amber-600 mt-1">
                    {t("credit_pickup_only", "Mkopo unapatikana kwa kuchukua mwenyewe (PICKUP) kwa sasa.")}
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t("fulfillment_label", "Utapokeaje Bidhaa?")}
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setFulfillmentType("PICKUP")}
              className={`flex items-center justify-center gap-2 border rounded-lg py-2.5 text-sm transition ${
                fulfillmentType === "PICKUP"
                  ? "border-blue-600 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400"
                  : "border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300"
              }`}
            >
              <Store className="w-4 h-4" /> {t("fulfillment_pickup", "Kuchukua Mwenyewe")}
            </button>
            <button
              type="button"
              onClick={() => setFulfillmentType("DELIVERY")}
              className={`flex items-center justify-center gap-2 border rounded-lg py-2.5 text-sm transition ${
                fulfillmentType === "DELIVERY"
                  ? "border-blue-600 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400"
                  : "border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300"
              }`}
            >
              <Truck className="w-4 h-4" /> {t("fulfillment_delivery", "Delivery")}
            </button>
          </div>
        </div>

        {canPayCash && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t("payment_method_label", "Utalipaje?")}
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setPaymentMethod("WALLET")}
                className={`flex items-center justify-center gap-2 border rounded-lg py-2.5 text-sm transition ${
                  paymentMethod === "WALLET"
                    ? "border-blue-600 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400"
                    : "border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300"
                }`}
              >
                <Wallet className="w-4 h-4" /> {t("payment_method_wallet", "JamiiWallet")}
              </button>
              <button
                type="button"
                onClick={() => setPaymentMethod("CASH")}
                className={`flex items-center justify-center gap-2 border rounded-lg py-2.5 text-sm transition ${
                  paymentMethod === "CASH"
                    ? "border-blue-600 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400"
                    : "border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300"
                }`}
              >
                <Banknote className="w-4 h-4" /> {t("payment_method_cash", "Taslimu")}
              </button>
            </div>
            {payingCash && (
              <p className="text-xs text-amber-600 mt-1">
                {t("cash_payment_note", "Fedha hazitashikiliwa mtandaoni - lipa taslimu ukichukua bidhaa. Hakuna kinga ya escrow kwa njia hii.")}
              </p>
            )}
            {cashCreditConflict && (
              <p className="text-xs text-red-600 mt-1">
                {t("cash_credit_conflict", "Malipo taslimu hayawezi kuchanganywa na masharti ya mkopo.")}
              </p>
            )}
          </div>
        )}

        {fulfillmentType === "DELIVERY" && (
          <div className="space-y-3 border-t border-gray-100 dark:border-gray-700 pt-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("dropoff_address_label", "Anwani ya Kupokelea")}
              </label>
              <input
                type="text"
                value={dropoffAddress}
                onChange={(e) => setDropoffAddress(e.target.value)}
                placeholder={t("dropoff_address_placeholder", "Mfano: Mtaa wa Uhuru, karibu na Soko Kuu")}
                className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
              />
              {!dropoffLocation && (
                <p className="text-xs text-amber-600 mt-1">
                  {t("dropoff_location_pending", "Tunahitaji ruhusa ya eneo lako ili kukokotoa bei ya usafiri.")}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("weight_label", "Uzito wa Mzigo (kg)")}
              </label>
              <input
                type="number"
                min="0"
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
                placeholder="5"
                className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("volume_label", "Ujazo wa Mzigo (m³, hiari)")}
              </label>
              <input
                type="number"
                min="0"
                step="0.1"
                value={volumeCbm}
                onChange={(e) => setVolumeCbm(e.target.value)}
                placeholder="0.5"
                className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t("vehicle_type_label", "Chagua Aina ya Usafiri")}
              </label>
              {loadingQuotes ? (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin" /> {t("loading_quotes", "Inakokotoa bei...")}
                </div>
              ) : quotes.length === 0 ? (
                <p className="text-sm text-gray-400">{t("no_quotes", "Weka anwani ili kuona chaguo za usafiri.")}</p>
              ) : (
                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {quotes.map((q) => (
                    <button
                      key={q.vehicle_type}
                      type="button"
                      onClick={() => setSelectedVehicleType(q.vehicle_type)}
                      className={`w-full flex items-center justify-between border rounded-lg px-3 py-2 text-sm transition ${
                        selectedVehicleType === q.vehicle_type
                          ? "border-blue-600 bg-blue-50 dark:bg-blue-900/20"
                          : "border-gray-200 dark:border-gray-700"
                      }`}
                    >
                      <span className="text-gray-700 dark:text-gray-300">{q.label}</span>
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {formatCurrency(q.estimated_fare)}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t("notes_label", "Maelezo ya Ziada (hiari)")}
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            placeholder={t("notes_placeholder", "Mfano: nipigie kabla ya kuleta...")}
            className="w-full p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
          />
        </div>
      </CardContent>
    </Card>
  );
}
