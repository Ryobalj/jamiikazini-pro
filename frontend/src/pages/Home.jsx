// src/pages/Home.jsx

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  MapPin,
  Wallet,
  ShoppingCart,
  Package,
  MessageCircle,
  Store,
  Truck,
  ShieldAlert,
  ArrowRight,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAppContext } from "@/context/AppContext";
import { useCurrency } from "@/context/CurrencyContext";
import api from "@/lib/axios";

function QuickAction({ icon: Icon, label, description, onClick }) {
  return (
    <button
      onClick={onClick}
      className="flex items-start gap-3 p-4 rounded-2xl bg-white dark:bg-gray-800 shadow-soft hover:shadow-medium hover:-translate-y-0.5 transition-all text-left"
    >
      <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
        <Icon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
      </div>
      <div>
        <p className="font-medium text-gray-900 dark:text-white text-sm">{label}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>
      </div>
    </button>
  );
}

export default function Home() {
  const { t } = useTranslation("dashboard");
  const navigate = useNavigate();
  const { user } = useAppContext();
  const { formatCurrency } = useCurrency();

  const [context, setContext] = useState(null);
  const [walletBalance, setWalletBalance] = useState(null);

  useEffect(() => {
    api
      .get("/kiini/dashboard-context/")
      .then((res) => setContext(res.data))
      .catch(() => setContext(null));
    api
      .get("/jamiiwallet/wallet/")
      .then((res) => setWalletBalance(Number(res.data?.balance || 0)))
      .catch(() => setWalletBalance(null));
  }, []);

  if (!user) return null;

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
          {t("home.welcome")}, {user.full_name || user.email}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{t("home.subtitle")}</p>
      </div>

      {context && !context.is_identity_verified && (
        <Card className="!p-4 border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20">
          <div className="flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-amber-800 dark:text-amber-300 text-sm">
                {t("home.verification_title")}
              </p>
              <p className="text-xs text-amber-700 dark:text-amber-400 mt-0.5">
                {t("home.verification_desc")}
              </p>
            </div>
            <Button size="sm" onClick={() => navigate("/verify-identity")}>
              {t("home.verification_cta")}
            </Button>
          </div>
        </Card>
      )}

      <div>
        <h2 className="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-3">
          {t("home.quick_actions")}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <QuickAction
            icon={Wallet}
            label={walletBalance != null ? `${t("wallet.title")} - ${formatCurrency(walletBalance)}` : t("wallet.title")}
            description={t("home.action_wallet_desc")}
            onClick={() => navigate("/jamiiwallet")}
          />
          <QuickAction
            icon={ShoppingCart}
            label={t("cart.title")}
            description={t("home.action_cart_desc")}
            onClick={() => navigate("/cart")}
          />
          <QuickAction
            icon={Package}
            label={t("orders.title")}
            description={t("home.action_orders_desc")}
            onClick={() => navigate("/orders")}
          />
          <QuickAction
            icon={MapPin}
            label={t("nearby.title", { ns: "businesses", defaultValue: "Nearby Businesses" })}
            description={t("home.action_nearby_desc")}
            onClick={() => navigate("/nearby")}
          />
          <QuickAction
            icon={MessageCircle}
            label={t("chat.title")}
            description={t("home.action_chat_desc")}
            onClick={() => navigate("/jamiichat")}
          />
          <QuickAction
            icon={Truck}
            label={t("request_service.title")}
            description={t("home.action_request_service_desc")}
            onClick={() => navigate("/logistics/request")}
          />
        </div>
      </div>

      {context?.business && (
        <Card
          className="!p-4 cursor-pointer hover:shadow-medium transition-shadow"
          onClick={() => navigate(`/businesses/dashboard/${context.business.id}/overview`)}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-green-50 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0">
              <Store className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div className="flex-1">
              <p className="text-xs text-gray-500 dark:text-gray-400">{t("home.business_title")}</p>
              <p className="font-medium text-gray-900 dark:text-white text-sm">{context.business.name}</p>
            </div>
            <Button size="sm" variant="secondary">
              {t("home.business_cta")} <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          </div>
        </Card>
      )}

      {context?.driver && (
        <Card
          className="!p-4 cursor-pointer hover:shadow-medium transition-shadow"
          onClick={() => navigate("/logistics/jobs")}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-orange-50 dark:bg-orange-900/30 flex items-center justify-center flex-shrink-0">
              <Truck className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div className="flex-1">
              <p className="text-xs text-gray-500 dark:text-gray-400">{t("home.driver_title")}</p>
              <p className="font-medium text-gray-900 dark:text-white text-sm">
                {context.driver.verification_status === "VERIFIED"
                  ? t("home.driver_status_verified")
                  : context.driver.verification_status === "FAILED"
                  ? t("home.driver_status_failed")
                  : t("home.driver_status_pending")}
              </p>
            </div>
            <Button size="sm" variant="secondary">
              {t("home.driver_cta")} <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
