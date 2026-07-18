// src/app/accounts/pages/VerifyIdentityPage.jsx

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ShieldCheck, ShieldAlert, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";

const COUNTRIES = [
  { code: "TZ", labelKey: "country_tz" },
  { code: "KE", labelKey: "country_ke" },
  { code: "UG", labelKey: "country_ug" },
  { code: "RW", labelKey: "country_rw" },
  { code: "BI", labelKey: "country_bi" },
  { code: "SS", labelKey: "country_ss" },
];

export default function VerifyIdentityPage() {
  const { t } = useTranslation("accounts");
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [isVerified, setIsVerified] = useState(false);
  const [country, setCountry] = useState("TZ");
  const [nationalId, setNationalId] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api
      .get("/auth/me/")
      .then((res) => setIsVerified(!!res.data?.is_identity_verified))
      .catch(() => setIsVerified(false))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!nationalId.trim()) {
      toast.error(t("verify_identity.id_required", "Weka namba ya kitambulisho."));
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/gov/verify_nin/", { country, national_id: nationalId.trim() });
      setIsVerified(true);
      toast.success(t("verify_identity.success", "Kitambulisho chako kimethibitishwa!"));
    } catch (error) {
      const detail =
        error.response?.data?.national_id?.[0] ||
        error.response?.data?.non_field_errors?.[0] ||
        error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("verify_identity.failed", "Imeshindwa kuthibitisha kitambulisho."));
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
          {t("verify_identity.title", "Thibitisha Kitambulisho Chako")}
        </h1>
      </div>

      {isVerified ? (
        <Card>
          <CardContent className="p-6 text-center space-y-3">
            <ShieldCheck className="w-12 h-12 text-green-500 mx-auto" />
            <p className="text-gray-700 dark:text-gray-300 font-medium">
              {t("verify_identity.already_verified", "Kitambulisho chako kimethibitishwa. Unaweza kununua na kuomba bidhaa bila kizuizi.")}
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card>
            <CardContent className="p-4 flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t(
                  "verify_identity.description",
                  "Ili kuongeza usalama wa Jamiikazini, kila mnunuzi lazima athibitishe kitambulisho chake cha taifa kabla ya kununua au kuomba bidhaa. Bado unaweza kutazama maduka na bidhaa bila kizuizi."
                )}
              </p>
            </CardContent>
          </Card>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Card>
              <CardContent className="p-4 space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t("verify_identity.country_label", "Nchi")}
                  </label>
                  <select
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                  >
                    {COUNTRIES.map((c) => (
                      <option key={c.code} value={c.code}>
                        {t(`verify_identity.${c.labelKey}`, c.code)}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t("verify_identity.id_label", "Namba ya Kitambulisho cha Taifa")}
                  </label>
                  <input
                    type="text"
                    value={nationalId}
                    onChange={(e) => setNationalId(e.target.value)}
                    placeholder={t("verify_identity.id_placeholder", "Weka namba yako")}
                    className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                    required
                  />
                </div>
              </CardContent>
            </Card>

            <Button type="submit" disabled={submitting} className="w-full" size="lg">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {t("verify_identity.submit", "Thibitisha Sasa")}
            </Button>
          </form>
        </>
      )}
    </div>
  );
}
