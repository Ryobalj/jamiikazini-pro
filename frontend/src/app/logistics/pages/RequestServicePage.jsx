// src/app/logistics/pages/RequestServicePage.jsx
//
// Standalone transport request - "I need a boda-boda/lorry from A to B right
// now", with no product purchase behind it. Mirrors the delivery step already
// built into CheckoutBusinessSection.jsx (pickup/dropoff, weight/volume,
// vehicle-type quotes), but pickup is also chosen by the buyer (not a
// business's fixed location) and submission creates a TransportRequest
// directly instead of riding along with an Order.

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Loader2, MapPin, Truck, ShieldAlert, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";
import LocationPicker from "@/components/LocationPicker";

const ASSIGNMENT_STATUS_KEYS = {
  ASSIGNED: "assignment_status_assigned",
  IN_TRANSIT: "assignment_status_in_transit",
  DELIVERED: "assignment_status_delivered",
  COMPLETED: "assignment_status_completed",
  CANCELLED: "assignment_status_cancelled",
};

export default function RequestServicePage() {
  const { t } = useTranslation("logistics");
  const { formatCurrency } = useCurrency();

  const [isIdentityVerified, setIsIdentityVerified] = useState(true);
  const [pickupLat, setPickupLat] = useState(null);
  const [pickupLng, setPickupLng] = useState(null);
  const [dropoffLat, setDropoffLat] = useState(null);
  const [dropoffLng, setDropoffLng] = useState(null);
  const [pickupAddress, setPickupAddress] = useState("");
  const [dropoffAddress, setDropoffAddress] = useState("");
  const [description, setDescription] = useState("");
  const [weightKg, setWeightKg] = useState("5");
  const [volumeCbm, setVolumeCbm] = useState("");
  const [quotes, setQuotes] = useState([]);
  const [loadingQuotes, setLoadingQuotes] = useState(false);
  const [selectedVehicleType, setSelectedVehicleType] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [activeRequest, setActiveRequest] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [approvingId, setApprovingId] = useState(null);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    api
      .get("/auth/me/")
      .then((res) => setIsIdentityVerified(!!res.data?.is_identity_verified))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (pickupLat == null || pickupLng == null || dropoffLat == null || dropoffLng == null) return;
    setLoadingQuotes(true);
    api
      .get("/logistics/delivery-quote/", {
        params: {
          pickup_lat: pickupLat,
          pickup_lng: pickupLng,
          dropoff_lat: dropoffLat,
          dropoff_lng: dropoffLng,
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
  }, [pickupLat, pickupLng, dropoffLat, dropoffLng, weightKg, volumeCbm]);

  // Poll the active request for status/assignment updates once created.
  useEffect(() => {
    if (!activeRequest) return;
    const load = () => {
      api
        .get(`/logistics/transport-requests/${activeRequest.id}/`)
        .then((res) => setActiveRequest(res.data))
        .catch(() => {});
      if (!activeRequest.assignment) {
        api
          .get(`/logistics/transport-requests/${activeRequest.id}/fare-proposals/`)
          .then((res) => setProposals(res.data || []))
          .catch(() => {});
      }
    };
    const interval = setInterval(load, 6000);
    return () => clearInterval(interval);
  }, [activeRequest]);

  const selectedQuote = quotes.find((q) => q.vehicle_type === selectedVehicleType);

  const handleSubmit = async () => {
    if (pickupLat == null || dropoffLat == null) {
      toast.error(t("request_service.locations_required", "Chagua eneo la kuchukua na kupokelea."));
      return;
    }
    if (!selectedVehicleType) {
      toast.error(t("request_service.vehicle_required", "Chagua aina ya usafiri."));
      return;
    }
    if (!description.trim()) {
      toast.error(t("request_service.description_required", "Eleza kitu unachohitaji kusafirishwa."));
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post("/logistics/transport-requests/", {
        package_description: description.trim(),
        weight_kg: weightKg ? Number(weightKg) : 5,
        volume_cbm: volumeCbm ? Number(volumeCbm) : undefined,
        suggested_transport_type: selectedVehicleType,
        pickup_location: { type: "Point", coordinates: [pickupLng, pickupLat] },
        dropoff_location: { type: "Point", coordinates: [dropoffLng, dropoffLat] },
        pickup_address_text: pickupAddress,
        dropoff_address_text: dropoffAddress,
      });
      setActiveRequest(res.data);
      toast.success(t("request_service.created", "Ombi lako la usafiri limetumwa - tunatafuta dereva."));
    } catch (error) {
      const detail =
        error.response?.data?.payment ||
        error.response?.data?.suggested_transport_type ||
        error.response?.data?.detail ||
        t("request_service.failed", "Imeshindwa kutuma ombi. Jaribu tena.");
      toast.error(typeof detail === "string" ? detail : t("request_service.failed", "Imeshindwa kutuma ombi. Jaribu tena."));
    } finally {
      setSubmitting(false);
    }
  };

  const handleApproveProposal = async (proposalId) => {
    setApprovingId(proposalId);
    try {
      await api.post(`/logistics/fare-proposals/${proposalId}/approve/`);
      toast.success(t("request_service.proposal_approved", "Umekubali pendekezo la bei."));
      const res = await api.get(`/logistics/transport-requests/${activeRequest.id}/`);
      setActiveRequest(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || t("request_service.proposal_approve_failed", "Imeshindwa kukubali pendekezo."));
    } finally {
      setApprovingId(null);
    }
  };

  const handleConfirmReceipt = async () => {
    if (!activeRequest?.assignment?.id) return;
    setConfirming(true);
    try {
      await api.post(`/logistics/assignments/${activeRequest.assignment.id}/confirm-receipt/`);
      toast.success(t("request_service.confirm_success", "Umethibitisha kupokea. Asante!"));
      const res = await api.get(`/logistics/transport-requests/${activeRequest.id}/`);
      setActiveRequest(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || t("request_service.confirm_failed", "Imeshindwa kuthibitisha."));
    } finally {
      setConfirming(false);
    }
  };

  if (activeRequest) {
    const assignment = activeRequest.assignment;
    const canConfirmReceipt = assignment?.assignment_status === "DELIVERED" && !assignment?.client_confirmed_at;

    return (
      <div className="max-w-xl mx-auto p-4 sm:p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Truck className="w-5 h-5 text-blue-600" />
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">
            {t("request_service.title", "Omba Huduma ya Usafiri")}
          </h1>
        </div>
        <Card>
          <CardContent className="p-4 space-y-3">
            <p className="text-sm text-gray-700 dark:text-gray-300">{activeRequest.package_description}</p>
            {activeRequest.estimated_fare && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t("request_service.fare_label", "Bei")}: {formatCurrency(activeRequest.estimated_fare)}
              </p>
            )}
            {!assignment ? (
              <div className="space-y-3">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t("request_service.waiting_driver", "Tunasubiri dereva akubali kukufikishia.")}
                </p>
                {proposals.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-300">
                      {t("request_service.proposals_heading", "Mapendekezo ya Bei kutoka kwa Madereva")}
                    </p>
                    {proposals.map((p) => (
                      <div key={p.id} className="flex items-center justify-between p-2 rounded-lg border border-gray-100 dark:border-gray-800">
                        <div className="text-sm">
                          <p className="text-gray-900 dark:text-white font-medium">{formatCurrency(p.proposed_fare)}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {p.provider_name} · {t(`vehicle_types.${p.vehicle_type}`, p.vehicle_type)}
                          </p>
                        </div>
                        {p.status === "PENDING" && (
                          <Button size="sm" onClick={() => handleApproveProposal(p.id)} disabled={approvingId === p.id}>
                            {approvingId === p.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("request_service.approve", "Kubali")}
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-2 text-sm">
                <p className="text-gray-700 dark:text-gray-300">
                  {t("request_service.status_label", "Hali")}:{" "}
                  <span className="font-medium">
                    {t(ASSIGNMENT_STATUS_KEYS[assignment.assignment_status] || assignment.assignment_status, assignment.assignment_status)}
                  </span>
                </p>
                {assignment.provider_name && (
                  <p className="text-gray-500 dark:text-gray-400">
                    {t("request_service.driver_label", "Dereva")}: {assignment.provider_name} {assignment.vehicle ? `(${assignment.vehicle})` : ""}
                  </p>
                )}
                {assignment.assignment_status === "DELIVERED" && assignment.client_confirmed_at && (
                  <p className="flex items-center gap-1 text-green-600 dark:text-green-400">
                    <CheckCircle2 className="w-4 h-4" /> {t("request_service.already_confirmed", "Umeshathibitisha kupokea.")}
                  </p>
                )}
                {canConfirmReceipt && (
                  <Button onClick={handleConfirmReceipt} disabled={confirming} className="w-full mt-2">
                    {confirming ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                    {t("request_service.confirm_receipt", "Nimepokea")}
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-center gap-2">
        <Truck className="w-5 h-5 text-blue-600" />
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("request_service.title", "Omba Huduma ya Usafiri")}
        </h1>
      </div>

      {!isIdentityVerified && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 text-sm">
          <ShieldAlert className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            {t("request_service.verification_required", "Lazima uthibitishe kitambulisho chako kabla ya kuomba huduma hii.")}{" "}
            <Link to="/verify-identity" className="underline font-medium">
              {t("driver.verify", "Verify Now")}
            </Link>
          </div>
        </div>
      )}

      <Card>
        <CardHeader title={t("request_service.pickup_heading", "Eneo la Kuchukua")} icon={<MapPin className="w-4 h-4" />} />
        <CardContent className="space-y-3">
          <LocationPicker lat={pickupLat} lon={pickupLng} setLat={setPickupLat} setLon={setPickupLng} />
          <input
            type="text"
            value={pickupAddress}
            onChange={(e) => setPickupAddress(e.target.value)}
            placeholder={t("request_service.address_placeholder", "Maelezo ya anwani (hiari)")}
            className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader title={t("request_service.dropoff_heading", "Eneo la Kupokelea")} icon={<MapPin className="w-4 h-4" />} />
        <CardContent className="space-y-3">
          <LocationPicker lat={dropoffLat} lon={dropoffLng} setLat={setDropoffLat} setLon={setDropoffLng} />
          <input
            type="text"
            value={dropoffAddress}
            onChange={(e) => setDropoffAddress(e.target.value)}
            placeholder={t("request_service.address_placeholder", "Maelezo ya anwani (hiari)")}
            className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
          />
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4 space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t("request_service.description_label", "Ni Nini Unachohitaji Kusafirisha?")}
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder={t("request_service.description_placeholder", "Mfano: masanduku 3 ya nguo")}
              className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("weight_label", "Uzito (kg)")}
              </label>
              <input
                type="number"
                min="0"
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
                className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("request_service.volume_label", "Ujazo (m³, hiari)")}
              </label>
              <input
                type="number"
                min="0"
                step="0.1"
                value={volumeCbm}
                onChange={(e) => setVolumeCbm(e.target.value)}
                className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t("vehicle_type_label", "Chagua Aina ya Usafiri")}
            </label>
            {loadingQuotes ? (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin" /> {t("request_service.loading_quotes", "Inakokotoa bei...")}
              </div>
            ) : quotes.length === 0 ? (
              <p className="text-sm text-gray-400">
                {t("request_service.no_quotes", "Chagua eneo la kuchukua na kupokelea kuona bei.")}
              </p>
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
                    <span className="font-semibold text-gray-900 dark:text-white">{formatCurrency(q.estimated_fare)}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {selectedQuote && (
            <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-700">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {t("request_service.fare_to_hold", "Bei Itakayoshikiliwa")}
              </span>
              <span className="text-lg font-bold text-gray-900 dark:text-white">{formatCurrency(selectedQuote.estimated_fare)}</span>
            </div>
          )}
        </CardContent>
      </Card>

      <Button
        onClick={handleSubmit}
        disabled={submitting || !isIdentityVerified || !selectedVehicleType || pickupLat == null || dropoffLat == null}
        className="w-full"
        size="lg"
      >
        {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
        {t("request_service.submit", "Tuma Ombi")}
      </Button>
    </div>
  );
}
