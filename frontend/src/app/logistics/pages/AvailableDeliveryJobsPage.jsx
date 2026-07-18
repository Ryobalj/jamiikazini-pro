// src/app/logistics/pages/AvailableDeliveryJobsPage.jsx

import React, { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Loader2, Truck, MapPin, Package, UserPlus, PlusCircle, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useAppContext } from "@/context/AppContext";

const VEHICLE_TYPES = [
  "boda_boda",
  "bajaji",
  "suzuki_carry",
  "tuk_tuk",
  "public_transport",
  "bus",
  "canter",
  "fuso",
  "scania",
  "train",
  "ship",
  "air",
];

export default function AvailableDeliveryJobsPage() {
  const { t } = useTranslation("logistics");
  const { user } = useAppContext();

  const [loading, setLoading] = useState(true);
  const [provider, setProvider] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [verificationStatus, setVerificationStatus] = useState(null);
  const [selectedVehicle, setSelectedVehicle] = useState({});
  const [proposedFare, setProposedFare] = useState({});
  const [busyId, setBusyId] = useState(null);

  // Provider registration form
  const [regSubmitting, setRegSubmitting] = useState(false);
  const [regLocation, setRegLocation] = useState(null);

  // Vehicle registration form
  const [vehType, setVehType] = useState(VEHICLE_TYPES[0]);
  const [vehReg, setVehReg] = useState("");
  const [vehSubmitting, setVehSubmitting] = useState(false);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const providersRes = await api.get("/logistics/transport-providers/");
      const providers = Array.isArray(providersRes.data)
        ? providersRes.data
        : providersRes.data?.results || [];
      const mine = providers.find((p) => p.user?.id === user?.id) || null;
      setProvider(mine);

      if (mine) {
        const [vehiclesRes, verificationRes] = await Promise.all([
          api.get("/logistics/vehicles/"),
          api.get("/logistics/transport-verifications/").catch(() => ({ data: [] })),
        ]);
        const allVehicles = Array.isArray(vehiclesRes.data)
          ? vehiclesRes.data
          : vehiclesRes.data?.results || [];
        const myVehicles = allVehicles.filter((v) => v.provider?.id === mine.id);
        setVehicles(myVehicles);

        const verificationList = Array.isArray(verificationRes.data)
          ? verificationRes.data
          : verificationRes.data?.results || [];
        setVerificationStatus(verificationList[0]?.overall_status || null);

        if (myVehicles.length > 0) {
          const jobsRes = await api.get("/logistics/transport-requests/available/");
          setJobs(jobsRes.data || []);
        } else {
          setJobs([]);
        }
      } else {
        setVehicles([]);
        setJobs([]);
      }
    } catch {
      toast.error(t("load_failed", "Imeshindwa kupakia taarifa."));
    } finally {
      setLoading(false);
    }
  }, [user?.id, t]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (position) => setRegLocation({ lat: position.coords.latitude, lng: position.coords.longitude }),
      () => setRegLocation(null)
    );
  }, []);

  const handleRegisterProvider = async (e) => {
    e.preventDefault();
    setRegSubmitting(true);
    try {
      const payload = { provider_type: "individual" };
      if (regLocation) {
        payload.location = { type: "Point", coordinates: [regLocation.lng, regLocation.lat] };
      }
      await api.post("/logistics/transport-providers/", payload);
      toast.success(t("provider_registered", "Umejisajili kama dereva."));
      loadAll();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("provider_register_failed", "Imeshindwa kujisajili."));
    } finally {
      setRegSubmitting(false);
    }
  };

  const handleRegisterVehicle = async (e) => {
    e.preventDefault();
    if (!vehReg.trim()) return;
    setVehSubmitting(true);
    try {
      await api.post("/logistics/vehicles/", { vehicle_type: vehType, registration_number: vehReg.trim() });
      toast.success(t("vehicle_registered", "Gari limesajiliwa."));
      setVehReg("");
      loadAll();
    } catch (err) {
      const detail = err.response?.data?.registration_number || err.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("vehicle_register_failed", "Imeshindwa kusajili gari."));
    } finally {
      setVehSubmitting(false);
    }
  };

  const matchingVehicles = (vehicleType) => vehicles.filter((v) => v.vehicle_type === vehicleType && v.is_active);

  const handleAccept = async (job) => {
    const vehicleId = selectedVehicle[job.id] || matchingVehicles(job.suggested_transport_type)[0]?.id;
    if (!vehicleId) {
      toast.error(t("no_matching_vehicle", "Huna gari linalolingana na aina hii."));
      return;
    }
    setBusyId(job.id);
    try {
      await api.post(`/logistics/assignments/assign-request/${job.id}/`, { vehicle: vehicleId });
      toast.success(t("accept_success", "Umekubali kazi hii ya usafirishaji."));
      loadAll();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("accept_failed", "Imeshindwa kukubali kazi hii."));
    } finally {
      setBusyId(null);
    }
  };

  const handlePropose = async (job) => {
    const vehicleId = selectedVehicle[job.id] || matchingVehicles(job.suggested_transport_type)[0]?.id;
    const fare = proposedFare[job.id];
    if (!vehicleId) {
      toast.error(t("no_matching_vehicle", "Huna gari linalolingana na aina hii."));
      return;
    }
    if (!fare || Number(fare) <= 0) {
      toast.error(t("enter_fare", "Weka bei unayopendekeza."));
      return;
    }
    setBusyId(job.id);
    try {
      await api.post("/logistics/fare-proposals/", {
        transport_request: job.id,
        vehicle: vehicleId,
        proposed_fare: fare,
      });
      toast.success(t("propose_success", "Umetuma pendekezo la bei."));
      setProposedFare((prev) => ({ ...prev, [job.id]: "" }));
    } catch (err) {
      const detail = err.response?.data?.detail || err.response?.data?.vehicle;
      toast.error(typeof detail === "string" ? detail : t("propose_failed", "Imeshindwa kutuma pendekezo."));
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

  if (!provider) {
    return (
      <div className="max-w-md mx-auto p-4 sm:p-6">
        <Card>
          <CardContent className="p-6 text-center space-y-4">
            <UserPlus className="w-10 h-10 mx-auto text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t("become_driver_title", "Kuwa Dereva wa Jamiikazini")}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("become_driver_desc", "Jisajili kama mtoa huduma wa usafirishaji ili uanze kupokea kazi za kufikisha bidhaa.")}
            </p>
            <form onSubmit={handleRegisterProvider}>
              <Button type="submit" disabled={regSubmitting} className="w-full">
                {regSubmitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                {t("register_now", "Jisajili Sasa")}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (vehicles.length === 0) {
    return (
      <div className="max-w-md mx-auto p-4 sm:p-6">
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="text-center">
              <PlusCircle className="w-10 h-10 mx-auto text-blue-600 mb-2" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {t("add_vehicle_title", "Ongeza Gari Lako")}
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t("add_vehicle_desc", "Unahitaji kusajili gari kabla ya kuanza kupokea kazi za usafirishaji.")}
              </p>
            </div>
            <form onSubmit={handleRegisterVehicle} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t("vehicle_type", "Aina ya Gari")}
                </label>
                <select
                  value={vehType}
                  onChange={(e) => setVehType(e.target.value)}
                  className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                >
                  {VEHICLE_TYPES.map((vt) => (
                    <option key={vt} value={vt}>{t(`vehicle_types.${vt}`, vt)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t("registration_number", "Namba ya Usajili")}
                </label>
                <input
                  type="text"
                  value={vehReg}
                  onChange={(e) => setVehReg(e.target.value)}
                  placeholder={t("registration_number_placeholder", "Mfano: T123ABC")}
                  className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                  required
                />
              </div>
              <Button type="submit" disabled={vehSubmitting} className="w-full">
                {vehSubmitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                {t("add_vehicle_submit", "Sajili Gari")}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-center gap-2">
        <Truck className="w-5 h-5 text-blue-600" />
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("available_jobs_title", "Kazi za Usafirishaji Zilizo Wazi")}
        </h1>
      </div>

      {verificationStatus !== "VERIFIED" && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 text-sm">
          <ShieldAlert className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            {t("driver_verification_required", "Lazima ukamilishe uthibitisho wako kabla ya kupokea kazi.")}{" "}
            <Link to="/logistics/verify" className="underline font-medium">
              {t("verify_now", "Thibitisha Sasa")}
            </Link>
          </div>
        </div>
      )}

      {jobs.length === 0 ? (
        <div className="text-center py-16 text-gray-400 dark:text-gray-500">
          <Package className="w-10 h-10 mx-auto mb-2" />
          <p>{t("no_jobs", "Hakuna kazi za usafirishaji kwa sasa.")}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => {
            const options = matchingVehicles(job.suggested_transport_type);
            return (
              <Card key={job.id}>
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {job.package_description || t("no_description", "Bila maelezo")}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {t("vehicle_type_label", "Aina")}: {t(`vehicle_types.${job.suggested_transport_type}`, job.suggested_transport_type)}
                        {job.weight_kg ? ` · ${job.weight_kg}kg` : ""}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1 mt-1">
                        <MapPin className="w-3 h-3" /> {job.pickup_address_text} → {job.dropoff_address_text}
                      </p>
                    </div>
                    {job.estimated_fare != null && (
                      <span className="text-sm font-semibold text-green-600 dark:text-green-400 whitespace-nowrap">
                        {job.estimated_fare}
                      </span>
                    )}
                  </div>

                  {options.length > 1 && (
                    <select
                      value={selectedVehicle[job.id] || options[0]?.id}
                      onChange={(e) =>
                        setSelectedVehicle((prev) => ({ ...prev, [job.id]: e.target.value }))
                      }
                      className="w-full p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm text-gray-900 dark:text-white"
                    >
                      {options.map((v) => (
                        <option key={v.id} value={v.id}>{v.registration_number}</option>
                      ))}
                    </select>
                  )}

                  <div className="flex flex-col sm:flex-row gap-2">
                    <Button
                      onClick={() => handleAccept(job)}
                      disabled={busyId === job.id}
                      className="flex-1 bg-green-600 hover:bg-green-700"
                    >
                      {busyId === job.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("accept_job", "Kubali Kazi")}
                    </Button>
                    <div className="flex gap-2 flex-1">
                      <input
                        type="number"
                        min="1"
                        placeholder={t("your_fare", "Bei yako")}
                        value={proposedFare[job.id] || ""}
                        onChange={(e) =>
                          setProposedFare((prev) => ({ ...prev, [job.id]: e.target.value }))
                        }
                        className="w-full p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm text-gray-900 dark:text-white"
                      />
                      <Button
                        variant="secondary"
                        onClick={() => handlePropose(job)}
                        disabled={busyId === job.id}
                      >
                        {t("propose", "Pendekeza")}
                      </Button>
                    </div>
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
