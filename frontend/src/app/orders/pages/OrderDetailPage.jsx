// src/app/orders/pages/OrderDetailPage.jsx

import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Loader2, Package, Truck, CheckCircle2, XCircle, Store } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";
import DeliveryTrackingMap from "@/app/logistics/components/DeliveryTrackingMap";

const POLL_INTERVAL_MS = 6000;

const ASSIGNMENT_STATUS_KEYS = {
  ASSIGNED: "assignment_status_assigned",
  IN_TRANSIT: "assignment_status_in_transit",
  DELIVERED: "assignment_status_delivered",
  COMPLETED: "assignment_status_completed",
  CANCELLED: "assignment_status_cancelled",
};

export default function OrderDetailPage() {
  const { id } = useParams();
  const { t } = useTranslation("orders");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();

  const [order, setOrder] = useState(null);
  const [transportRequest, setTransportRequest] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [approvingId, setApprovingId] = useState(null);
  const [markingCash, setMarkingCash] = useState(false);

  const load = useCallback(async () => {
    try {
      const orderRes = await api.get(`/orders/${id}/`);
      setOrder(orderRes.data);

      if (orderRes.data.fulfillment_type === "DELIVERY") {
        const trRes = await api.get(`/logistics/transport-requests/by-order/${id}/`);
        setTransportRequest(trRes.data);

        if (trRes.data && !trRes.data.assignment && trRes.data.status === "pending") {
          const proposalsRes = await api.get(`/logistics/transport-requests/${trRes.data.id}/fare-proposals/`);
          setProposals(proposalsRes.data || []);
        } else {
          setProposals([]);
        }
      }
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
    const interval = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [load]);

  const handleConfirmReceipt = async () => {
    if (!transportRequest?.assignment?.id) return;
    setConfirming(true);
    try {
      await api.post(`/logistics/assignments/${transportRequest.assignment.id}/confirm-receipt/`);
      toast.success(t("confirm_success", "Umethibitisha kupokea bidhaa. Asante!"));
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("confirm_failed", "Imeshindwa kuthibitisha."));
    } finally {
      setConfirming(false);
    }
  };

  const handleMarkCashReceived = async () => {
    setMarkingCash(true);
    try {
      await api.post(`/orders/${id}/mark-cash-received/`);
      toast.success(t("cash_received_success", "Umethibitisha kupokea malipo taslimu."));
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("cash_received_failed", "Imeshindwa kuthibitisha malipo."));
    } finally {
      setMarkingCash(false);
    }
  };

  const handleApproveProposal = async (proposalId) => {
    setApprovingId(proposalId);
    try {
      await api.post(`/logistics/fare-proposals/${proposalId}/approve/`);
      toast.success(t("proposal_approved", "Umekubali pendekezo la bei."));
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("proposal_approve_failed", "Imeshindwa kukubali pendekezo."));
    } finally {
      setApprovingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="max-w-md mx-auto p-6 text-center py-20">
        <XCircle className="w-14 h-14 text-red-400 mx-auto mb-4" />
        <p className="text-gray-500 dark:text-gray-400 mb-6">
          {t("load_failed", "Imeshindwa kupata taarifa za order hii.")}
        </p>
        <Button onClick={() => navigate("/")}>{t("go_home", "Rudi Mwanzo")}</Button>
      </div>
    );
  }

  const assignment = transportRequest?.assignment;
  const canConfirmReceipt =
    order.payment_status === "HELD" &&
    assignment?.assignment_status === "DELIVERED" &&
    !assignment?.client_confirmed_at;

  return (
    <div className="max-w-xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-center gap-2">
        <Package className="w-5 h-5 text-blue-600" />
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("title", "Maelezo ya Order")}
        </h1>
      </div>

      <Card>
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
              <Store className="w-4 h-4" /> {order.business_name}
            </div>
            <span className="text-xs font-medium px-2 py-1 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300">
              {t(`order_status_${order.status?.toLowerCase()}`, order.status)}
            </span>
          </div>

          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {order.items?.map((item) => (
              <div key={item.id} className="py-2 flex items-center justify-between text-sm">
                <span className="text-gray-700 dark:text-gray-300">
                  {item.product_name || item.service_name} × {item.quantity}
                  {item.unit && item.unit !== "pcs" ? ` ${item.unit}` : ""}
                </span>
                <span className="text-gray-900 dark:text-white font-medium">
                  {formatCurrency(item.total_price)}
                </span>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-gray-100 dark:border-gray-800 space-y-1 text-sm">
            {order.fulfillment_type === "DELIVERY" && Number(order.delivery_fee) > 0 && (
              <div className="flex justify-between text-gray-500 dark:text-gray-400">
                <span>{t("delivery_fee", "Gharama ya Usafiri")}</span>
                <span>{formatCurrency(order.delivery_fee)}</span>
              </div>
            )}
            <div className="flex justify-between font-semibold text-gray-900 dark:text-white">
              <span>{t("total", "Jumla")}</span>
              <span>{formatCurrency(order.total_amount)}</span>
            </div>
            <div className="flex justify-between text-xs text-gray-400 dark:text-gray-500">
              <span>{t("payment_status", "Hali ya Malipo")}</span>
              <span>{t(`payment_status_${order.payment_status?.toLowerCase()}`, order.payment_status)}</span>
            </div>
          </div>

          {order.can_mark_cash_received && (
            <Button onClick={handleMarkCashReceived} disabled={markingCash} className="w-full mt-2">
              {markingCash ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {t("mark_cash_received", "Nimepokea Fedha Taslimu")}
            </Button>
          )}
        </CardContent>
      </Card>

      {order.fulfillment_type === "DELIVERY" && (
        <Card>
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Truck className="w-4 h-4 text-blue-600" />
              <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
                {t("delivery_heading", "Hali ya Usafirishaji")}
              </h2>
            </div>

            {!transportRequest ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t("delivery_pending", "Tunatafuta dereva wa kukufikishia bidhaa...")}
              </p>
            ) : assignment ? (
              <div className="space-y-2 text-sm">
                <p className="text-gray-700 dark:text-gray-300">
                  {t("assignment_status_label", "Hali")}:{" "}
                  <span className="font-medium">
                    {t(ASSIGNMENT_STATUS_KEYS[assignment.assignment_status] || assignment.assignment_status, assignment.assignment_status)}
                  </span>
                </p>
                {assignment.provider_name && (
                  <p className="text-gray-500 dark:text-gray-400">
                    {t("driver_label", "Dereva")}: {assignment.provider_name} {assignment.vehicle ? `(${assignment.vehicle})` : ""}
                  </p>
                )}
                {assignment.agreed_fare != null && (
                  <p className="text-gray-500 dark:text-gray-400">
                    {t("agreed_fare_label", "Bei ya Usafiri")}: {formatCurrency(assignment.agreed_fare)}
                  </p>
                )}

                {assignment.assignment_status === "IN_TRANSIT" && (
                  <div className="pt-2 space-y-1">
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-300">
                      {t("tracking_heading", "Fuatilia Usafirishaji")}
                    </p>
                    <DeliveryTrackingMap
                      pickupLocation={transportRequest?.pickup_location}
                      dropoffLocation={transportRequest?.dropoff_location}
                      courierLocation={assignment.current_location}
                    />
                  </div>
                )}

                {assignment.assignment_status === "DELIVERED" && assignment.client_confirmed_at && (
                  <p className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                    <CheckCircle2 className="w-4 h-4" /> {t("already_confirmed", "Umeshathibitisha kupokea.")}
                  </p>
                )}

                {canConfirmReceipt && (
                  <Button onClick={handleConfirmReceipt} disabled={confirming} className="w-full mt-2">
                    {confirming ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                    {t("confirm_receipt", "Nimepokea Bidhaa")}
                  </Button>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t("waiting_driver", "Tunasubiri dereva akubali kukufikishia bidhaa.")}
                </p>
                {proposals.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-300">
                      {t("proposals_heading", "Mapendekezo ya Bei kutoka kwa Madereva")}
                    </p>
                    {proposals.map((p) => (
                      <div
                        key={p.id}
                        className="flex items-center justify-between p-2 rounded-lg border border-gray-100 dark:border-gray-800"
                      >
                        <div className="text-sm">
                          <p className="text-gray-900 dark:text-white font-medium">
                            {formatCurrency(p.proposed_fare)}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {p.provider_name} · {t(`vehicle_types.${p.vehicle_type}`, p.vehicle_type)}
                          </p>
                        </div>
                        {p.status === "PENDING" && (
                          <Button
                            size="sm"
                            onClick={() => handleApproveProposal(p.id)}
                            disabled={approvingId === p.id}
                          >
                            {approvingId === p.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("approve", "Kubali")}
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
