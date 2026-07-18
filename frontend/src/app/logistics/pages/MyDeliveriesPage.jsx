// src/app/logistics/pages/MyDeliveriesPage.jsx

import React, { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Loader2, Truck, MapPin, PackageCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";

const STATUS_LABELS = {
  ASSIGNED: "status_assigned",
  IN_TRANSIT: "status_in_transit",
  DELIVERED: "status_delivered",
  COMPLETED: "status_completed",
  CANCELLED: "status_cancelled",
};

const STATUS_COLORS = {
  ASSIGNED: "text-gray-500",
  IN_TRANSIT: "text-blue-600",
  DELIVERED: "text-amber-600",
  COMPLETED: "text-green-600",
  CANCELLED: "text-red-500",
};

export default function MyDeliveriesPage() {
  const { t } = useTranslation("logistics");

  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  const pushLocation = useCallback((inTransitIds) => {
    if (!navigator.geolocation || inTransitIds.length === 0) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        inTransitIds.forEach((id) => {
          api
            .post(`/logistics/assignments/${id}/update-location/`, {
              current_location: { type: "Point", coordinates: [longitude, latitude] },
            })
            .catch(() => {
              // fail silently if the update can't be posted
            });
        });
      },
      () => {
        // fail silently if no GPS
      }
    );
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    api
      .get("/logistics/assignments/")
      .then((res) => {
        const data = Array.isArray(res.data) ? res.data : res.data?.results || [];
        setAssignments(data);
        const inTransitIds = data.filter((a) => a.assignment_status === "IN_TRANSIT").map((a) => a.id);
        pushLocation(inTransitIds);
      })
      .catch(() => setAssignments([]))
      .finally(() => setLoading(false));
  }, [pushLocation]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, [load]);

  const handleAction = async (assignment, action) => {
    setBusyId(assignment.id);
    try {
      await api.post(`/logistics/assignments/${assignment.id}/${action}/`);
      toast.success(t("status_updated", "Hali ya usafirishaji imesasishwa."));
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("status_update_failed", "Imeshindwa kusasisha hali."));
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-center gap-2">
        <Truck className="w-5 h-5 text-blue-600" />
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("my_deliveries_title", "Usafirishaji Wangu")}
        </h1>
      </div>

      {assignments.length === 0 ? (
        <div className="text-center py-16 text-gray-400 dark:text-gray-500">
          <PackageCheck className="w-10 h-10 mx-auto mb-2" />
          <p>{t("no_deliveries", "Huna usafirishaji wowote kwa sasa.")}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {assignments.map((a) => (
            <Card key={a.id}>
              <CardContent className="p-4 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className={`text-sm font-semibold ${STATUS_COLORS[a.assignment_status] || "text-gray-500"}`}>
                      {t(STATUS_LABELS[a.assignment_status] || a.assignment_status, a.assignment_status)}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1 mt-1">
                      <MapPin className="w-3 h-3" /> {a.vehicle}
                    </p>
                  </div>
                  {a.agreed_fare != null && (
                    <span className="text-sm font-semibold text-green-600 dark:text-green-400 whitespace-nowrap">
                      {a.agreed_fare}
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap gap-2">
                  {a.assignment_status === "ASSIGNED" && (
                    <Button
                      size="sm"
                      onClick={() => handleAction(a, "mark-in-transit")}
                      disabled={busyId === a.id}
                    >
                      {busyId === a.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("mark_in_transit", "Anza Safari")}
                    </Button>
                  )}
                  {a.assignment_status === "IN_TRANSIT" && (
                    <Button
                      size="sm"
                      className="bg-green-600 hover:bg-green-700"
                      onClick={() => handleAction(a, "mark-delivered")}
                      disabled={busyId === a.id}
                    >
                      {busyId === a.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("mark_delivered", "Nimefikisha")}
                    </Button>
                  )}
                  {a.assignment_status === "DELIVERED" && (
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t("waiting_client_confirmation", "Inasubiri mnunuzi kuthibitisha kupokea.")}
                    </p>
                  )}
                  {["ASSIGNED", "IN_TRANSIT"].includes(a.assignment_status) && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => handleAction(a, "cancel")}
                      disabled={busyId === a.id}
                    >
                      {t("cancel", "Ghairi")}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
