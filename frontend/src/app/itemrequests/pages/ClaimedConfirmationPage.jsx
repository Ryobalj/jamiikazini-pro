// src/app/itemrequests/pages/ClaimedConfirmationPage.jsx

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { CheckCircle2, Loader2, Store } from "lucide-react";
import { Button } from "@/components/ui/button";
import api from "@/lib/axios";

export default function ClaimedConfirmationPage() {
  const { id } = useParams();
  const { t } = useTranslation("itemrequests");
  const navigate = useNavigate();
  const [itemRequest, setItemRequest] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get(`/item-requests/${id}/`)
      .then((res) => setItemRequest(res.data))
      .catch(() => setItemRequest(null))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!itemRequest || itemRequest.status !== "CLAIMED") {
    return (
      <div className="max-w-md mx-auto p-6 text-center py-20">
        <p className="text-gray-500 dark:text-gray-400 mb-6">
          {t("not_claimed_yet", "Ombi hili bado halijakubaliwa na duka lolote.")}
        </p>
        <Button onClick={() => navigate(`/request-item/${id}/waiting`)}>
          {t("back_to_waiting", "Rudi Kusubiri")}
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto p-6 text-center py-16">
      <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
        {t("claimed_title", "Ombi Lako Limekubaliwa!")}
      </h2>
      <p className="text-gray-500 dark:text-gray-400 mb-6">
        {t("claimed_desc", "{{business}} imekubali kukuhudumia.", {
          business: itemRequest.claimed_by_business_name,
        })}
      </p>
      <div className="flex items-center justify-center gap-2 text-sm text-gray-600 dark:text-gray-300 mb-6">
        <Store className="w-4 h-4" />
        {itemRequest.claimed_product_name}
      </div>
      <Button onClick={() => navigate(`/store/${itemRequest.claimed_by_business}`)} size="lg" className="w-full">
        {t("go_to_store", "Nenda Dukani Ununue")}
      </Button>
    </div>
  );
}
