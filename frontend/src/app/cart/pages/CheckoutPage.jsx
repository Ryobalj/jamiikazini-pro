// src/app/cart/pages/CheckoutPage.jsx

import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowLeft, Loader2, CheckCircle2, Wallet, AlertTriangle, ShieldAlert, Tag } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useCart } from "@/context/CartContext";
import { useCurrency } from "@/context/CurrencyContext";
import CheckoutBusinessSection from "@/app/cart/components/CheckoutBusinessSection";

export default function CheckoutPage() {
  const { t } = useTranslation("cart");
  const navigate = useNavigate();
  const { items, itemsByBusiness, clearCart } = useCart();
  const { formatCurrency } = useCurrency();

  const [submitting, setSubmitting] = useState(false);
  const [placedOrders, setPlacedOrders] = useState(null);
  const [walletBalance, setWalletBalance] = useState(null);
  const [loadingWallet, setLoadingWallet] = useState(true);
  const [isIdentityVerified, setIsIdentityVerified] = useState(true);
  const [myBusiness, setMyBusiness] = useState(null);
  const [groupState, setGroupState] = useState({});
  const [referralCode, setReferralCode] = useState("");

  useEffect(() => {
    api
      .get("/jamiiwallet/wallet/")
      .then((res) => setWalletBalance(Number(res.data?.balance || 0)))
      .catch(() => setWalletBalance(null))
      .finally(() => setLoadingWallet(false));
  }, []);

  useEffect(() => {
    api
      .get("/auth/me/")
      .then((res) => setIsIdentityVerified(!!res.data?.is_identity_verified))
      .catch(() => {});
  }, []);

  useEffect(() => {
    api
      .get("/kiini/dashboard-context/")
      .then((res) => setMyBusiness(res.data?.business?.is_verified ? res.data.business : null))
      .catch(() => setMyBusiness(null));
  }, []);

  const handleGroupChange = (businessId, data) => {
    setGroupState((prev) => ({ ...prev, [businessId]: data }));
  };

  const groupEntries = Object.values(groupState);
  const grandTotal = groupEntries.reduce((sum, g) => sum + g.total, 0);
  // Cash-paid groups aren't charged to the wallet at all - only wallet-method
  // groups should count against the buyer's available balance.
  const walletChargeTotal = groupEntries
    .filter((g) => g.paymentMethod !== "CASH")
    .reduce((sum, g) => sum + g.total, 0);
  const anyDelivery = groupEntries.some((g) => g.fulfillmentType === "DELIVERY");
  const anyCash = groupEntries.some((g) => g.paymentMethod === "CASH");
  const allValid = itemsByBusiness.length > 0 && itemsByBusiness.every((g) => groupState[g.businessId]?.isValid);
  const insufficientBalance = walletBalance != null && walletBalance < walletChargeTotal;

  const handlePlaceOrder = async () => {
    if (items.length === 0 || !allValid) {
      toast.error(t("delivery_details_required", "Chagua eneo la kupokelea na aina ya usafiri."));
      return;
    }
    setSubmitting(true);
    try {
      const code = referralCode.trim();
      const orders = itemsByBusiness.map((g) => {
        const payload = groupState[g.businessId].payload;
        return code ? { ...payload, referral_code: code } : payload;
      });
      const res = await api.post("/orders/bulk/", { orders });
      setPlacedOrders(res.data?.orders || []);
      clearCart();
      toast.success(
        anyDelivery
          ? t("order_held", "Order imepokewa - fedha zimeshikiliwa mpaka delivery ikamilike!")
          : anyCash
          ? t("order_placed_cash", "Order yako imethibitishwa - lipa taslimu ukichukua bidhaa!")
          : t("order_placed", "Order yako imelipwa na kutumwa kikamilifu!")
      );
    } catch (error) {
      const detail =
        error.response?.data?.payment ||
        error.response?.data?.payment_method ||
        error.response?.data?.delivery ||
        error.response?.data?.items?.[0] ||
        error.response?.data?.non_field_errors?.[0] ||
        error.response?.data?.detail ||
        t("order_failed", "Imeshindwa kutuma order. Jaribu tena.");
      toast.error(typeof detail === "string" ? detail : t("order_failed", "Imeshindwa kutuma order. Jaribu tena."));
    } finally {
      setSubmitting(false);
    }
  };

  if (placedOrders) {
    const anyHeld = placedOrders.some((o) => o.payment_status === "HELD");
    const anyCashPending = placedOrders.some((o) => o.payment_status === "CASH_PENDING");
    return (
      <div className="max-w-lg mx-auto p-6 text-center py-20">
        <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          {t("order_confirmed", "Order Imethibitishwa")}
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mb-6">
          {anyHeld
            ? t("order_confirmed_desc_delivery", "Fedha zimeshikiliwa - zitatolewa kwa muuzaji na dereva baada ya delivery kukamilika na wewe kuthibitisha kupokea.")
            : anyCashPending
            ? t("order_confirmed_desc_cash", "Lipa taslimu ukichukua bidhaa dukani - muuzaji atathibitisha malipo yakishapokewa.")
            : t("order_confirmed_desc", "Muuzaji ataangalia order yako hivi karibuni.")}
        </p>
        <div className="space-y-2">
          {placedOrders.map((order) => (
            <Button key={order.id} className="w-full" onClick={() => navigate(`/orders/${order.id}`)}>
              {order.business_name} - {t("track_order", "Fuatilia Order")}
            </Button>
          ))}
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="max-w-lg mx-auto p-6 text-center py-20">
        <p className="text-gray-500 dark:text-gray-400 mb-6">
          {t("empty_title", "Kikapu chako kiko tupu")}
        </p>
        <Button onClick={() => navigate("/nearby")}>
          {t("browse_businesses", "Tafuta Biashara")}
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t("checkout_title", "Kamilisha Order")}
        </h1>
      </div>

      {!isIdentityVerified && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 text-sm">
          <ShieldAlert className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            {t("identity_verification_required", "Lazima uthibitishe kitambulisho chako kabla ya kununua.")}{" "}
            <Link to="/verify-identity" className="underline font-medium">
              {t("verify_now", "Thibitisha Sasa")}
            </Link>
          </div>
        </div>
      )}

      {itemsByBusiness.length > 1 && (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {t("multi_seller_note", "Bidhaa zako zitatumwa kama oda tofauti kwa kila muuzaji.")}
        </p>
      )}

      {itemsByBusiness.map((group) => (
        <CheckoutBusinessSection key={group.businessId} group={group} onChange={handleGroupChange} myBusiness={myBusiness} />
      ))}

      <div className="flex items-center justify-between px-1 text-xs text-gray-400 dark:text-gray-500">
        <div className="flex items-center gap-1.5">
          <Wallet className="w-3.5 h-3.5" />
          {t("wallet_balance_label", "Salio linalopatikana JamiiWallet")}
        </div>
        <span>
          {loadingWallet ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : walletBalance != null ? (
            formatCurrency(walletBalance)
          ) : (
            "—"
          )}
        </span>
      </div>

      {insufficientBalance && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            {t("insufficient_balance", "Salio la JamiiWallet halitoshi kulipia order hii.")}{" "}
            <Link to="/jamiiwallet" className="underline font-medium">
              {t("topup_wallet", "Weka pesa kwenye Wallet")}
            </Link>
          </div>
        </div>
      )}

      <p className="text-xs text-gray-400 dark:text-gray-500">
        {anyDelivery
          ? t("payment_note_delivery", "Malipo ya bidhaa na usafiri yatashikiliwa (escrow) hadi delivery ithibitishwe na wewe na dereva - ndipo fedha zitatolewa kwa muuzaji na dereva.")
          : anyCash
          ? t("payment_note_mixed_cash", "Baadhi ya bidhaa zitalipiwa taslimu ukichukua dukani - zilizobaki zitakatwa kwenye JamiiWallet yako sasa hivi.")
          : t("payment_note", "Malipo ya bidhaa na huduma hufanyika kupitia JamiiWallet pekee - kiasi kitakatwa moja kwa moja unapotuma order.")}
      </p>

      <div>
        <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          <Tag className="w-3.5 h-3.5" /> {t("referral_code_label", "Msimbo wa Dalali (hiari)")}
        </label>
        <input
          type="text"
          value={referralCode}
          onChange={(e) => setReferralCode(e.target.value)}
          placeholder={t("referral_code_placeholder", "Mfano: AB12CD34")}
          className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
        />
      </div>

      <Card>
        <CardContent className="p-4 flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {t("amount_to_be_charged", "Utatozwa")}
          </span>
          <span className="text-xl font-bold text-gray-900 dark:text-white">
            {formatCurrency(grandTotal)}
          </span>
        </CardContent>
      </Card>

      <Button
        onClick={handlePlaceOrder}
        disabled={submitting || insufficientBalance || !isIdentityVerified || !allValid}
        className="w-full"
        size="lg"
      >
        {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
        {anyDelivery ? t("place_order_delivery", "Shikilia Malipo na Tuma Order") : t("place_order", "Lipa na Tuma Order")}
      </Button>
    </div>
  );
}
