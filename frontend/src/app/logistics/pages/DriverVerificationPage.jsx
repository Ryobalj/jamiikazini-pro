// src/app/logistics/pages/DriverVerificationPage.jsx

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ShieldCheck, ShieldAlert, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";

const STATUS_LABELS = {
  VERIFIED: "status_verified",
  PENDING: "status_pending",
  FAILED: "status_failed",
};

export default function DriverVerificationPage() {
  const { t } = useTranslation("logistics");
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [overallStatus, setOverallStatus] = useState(null);
  const [countryCode, setCountryCode] = useState("tz");
  const [nationalId, setNationalId] = useState("");
  const [driverLicense, setDriverLicense] = useState("");
  const [vehicleLicense, setVehicleLicense] = useState("");
  const [latraLicense, setLatraLicense] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadStatus = () => {
    setLoading(true);
    api
      .get("/logistics/transport-verifications/")
      .then((res) => {
        const data = Array.isArray(res.data) ? res.data : res.data?.results || [];
        setOverallStatus(data[0]?.overall_status || null);
      })
      .catch(() => setOverallStatus(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!nationalId && !driverLicense && !vehicleLicense && !latraLicense) {
      toast.error(t("verify_driver.at_least_one_required", "Jaza angalau namba moja ya uthibitisho."));
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/logistics/transport-verifications/verify_all/", {
        country_code: countryCode,
        national_id_number: nationalId || undefined,
        driver_license_number: driverLicense || undefined,
        vehicle_license_number: vehicleLicense || undefined,
        latra_license_number: latraLicense || undefined,
      });
      toast.success(t("verify_driver.submitted", "Maombi ya uthibitisho yametumwa."));
      loadStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || t("verify_driver.failed", "Imeshindwa kutuma uthibitisho."));
    } finally {
      setSubmitting(false);
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
    <div className="max-w-md mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("verify_driver.title", "Thibitisha Uwezo Wako wa Kuendesha")}
        </h1>
      </div>

      {overallStatus === "VERIFIED" ? (
        <Card>
          <CardContent className="p-6 text-center space-y-3">
            <ShieldCheck className="w-12 h-12 text-green-500 mx-auto" />
            <p className="text-gray-700 dark:text-gray-300 font-medium">
              {t("verify_driver.already_verified", "Umethibitishwa - unaweza kupokea kazi za usafirishaji.")}
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card>
            <CardContent className="p-4 flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-gray-600 dark:text-gray-400">
                <p>
                  {t(
                    "verify_driver.description",
                    "Lazima ukamilishe uthibitisho wa NIDA, leseni ya udereva, leseni ya gari, na LATRA kabla ya kupokea kazi za usafirishaji."
                  )}
                </p>
                {overallStatus && (
                  <p className="mt-2 font-medium">
                    {t("verify_driver.current_status", "Hali ya sasa")}: {t(`verify_driver.${STATUS_LABELS[overallStatus]}`, overallStatus)}
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Card>
              <CardContent className="p-4 space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t("verify_driver.country_label", "Nchi")}
                  </label>
                  <select
                    value={countryCode}
                    onChange={(e) => setCountryCode(e.target.value)}
                    className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                  >
                    <option value="tz">Tanzania</option>
                    <option value="ke">Kenya</option>
                    <option value="ug">Uganda</option>
                    <option value="rw">Rwanda</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t("verify_driver.nida_label", "Namba ya NIDA")}
                  </label>
                  <input
                    type="text"
                    value={nationalId}
                    onChange={(e) => setNationalId(e.target.value)}
                    className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t("verify_driver.driver_license_label", "Namba ya Leseni ya Udereva")}
                  </label>
                  <input
                    type="text"
                    value={driverLicense}
                    onChange={(e) => setDriverLicense(e.target.value)}
                    className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t("verify_driver.vehicle_license_label", "Namba ya Leseni ya Gari")}
                  </label>
                  <input
                    type="text"
                    value={vehicleLicense}
                    onChange={(e) => setVehicleLicense(e.target.value)}
                    className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t("verify_driver.latra_label", "Namba ya Leseni ya LATRA")}
                  </label>
                  <input
                    type="text"
                    value={latraLicense}
                    onChange={(e) => setLatraLicense(e.target.value)}
                    className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                  />
                </div>
              </CardContent>
            </Card>

            <Button type="submit" disabled={submitting} className="w-full" size="lg">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {t("verify_driver.submit", "Tuma Uthibitisho")}
            </Button>
          </form>
        </>
      )}
    </div>
  );
}
