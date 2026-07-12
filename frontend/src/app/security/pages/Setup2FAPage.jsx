// src/app/security/pages/Setup2FAPage.jsx

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import { ArrowLeft, Loader2, ShieldCheck, KeyRound, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useAppContext } from "@/context/AppContext";

export default function Setup2FAPage() {
  const { t } = useTranslation("security");
  const navigate = useNavigate();
  const { user } = useAppContext();

  const [loading, setLoading] = useState(true);
  const [qrCode, setQrCode] = useState(null);
  const [otpUri, setOtpUri] = useState(null);
  const [token, setToken] = useState("");
  const [verifying, setVerifying] = useState(false);
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    api
      .get("/security/2fa/setup/")
      .then((res) => {
        setQrCode(res.data?.qr_code);
        setOtpUri(res.data?.otp_uri);
      })
      .catch(() => toast.error(t("2fa.errors.load_failed") || "Imeshindwa kupakia QR code."))
      .finally(() => setLoading(false));
  }, [t]);

  const handleVerify = async (e) => {
    e.preventDefault();
    if (!token.trim() || token.trim().length < 6) {
      toast.error(t("2fa.errors.code_required") || "Weka namba 6 kutoka programu yako ya authenticator.");
      return;
    }
    setVerifying(true);
    try {
      await api.post("/security/2fa/setup/", { token: token.trim() });
      setEnabled(true);
      toast.success(t("2fa.success") || "2FA imewashwa kikamilifu.");
    } catch (error) {
      toast.error(error.response?.data?.detail || t("2fa.errors.invalid_code") || "Namba si sahihi. Jaribu tena.");
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        {t("back") || "Rudi"}
      </button>

      <Card>
        <CardHeader
          title={t("2fa.title") || "Washa Uthibitishaji wa Hatua Mbili (2FA)"}
          icon={<ShieldCheck className="w-5 h-5" />}
          divider
        />
        <CardContent>
          {enabled || user?.is_2fa_enabled ? (
            <div className="text-center py-6">
              <CheckCircle2 className="w-14 h-14 mx-auto text-green-500 mb-3" />
              <p className="text-gray-700 dark:text-gray-300 font-medium">
                {t("2fa.already_enabled") || "2FA tayari imewashwa kwenye akaunti yako."}
              </p>
            </div>
          ) : loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t("2fa.instructions") ||
                  "1) Fungua programu ya authenticator (Google Authenticator, Authy n.k). 2) Piga picha (scan) QR code hii. 3) Weka namba 6 inayotokea."}
              </p>
              {qrCode && (
                <div className="flex justify-center">
                  <img
                    src={`data:image/png;base64,${qrCode}`}
                    alt="2FA QR Code"
                    className="w-48 h-48 border border-gray-200 dark:border-gray-700 rounded-lg"
                  />
                </div>
              )}
              {otpUri && (
                <p className="text-xs text-center text-gray-400 dark:text-gray-500 break-all">
                  {t("2fa.manual_entry") || "Huwezi ku-scan? Andika key hii mwenyewe:"} {otpUri.match(/secret=([^&]+)/)?.[1]}
                </p>
              )}

              <form onSubmit={handleVerify} className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    <KeyRound className="w-4 h-4 inline mr-1" />
                    {t("2fa.code") || "Namba 6 kutoka Authenticator"}
                  </label>
                  <input
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    value={token}
                    onChange={(e) => setToken(e.target.value.replace(/\D/g, ""))}
                    placeholder="123456"
                    className="w-full px-3 py-2 text-center tracking-[0.5em] text-lg border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
                <Button type="submit" disabled={verifying} className="w-full bg-purple-600 hover:bg-purple-700">
                  {verifying ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <ShieldCheck className="w-4 h-4 mr-2" />}
                  {verifying ? t("2fa.verifying") || "Inathibitisha..." : t("2fa.enable") || "Washa 2FA"}
                </Button>
              </form>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
