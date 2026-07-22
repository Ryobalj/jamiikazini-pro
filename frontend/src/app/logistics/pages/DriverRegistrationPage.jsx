// src/app/logistics/pages/DriverRegistrationPage.jsx
//
// Unified, step-by-step driver/company registration: provider type ->
// driver details (license number + photo) -> vehicle details (registration
// number + photo, LATRA permit number + photo) -> bonded automatically to
// the vehicle. Once set up, shows "My Vehicles" with an explicit
// unbond/remove action - a vehicle stays bonded to its driver until this
// action is taken, never silently reassigned.

import React, { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import {
  Loader2, UserPlus, Building2, User as UserIcon, Truck, ShieldCheck,
  CheckCircle2, XCircle, ImagePlus, ArrowLeft, ShieldAlert, ShieldX,
} from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useAppContext } from "@/context/AppContext";

const VEHICLE_TYPES = [
  "bicycle", "boda_boda", "bajaji", "taxi", "suzuki_carry", "tuk_tuk",
  "public_transport", "bus", "canter", "fuso", "scania", "train", "ship", "air",
];

// Mamlaka za uthibitisho (TRA/LATRA, NTSA, URSB, n.k.) ni tofauti kwa kila
// nchi - orodha hii inaendana na gov_integration.CountryConfig.ISO_CODES.
const COUNTRIES = [
  { code: "TZ", label: "Tanzania" },
  { code: "KE", label: "Kenya" },
  { code: "UG", label: "Uganda" },
  { code: "RW", label: "Rwanda" },
  { code: "BI", label: "Burundi" },
  { code: "SS", label: "South Sudan" },
];

function StepBadge({ done, active, label, num }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`flex items-center justify-center w-6 h-6 rounded-full text-xs font-semibold flex-shrink-0 ${
          done ? "bg-green-600 text-white" : active ? "bg-blue-600 text-white" : "bg-gray-200 dark:bg-gray-700 text-gray-500"
        }`}
      >
        {done ? <CheckCircle2 className="w-4 h-4" /> : num}
      </div>
      <span className={`text-xs sm:text-sm ${active ? "font-semibold text-gray-900 dark:text-white" : "text-gray-500 dark:text-gray-400"}`}>
        {label}
      </span>
    </div>
  );
}

function FileField({ label, file, onChange, hint }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
      <label className="flex items-center gap-2 p-2.5 bg-white dark:bg-gray-800 border border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-500 dark:text-gray-400 cursor-pointer hover:border-blue-400">
        <ImagePlus className="w-4 h-4 flex-shrink-0" />
        <span className="truncate">{file ? file.name : hint}</span>
        <input type="file" accept="image/*" className="hidden" onChange={(e) => onChange(e.target.files?.[0] || null)} />
      </label>
    </div>
  );
}

