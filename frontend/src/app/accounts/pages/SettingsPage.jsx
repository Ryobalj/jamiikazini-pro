// src/app/accounts/pages/SettingsPage.jsx

import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Settings, Globe, Bell, Lock, Loader2, ShieldCheck, Phone, CheckCircle2 } from "lucide-react";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useAppContext } from "@/context/AppContext";
import LanguageSwitcher from "@/components/LanguageSwitcher";

export default function SettingsPage() {
  const { t } = useTranslation("accounts");
  const navigate = useNavigate();
  const { user, setUser } = useAppContext();

  const [otpMethod, setOtpMethod] = useState(user?.preferred_otp_method || "SMS");
  const [savingOtpMethod, setSavingOtpMethod] = useState(false);

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);

  const [phoneRequested, setPhoneRequested] = useState(false);
  const [phoneMasked, setPhoneMasked] = useState("");
  const [phoneCode, setPhoneCode] = useState("");
  const [requestingPhoneOtp, setRequestingPhoneOtp] = useState(false);
  const [verifyingPhone, setVerifyingPhone] = useState(false);

  const saveOtpMethod = async (method) => {
    setOtpMethod(method);
    setSavingOtpMethod(true);
    try {
      const res = await api.patch("/auth/me/", { preferred_otp_method: method });
      setUser?.((prev) => (prev ? { ...prev, preferred_otp_method: res.data.preferred_otp_method } : prev));
      toast.success(t("settings.saved", "Imehifadhiwa."));
    } catch (error) {
      toast.error(t("settings.save_failed", "Imeshindwa kuhifadhi."));
    } finally {
      setSavingOtpMethod(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error(t("settings.passwords_mismatch", "Manenosiri mapya hayafanani."));
      return;
    }
    setChangingPassword(true);
    try {
      await api.post("/auth/change-password/", {
        old_password: oldPassword,
        new_password: newPassword,
        otp_code: otpCode || undefined,
      });
      toast.success(t("settings.password_changed", "Nenosiri limebadilishwa."));
      setOldPassword(""); setNewPassword(""); setConfirmPassword(""); setOtpCode("");
    } catch (error) {
      const detail = error.response?.data?.detail
        || error.response?.data?.old_password?.[0]
        || error.response?.data?.new_password?.[0];
      toast.error(typeof detail === "string" ? detail : t("settings.save_failed", "Imeshindwa kuhifadhi."));
    } finally {
      setChangingPassword(false);
    }
  };

  const requestPhoneOtp = async () => {
    setRequestingPhoneOtp(true);
    try {
      const res = await api.post("/security/phone/request/");
      setPhoneRequested(true);
      setPhoneMasked(res.data?.masked || "");
      toast.success(t("settings.phone_otp_sent", "OTP imetumwa kwa SMS."));
    } catch (error) {
      toast.error(error.response?.data?.detail || t("settings.save_failed", "Imeshindwa kuhifadhi."));
    } finally {
      setRequestingPhoneOtp(false);
    }
  };

  const verifyPhoneOtp = async (e) => {
    e.preventDefault();
    setVerifyingPhone(true);
    try {
      await api.post("/security/phone/verify/", { code: phoneCode });
      setUser?.((prev) => (prev ? { ...prev, is_phone_verified: true } : prev));
      toast.success(t("settings.phone_verified", "Namba yako ya simu imethibitishwa."));
      setPhoneCode(""); setPhoneRequested(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || t("settings.phone_invalid_code", "Msimbo si sahihi."));
    } finally {
      setVerifyingPhone(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">
          <Settings className="inline w-6 h-6 mr-2" />
          {t("settings.title")}
        </h1>

        <div className="space-y-6">
          <Card>
            <CardHeader title={t("settings.language_title", "Lugha")} icon={<Globe className="w-5 h-5" />} divider />
            <CardContent>
              <LanguageSwitcher />
            </CardContent>
          </Card>

          <Card>
            <CardHeader title={t("settings.notifications_title", "Njia ya OTP/Arifa")} icon={<Bell className="w-5 h-5" />} divider />
            <CardContent>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                {t("settings.otp_method_desc", "Chagua njia unayopendelea kupokea msimbo wa OTP.")}
              </p>
              <div className="flex gap-2">
                {["SMS", "EMAIL", "TOTP"].map((method) => (
                  <button
                    key={method}
                    disabled={savingOtpMethod}
                    onClick={() => saveOtpMethod(method)}
                    className={`px-4 py-2 rounded-lg text-sm border ${
                      otpMethod === method
                        ? "bg-purple-600 text-white border-purple-600"
                        : "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700"
                    }`}
                  >
                    {method}
                  </button>
                ))}
                {savingOtpMethod && <Loader2 className="w-4 h-4 animate-spin text-gray-400 mt-2" />}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader title={t("settings.privacy_title", "Faragha na Usalama")} icon={<Lock className="w-5 h-5" />} divider />
            <CardContent className="space-y-6">
              <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-purple-600" />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {t("phone_verified")}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {user?.phone_number || t("settings.no_phone", "Hakuna namba ya simu")}
                      </p>
                    </div>
                  </div>
                  {user?.is_phone_verified ? (
                    <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 font-medium">
                      <CheckCircle2 className="w-4 h-4" /> {t("settings.verified", "Imethibitishwa")}
                    </span>
                  ) : (
                    !phoneRequested && (
                      <Button size="sm" disabled={requestingPhoneOtp || !user?.phone_number} onClick={requestPhoneOtp}>
                        {requestingPhoneOtp ? <Loader2 className="w-4 h-4 animate-spin" /> : t("settings.verify_phone", "Thibitisha")}
                      </Button>
                    )
                  )}
                </div>

                {!user?.is_phone_verified && phoneRequested && (
                  <form onSubmit={verifyPhoneOtp} className="mt-3 flex gap-2">
                    <input
                      type="text" inputMode="numeric" maxLength={6} value={phoneCode}
                      onChange={(e) => setPhoneCode(e.target.value.replace(/\D/g, ""))}
                      placeholder={phoneMasked ? `${t("settings.otp_code", "Msimbo wa 2FA")} (${phoneMasked})` : t("settings.otp_code", "Msimbo wa 2FA")}
                      className="flex-1 p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                    />
                    <Button type="submit" size="sm" disabled={verifyingPhone}>
                      {verifyingPhone ? <Loader2 className="w-4 h-4 animate-spin" /> : t("settings.verify_phone", "Thibitisha")}
                    </Button>
                  </form>
                )}
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-purple-600" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {t("two_factor_authentication")}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {user?.is_2fa_enabled ? t("2fa_enabled_desc") : t("2fa_disabled_desc")}
                    </p>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant={user?.is_2fa_enabled ? "danger" : "primary"}
                  onClick={() => navigate("/security/2fa/setup")}
                >
                  {user?.is_2fa_enabled ? t("disable_2fa") : t("enable_2fa")}
                </Button>
              </div>

              <form onSubmit={handleChangePassword} className="space-y-3">
                <p className="text-sm font-medium text-gray-900 dark:text-white">{t("change_password")}</p>
                <input
                  type="password" required value={oldPassword} onChange={(e) => setOldPassword(e.target.value)}
                  placeholder={t("settings.old_password", "Nenosiri la Zamani")}
                  className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                />
                <input
                  type="password" required value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
                  placeholder={t("settings.new_password", "Nenosiri Jipya")}
                  className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                />
                <input
                  type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder={t("settings.confirm_password", "Rudia Nenosiri Jipya")}
                  className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                />
                {user?.is_2fa_enabled && (
                  <input
                    type="text" value={otpCode} onChange={(e) => setOtpCode(e.target.value)}
                    placeholder={t("settings.otp_code", "Msimbo wa 2FA")}
                    className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                  />
                )}
                <Button type="submit" disabled={changingPassword} className="w-full">
                  {changingPassword ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                  {t("update_password")}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
