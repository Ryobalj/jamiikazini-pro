// src/app/orders/pages/OrdersListPage.jsx

import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Loader2, Package, Store, Tag } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";

export default function OrdersListPage() {
  const { t } = useTranslation("orders");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();

  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/orders/")
      .then((res) => {
        const data = Array.isArray(res.data) ? res.data : res.data?.results || [];
        setOrders(data);
      })
      .catch(() => setOrders([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-blue-600" />
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">
            {t("list_title", "My Orders")}
          </h1>
        </div>
        <Link to="/offers/mine" className="flex items-center gap-1 text-sm text-purple-600 dark:text-purple-400 hover:underline">
          <Tag className="w-4 h-4" /> {t("my_offers_link", "Ofa Zangu")}
        </Link>
      </div>

      {orders.length === 0 ? (
        <div className="text-center py-16 text-gray-400 dark:text-gray-500">
          <Package className="w-10 h-10 mx-auto mb-2" />
          <p>{t("no_orders", "You have no orders yet.")}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map((order) => (
            <Card
              key={order.id}
              className="cursor-pointer hover:shadow-medium transition-shadow"
              onClick={() => navigate(`/orders/${order.id}`)}
            >
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-1.5 text-sm text-gray-700 dark:text-gray-300">
                    <Store className="w-3.5 h-3.5" /> {order.business_name}
                  </div>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                    {new Date(order.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {formatCurrency(order.total_amount)}
                  </p>
                  <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300">
                    {t(`order_status_${order.status?.toLowerCase()}`, order.status)}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
