// src/app/businesses/pages/Settings.jsx

import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "@/lib/axios";
import { Loader2, Package, AlertTriangle, PlusCircle, Store } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";

import { useProducts } from "@/hooks/useProducts";

const LOW_STOCK_THRESHOLD = 5;

export default function Settings() {
  const { id: businessId } = useParams();
  const { t } = useTranslation("businesses");

  const { products, loading: loadingProducts, fetchProducts } = useProducts(businessId);
  const [business, setBusiness] = useState(null);
  const [loadingBusiness, setLoadingBusiness] = useState(true);
  const [restockingSlug, setRestockingSlug] = useState(null);
  const [restockAmounts, setRestockAmounts] = useState({});

  useEffect(() => {
    if (!businessId) return;
    api
      .get(`/businesses/${businessId}/`)
      .then((res) => setBusiness(res.data))
      .catch(() => setBusiness(null))
      .finally(() => setLoadingBusiness(false));
  }, [businessId]);

  const lowStockProducts = products.filter((p) => p.quantity_in_stock <= LOW_STOCK_THRESHOLD);

  const handleRestock = async (slug) => {
    const amount = parseInt(restockAmounts[slug], 10);
    if (!amount || amount <= 0) {
      toast.error(t("settings.errors.invalid_quantity") || "Weka kiasi sahihi.");
      return;
    }
    setRestockingSlug(slug);
    try {
      await api.post(`/businesses/${businessId}/products/${slug}/restock/`, { quantity: amount });
      toast.success(t("settings.restocked") || "Stock imeongezwa.");
      setRestockAmounts((prev) => ({ ...prev, [slug]: "" }));
      fetchProducts();
    } catch (error) {
      toast.error(error.response?.data?.quantity?.[0] || t("settings.errors.restock_failed") || "Imeshindwa.");
    } finally {
      setRestockingSlug(null);
    }
  };

  return (
    <div className="p-4 space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
        {t("tabs.settings") || "Mipangilio"}
      </h1>

      <Card>
        <CardHeader title={t("settings.business_info") || "Taarifa za Biashara"} icon={<Store className="w-5 h-5" />} divider />
        <CardContent>
          {loadingBusiness ? (
            <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
          ) : business ? (
            <div className="space-y-1">
              <p className="font-medium text-gray-900 dark:text-white">{business.name}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {business.category_name || t("settings.no_category") || "Bila aina"}
                {business.is_verified && ` · ${t("settings.verified") || "Imethibitishwa"}`}
              </p>
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("settings.load_failed") || "Imeshindwa kupakia biashara."}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader
          title={t("settings.low_stock") || "Bidhaa Zenye Stock Kidogo"}
          icon={<AlertTriangle className="w-5 h-5 text-yellow-500" />}
          divider
        />
        <CardContent>
          {loadingProducts ? (
            <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
          ) : lowStockProducts.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
              <Package className="w-4 h-4" />
              {t("settings.no_low_stock") || "Bidhaa zote zina stock ya kutosha."}
            </p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {lowStockProducts.map((p) => (
                <div key={p.slug} className="flex items-center justify-between py-3 gap-3">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{p.name}</p>
                    <p className="text-sm text-red-500">
                      {t("settings.stock_remaining", { count: p.quantity_in_stock }) ||
                        `Zimebaki: ${p.quantity_in_stock}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min="1"
                      value={restockAmounts[p.slug] || ""}
                      onChange={(e) => setRestockAmounts((prev) => ({ ...prev, [p.slug]: e.target.value }))}
                      placeholder="+"
                      className="w-16 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                    />
                    <Button
                      size="sm"
                      className="bg-purple-600 hover:bg-purple-700"
                      disabled={restockingSlug === p.slug}
                      onClick={() => handleRestock(p.slug)}
                    >
                      {restockingSlug === p.slug ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <PlusCircle className="w-4 h-4" />
                      )}
                    </Button>
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
