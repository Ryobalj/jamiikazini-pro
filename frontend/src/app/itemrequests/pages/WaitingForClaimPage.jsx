// src/app/itemrequests/pages/WaitingForClaimPage.jsx

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Loader2, XCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import api from "@/lib/axios";

const POLL_INTERVAL_MS = 4000;

export default function WaitingForClaimPage() {
  const { id } = useParams();
  const { t } = useTranslation("itemrequests");
  const navigate = useNavigate();
  const [itemRequest, setItemRequest] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let timer;

    const poll = async () => {
      try {
        const res = await api.get(`/item-requests/${id}/`);
        if (cancelled) return;
        setItemRequest(res.data);
        if (res.data.status === "CLAIMED") {
          navigate(`/request-item/${id}/claimed`, { replace: true });
          return;
        }
        const isExpired = res.data.expires_at && new Date(res.data.expires_at) < new Date();
        if (res.data.status === "PENDING" && !isExpired) {
          timer = setTimeout(poll, POLL_INTERVAL_MS);
        }
      } catch {
        if (!cancelled) setError(true);
      }
    };
    poll();

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [id, navigate]);

  if (error) {
    return (
      <div className="max-w-md mx-auto p-6 text-center py-20">
        <XCircle className="w-14 h-14 text-red-400 mx-auto mb-4" />
        <p className="text-gray-500 dark:text-gray-400 mb-6">
          {t("waiting_error", "Imeshindwa kupata taarifa za ombi lako.")}
        </p>
        <Button onClick={() => navigate("/request-item")}>
          {t("try_again", "Jaribu Tena")}
        </Button>
      </div>
    );
  }

  const clientSideExpired =
    itemRequest?.status === "PENDING" &&
    itemRequest?.expires_at &&
    new Date(itemRequest.expires_at) < new Date();

  if (itemRequest?.status === "EXPIRED" || itemRequest?.status === "CANCELLED" || clientSideExpired) {
    return (
      <div className="max-w-md mx-auto p-6 text-center py-20">
        <XCircle className="w-14 h-14 text-amber-400 mx-auto mb-4" />
        <p className="text-gray-700 dark:text-gray-300 font-medium mb-2">
          {t("no_response_title", "Hakuna duka lililokubali kwa wakati")}
        </p>
        <p className="text-gray-500 dark:text-gray-400 mb-6">
          {t("no_response_desc", "Jaribu tena kwa eneo pana zaidi au bidhaa tofauti kidogo.")}
        </p>
        <Button onClick={() => navigate("/request-item")}>
          <RotateCcw className="w-4 h-4 mr-2" /> {t("try_again", "Jaribu Tena")}
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto p-6 text-center py-20">
      <Loader2 className="w-14 h-14 text-blue-600 animate-spin mx-auto mb-4" />
      <p className="text-gray-700 dark:text-gray-300 font-medium mb-2">
        {t("waiting_title", "Tunatuma ombi lako kwa maduka ya karibu...")}
      </p>
      <p className="text-gray-500 dark:text-gray-400">
        {t("waiting_desc", "Subiri kidogo - duka la kwanza kukubali litakuhudumia.")}
      </p>
      {itemRequest?.matched_products_count != null && (
        <p className="text-xs text-gray-400 mt-4">
          {t("matched_count", "Maduka {{count}} yanayoweza kuwa na bidhaa hiyo yamearifiwa.", {
            count: itemRequest.matched_products_count,
          })}
        </p>
      )}
    </div>
  );
}