export default function DriverRegistrationPage() {
  const { t } = useTranslation("logistics");
  const { user } = useAppContext();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [provider, setProvider] = useState(null);
  const [driver, setDriver] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  // Step 1: provider type
  const [providerType, setProviderType] = useState("individual");
  const [country, setCountry] = useState("TZ");
  const [companyName, setCompanyName] = useState("");
  const [companyRegNumber, setCompanyRegNumber] = useState("");
  const [regLocation, setRegLocation] = useState(null);

  // Step 2: driver details
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [licenseNumber, setLicenseNumber] = useState("");
  const [licensePhoto, setLicensePhoto] = useState(null);
  const [driverPhone, setDriverPhone] = useState("");
  const [profilePhoto, setProfilePhoto] = useState(null);

  // Step 3: vehicle details
  const [vehType, setVehType] = useState(VEHICLE_TYPES[0]);
  const [vehReg, setVehReg] = useState("");
  const [vehPhoto, setVehPhoto] = useState(null);
  const [regCardPhoto, setRegCardPhoto] = useState(null);
  const [latraNumber, setLatraNumber] = useState("");
  const [latraPhoto, setLatraPhoto] = useState(null);

  const [unbondingId, setUnbondingId] = useState(null);
  const [verifyingId, setVerifyingId] = useState(null);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const providersRes = await api.get("/logistics/transport-providers/");
      const providers = Array.isArray(providersRes.data) ? providersRes.data : providersRes.data?.results || [];
      const mine = providers.find((p) => p.user?.id === user?.id) || null;
      setProvider(mine);

      if (mine) {
        const driversRes = await api.get("/logistics/drivers/");
        const allDrivers = Array.isArray(driversRes.data) ? driversRes.data : driversRes.data?.results || [];
        const myDriver = allDrivers.find((d) => d.transport_provider === mine.id) || null;
        setDriver(myDriver);

        const vehiclesRes = await api.get("/logistics/vehicles/");
        const allVehicles = Array.isArray(vehiclesRes.data) ? vehiclesRes.data : vehiclesRes.data?.results || [];
        setVehicles(allVehicles.filter((v) => v.provider?.id === mine.id));
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
    if (providerType === "company" && !companyName.trim()) {
      toast.error(t("register.company_name_required", "Weka jina la kampuni."));
      return;
    }
    setSubmitting(true);
    try {
      const payload = { provider_type: providerType, country_code: country };
      if (providerType === "company") {
        payload.company_name = companyName.trim();
        payload.company_registration_number = companyRegNumber.trim();
      }
      if (regLocation) {
        payload.location = { type: "Point", coordinates: [regLocation.lng, regLocation.lat] };
      }
      await api.post("/logistics/transport-providers/", payload);
      toast.success(t("provider_registered", "Umejisajili kama dereva."));
      loadAll();
    } catch (err) {
      const detail = err.response?.data?.company_name || err.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("provider_register_failed", "Imeshindwa kujisajili."));
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegisterDriver = async (e) => {
    e.preventDefault();
    if (!fullName.trim() || !licenseNumber.trim()) {
      toast.error(t("register.driver_required_fields", "Jaza jina na namba ya leseni."));
      return;
    }
    setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append("full_name", fullName.trim());
      fd.append("license_number", licenseNumber.trim());
      if (driverPhone.trim()) fd.append("phone_number", driverPhone.trim());
      if (licensePhoto) fd.append("license_photo", licensePhoto);
      if (profilePhoto) fd.append("profile_image", profilePhoto);
      await api.post("/logistics/drivers/", fd);
      toast.success(t("register.driver_registered", "Taarifa zako za udereva zimehifadhiwa."));
      loadAll();
    } catch (err) {
      const detail = err.response?.data?.license_number || err.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("register.driver_register_failed", "Imeshindwa kuhifadhi taarifa za udereva."));
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegisterVehicle = async (e) => {
    e.preventDefault();
    if (!vehReg.trim()) return;
    setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append("vehicle_type", vehType);
      fd.append("registration_number", vehReg.trim());
      if (vehPhoto) fd.append("image", vehPhoto);
      if (regCardPhoto) fd.append("registration_photo", regCardPhoto);
      if (latraNumber.trim()) fd.append("latra_permit_number", latraNumber.trim());
      if (latraPhoto) fd.append("latra_permit_photo", latraPhoto);
      const res = await api.post("/logistics/vehicles/", fd);

      // Bond the driver to their first vehicle automatically - there's only
      // one driver on the account at this point, so this is an unambiguous,
      // helpful default rather than leaving the vehicle unbonded.
      if (driver?.id && res.data?.id) {
        await api.post(`/logistics/vehicles/${res.data.id}/assign-driver/`, { driver_id: driver.id });
      }

      toast.success(t("vehicle_registered", "Gari limesajiliwa na kuunganishwa na wewe."));
      setVehReg("");
      loadAll();
    } catch (err) {
      const detail = err.response?.data?.registration_number || err.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("vehicle_register_failed", "Imeshindwa kusajili gari."));
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerifyVehicle = async (vehicle) => {
    setVerifyingId(vehicle.id);
    try {
      // Bila country_code hapa - backend inatumia nchi ya mtoa-huduma mwenyewe
      // (TransportProvider.country_code) kuchagua mamlaka sahihi (TRA/LATRA,
      // NTSA, URSB, n.k.), badala ya "tz" iliyowekwa ngumu.
      const res = await api.post(`/logistics/vehicles/${vehicle.id}/verify/`, {});
      const overall = res.data?.vehicle?.verification?.overall_status;
      if (overall === "VERIFIED") {
        toast.success(t("register.vehicle_verified", "Gari limethibitishwa - linaweza kupokea kazi."));
      } else {
        toast.error(t("register.vehicle_verify_pending_or_failed", "Uthibitisho haujakamilika - kagua namba ulizoweka na ujaribu tena."));
      }
      loadAll();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("register.vehicle_verify_failed", "Imeshindwa kuthibitisha gari."));
    } finally {
      setVerifyingId(null);
    }
  };

  const handleUnbond = async (vehicle) => {
    if (!window.confirm(t("register.confirm_unbond", "Una uhakika unataka kuondoa gari hili kwenye profaili yako? Hutopokea tena kazi kwa gari hili hadi utakapolijumuisha upya."))) {
      return;
    }
    setUnbondingId(vehicle.id);
    try {
      await api.post(`/logistics/vehicles/${vehicle.id}/release-driver/`, { driver_id: driver?.id });
      toast.success(t("register.unbonded", "Gari limeondolewa kwenye profaili yako."));
      loadAll();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("register.unbond_failed", "Imeshindwa kuondoa gari."));
    } finally {
      setUnbondingId(null);
    }
  };

  const handleRebond = async (vehicle) => {
    if (!driver?.id) return;
    setUnbondingId(vehicle.id);
    try {
      await api.post(`/logistics/vehicles/${vehicle.id}/assign-driver/`, { driver_id: driver.id });
      toast.success(t("register.rebonded", "Umeunganishwa tena na gari hili."));
      loadAll();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("register.rebond_failed", "Imeshindwa kuunganisha tena."));
    } finally {
      setUnbondingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const step = !provider ? 1 : !driver ? 2 : vehicles.length === 0 ? 3 : 4;

  return (
    <div className="max-w-xl mx-auto p-4 sm:p-6 space-y-5">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("register.title", "Jisajili kama Dereva au Kampuni ya Usafirishaji")}
        </h1>
      </div>

      {/* Progress indicator */}
      <div className="flex items-center justify-between gap-1 px-1">
        <StepBadge num={1} label={t("register.step1_label", "Aina ya Mtoa Huduma")} done={step > 1} active={step === 1} />
        <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700 mx-1" />
        <StepBadge num={2} label={t("register.step2_label", "Taarifa za Dereva")} done={step > 2} active={step === 2} />
        <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700 mx-1" />
        <StepBadge num={3} label={t("register.step3_label", "Gari")} done={step > 3} active={step === 3} />
      </div>

      {/* Step 1: Provider type */}
      {step === 1 && (
        <Card>
          <CardHeader title={t("register.step1_heading", "Wewe ni Nani?")} icon={<UserPlus className="w-4 h-4" />} />
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setProviderType("individual")}
                className={`p-4 rounded-lg border-2 text-center transition ${
                  providerType === "individual" ? "border-blue-600 bg-blue-50 dark:bg-blue-900/20" : "border-gray-200 dark:border-gray-700"
                }`}
              >
                <UserIcon className="w-6 h-6 mx-auto mb-1 text-blue-600" />
                <p className="text-sm font-medium text-gray-900 dark:text-white">{t("register.individual", "Dereva Binafsi")}</p>
              </button>
              <button
                type="button"
                onClick={() => setProviderType("company")}
                className={`p-4 rounded-lg border-2 text-center transition ${
                  providerType === "company" ? "border-blue-600 bg-blue-50 dark:bg-blue-900/20" : "border-gray-200 dark:border-gray-700"
                }`}
              >
                <Building2 className="w-6 h-6 mx-auto mb-1 text-blue-600" />
                <p className="text-sm font-medium text-gray-900 dark:text-white">{t("register.company", "Kampuni ya Usafirishaji")}</p>
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("register.country_label", "Nchi")}
              </label>
              <select
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
              >
                {COUNTRIES.map((c) => (
                  <option key={c.code} value={c.code}>{c.label}</option>
                ))}
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {t("register.country_hint", "Hii inaamua mamlaka gani (TRA/LATRA, NTSA, URSB, n.k.) itakayotumika kuthibitisha wewe na magari yako.")}
              </p>
            </div>

            {providerType === "company" && (
              <div className="space-y-3 pt-2 border-t border-gray-100 dark:border-gray-700">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t("register.company_name_label", "Jina la Kampuni")}
                  </label>
                  <input
                    type="text"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t("register.company_reg_label", "Namba ya Usajili (TIN/BRELA)")}
                  </label>
                  <input
                    type="text"
                    value={companyRegNumber}
                    onChange={(e) => setCompanyRegNumber(e.target.value)}
                    placeholder={t("register.company_reg_placeholder", "Hiari - unaweza kuongeza baadaye")}
                    className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                  />
                </div>
              </div>
            )}

            <Button onClick={handleRegisterProvider} disabled={submitting} className="w-full">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {t("register_now", "Endelea")}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Driver details */}
      {step === 2 && (
        <Card>
          <CardHeader title={t("register.step2_heading", "Taarifa Zako za Udereva")} icon={<UserIcon className="w-4 h-4" />} />
          <CardContent className="space-y-3">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("register.step2_desc", "Hii ndiyo itakayoonekana kwa wateja wanapokuona dereva wa mzigo wao.")}
            </p>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t("register.full_name_label", "Jina Kamili")}</label>
              <input
                type="text" value={fullName} onChange={(e) => setFullName(e.target.value)}
                className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t("verify_driver.driver_license_label", "Namba ya Leseni ya Udereva")}</label>
              <input
                type="text" value={licenseNumber} onChange={(e) => setLicenseNumber(e.target.value)}
                className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                required
              />
            </div>
            <FileField
              label={t("register.license_photo_label", "Picha ya Leseni")}
              file={licensePhoto}
              onChange={setLicensePhoto}
              hint={t("register.upload_hint", "Bofya kupakia picha")}
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t("register.phone_label", "Namba ya Simu (hiari)")}</label>
              <input
                type="text" value={driverPhone} onChange={(e) => setDriverPhone(e.target.value)}
                className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
              />
            </div>
            <FileField
              label={t("register.profile_photo_label", "Picha Yako (hiari)")}
              file={profilePhoto}
              onChange={setProfilePhoto}
              hint={t("register.upload_hint", "Bofya kupakia picha")}
            />
            <Button onClick={handleRegisterDriver} disabled={submitting} className="w-full">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {t("register_now", "Endelea")}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Vehicle details */}
      {step === 3 && (
        <Card>
          <CardHeader title={t("add_vehicle_title", "Ongeza Gari Lako")} icon={<Truck className="w-4 h-4" />} />
          <CardContent className="space-y-3">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("register.step3_desc", "Gari hili litaunganishwa moja kwa moja na wewe kama dereva wake.")}
            </p>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t("vehicle_type", "Aina ya Gari")}</label>
              <select
                value={vehType} onChange={(e) => setVehType(e.target.value)}
                className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
              >
                {VEHICLE_TYPES.map((vt) => (
                  <option key={vt} value={vt}>{t(`vehicle_types.${vt}`, vt)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t("registration_number", "Namba ya Usajili")}</label>
              <input
                type="text" value={vehReg} onChange={(e) => setVehReg(e.target.value)}
                placeholder={t("registration_number_placeholder", "Mfano: T123ABC")}
                className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                required
              />
            </div>
            <FileField
              label={t("register.vehicle_photo_label", "Picha ya Gari (hiari)")}
              file={vehPhoto} onChange={setVehPhoto}
              hint={t("register.upload_hint", "Bofya kupakia picha")}
            />
            <FileField
              label={t("register.reg_card_photo_label", "Picha ya Cheti cha Usajili")}
              file={regCardPhoto} onChange={setRegCardPhoto}
              hint={t("register.upload_hint", "Bofya kupakia picha")}
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t("verify_driver.latra_label", "Namba ya Leseni ya LATRA")}</label>
              <input
                type="text" value={latraNumber} onChange={(e) => setLatraNumber(e.target.value)}
                placeholder={t("register.latra_placeholder", "Hiari - kwa gari linalotumika kibiashara")}
                className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
              />
            </div>
            <FileField
              label={t("register.latra_photo_label", "Picha ya Kibali cha LATRA (hiari)")}
              file={latraPhoto} onChange={setLatraPhoto}
              hint={t("register.upload_hint", "Bofya kupakia picha")}
            />
            <Button onClick={handleRegisterVehicle} disabled={submitting} className="w-full">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {t("add_vehicle_submit", "Sajili Gari")}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 4: All set - manage vehicles + next step (verification) */}
      {step === 4 && (
        <div className="space-y-4">
          <Card>
            <CardContent className="p-4 flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-gray-700 dark:text-gray-300">
                <p className="font-medium">{t("register.setup_complete", "Usajili wako wa msingi umekamilika.")}</p>
                <p className="text-gray-500 dark:text-gray-400 mt-1">
                  {t("register.next_step_verify", "Hatua inayofuata: thibitisha NIDA na leseni yako ya udereva, kisha thibitisha kila gari (TRA/LATRA) hapa chini, kabla ya kuanza kupokea kazi.")}{" "}
                  <Link to="/logistics/verify" className="underline font-medium text-blue-600 dark:text-blue-400">
                    {t("verify_now", "Thibitisha Sasa")}
                  </Link>
                </p>
              </div>
            </CardContent>
          </Card>

          <div>
            <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">{t("register.my_vehicles", "Magari Yangu")}</h2>
            <div className="space-y-2">
              {vehicles.map((v) => {
                const bondedToMe = v.active_driver?.id === driver?.id;
                const verifStatus = v.verification?.overall_status || "UNVERIFIED";
                return (
                  <Card key={v.id}>
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">{v.registration_number}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {t(`vehicle_types.${v.vehicle_type}`, v.vehicle_type)}
                          </p>
                          <p className="text-xs mt-1 flex items-center gap-1">
                            {bondedToMe ? (
                              <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
                                <CheckCircle2 className="w-3.5 h-3.5" /> {t("register.bonded_to_you", "Umeunganishwa na gari hili")}
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 text-gray-400">
                                <XCircle className="w-3.5 h-3.5" /> {t("register.not_bonded", "Hujaunganishwa")}
                              </span>
                            )}
                          </p>
                        </div>
                        <Button
                          size="sm"
                          variant={bondedToMe ? "outline" : "secondary"}
                          onClick={() => (bondedToMe ? handleUnbond(v) : handleRebond(v))}
                          disabled={unbondingId === v.id}
                        >
                          {unbondingId === v.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : bondedToMe ? (
                            t("register.remove_vehicle", "Ondoa")
                          ) : (
                            t("register.rebond", "Unganisha")
                          )}
                        </Button>
                      </div>

                      <div className="flex items-center justify-between gap-3 pt-2 border-t border-gray-100 dark:border-gray-700">
                        <p className="text-xs flex items-center gap-1">
                          {verifStatus === "VERIFIED" ? (
                            <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
                              <ShieldCheck className="w-3.5 h-3.5" /> {t("register.tra_latra_verified", "Imethibitishwa (TRA/LATRA)")}
                            </span>
                          ) : verifStatus === "FAILED" ? (
                            <span className="flex items-center gap-1 text-red-500">
                              <ShieldX className="w-3.5 h-3.5" /> {t("register.tra_latra_failed", "Uthibitisho umeshindwa")}
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-amber-500">
                              <ShieldAlert className="w-3.5 h-3.5" /> {t("register.tra_latra_pending", "Bado halijathibitishwa")}
                            </span>
                          )}
                        </p>
                        {verifStatus !== "VERIFIED" && (
                          <Button size="sm" variant="secondary" onClick={() => handleVerifyVehicle(v)} disabled={verifyingId === v.id}>
                            {verifyingId === v.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("register.verify_vehicle", "Thibitisha Gari (TRA/LATRA)")}
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>

          <Link to="/logistics/jobs">
            <Button className="w-full" variant="secondary">
              {t("available_jobs_title", "Kazi za Usafirishaji Zilizo Wazi")}
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
