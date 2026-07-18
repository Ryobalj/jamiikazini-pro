// src/app/businesses/pages/IncomingRequests.jsx

import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Inbox, Loader2, PackageCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useProducts } from "@/hooks/useProducts";

export default function IncomingRequests() {
  const { id: businessId } = useParams();
  const { t } = useTranslation("businesses");
  const { products } = useProducts(businessId);

  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [claimingId, setClaimingId] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState({});

  const myProductIds = new Set(products.map((p) => p.id));

  const fetchIncoming = () => {
    setLoading(true);
    api
      .get("/item-requests/incoming/")
      .then((res) => setRequests(res.data || []))
      .catch(() => setRequests([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchIncoming();
    const interval = setInterval(fetchIncoming, 15000);
    return () => clearInterval(interval);
  }, [businessId]);

  const handleClaim = async (itemRequestId) => {
    const productId = selectedProduct[itemRequestId];
    if (!productId) {
      toast.error(t("requests.select_product_first", "Chagua bidhaa kwanza."));
      return;
    }
    setClaimingId(itemRequestId);
    try {
      await api.post(`/item-requests/${itemRequestId}/claim/`, { product_id: productId });
      toast.success(t("requests.claim_success", "Umekubali ombi hili - mnunuzi ataelekezwa kwako."));
      fetchIncoming();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("requests.claim_failed", "Imeshindwa kudai ombi hili."));
    } finally {
      setClaimingId(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Inbox className="w-5 h-5 text-blue-600" />
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t("requests.heading", "Maombi ya Wateja")}
        </h2>
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        {t("requests.description", "Wateja walio karibu wanatafuta bidhaa - dai (claim) ombi ili uwahudumie.")}
      </p>

      {loading ? (
        <div className="flex justify-center py-10">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        </div>
      ) : requests.length === 0 ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">
          <PackageCheck className="w-10 h-10 mx-auto mb-2" />
          <p>{t("requests.empty", "Hakuna maombi ya wateja kwa sasa.")}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {requests.map((r) => {
            const matchingProducts = products.filter((p) => myProductIds.has(p.id));
            return (
              <Card key={r.id}>
                <CardContent className="p-4 space-y-3">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {r.product_name_query} <span className="text-gray-400">×{r.quantity}</span>
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t("requests.matched_count_label", "Bidhaa zinazolingana: {{count}}", {
                        count: r.matched_products_count,
                      })}
                    </p>
                  </div>
                  <div className="flex flex-col sm:flex-row gap-2">
                    <select
                      value={selectedProduct[r.id] || ""}
                      onChange={(e) =>
                        setSelectedProduct((prev) => ({ ...prev, [r.id]: e.target.value }))
                      }
                      className="flex-1 p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm text-gray-900 dark:text-white"
                    >
                      <option value="">{t("requests.select_product", "Chagua bidhaa yako inayolingana")}</option>
                      {matchingProducts.map((p) => (
                        <option key={p.id} value={p.id}>{p.name}</option>
                      ))}
                    </select>
                    <Button
                      onClick={() => handleClaim(r.id)}
                      disabled={claimingId === r.id}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      {claimingId === r.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        t("requests.claim", "Dai Ombi")
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
