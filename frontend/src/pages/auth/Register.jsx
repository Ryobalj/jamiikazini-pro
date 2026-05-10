// src/pages/auth/Register.jsx

import React, { useState } from "react";
import ReCAPTCHA from "react-google-recaptcha";
import { useNavigate } from "react-router-dom";
import { registerUser } from "@/lib/auth";
import InputField from "@/components/InputField";
import PasswordField from "@/components/PasswordField";
import * as Icons from "lucide-react";
import { useTranslation } from "react-i18next";

const RECAPTCHA_V2_SITE_KEY = import.meta.env.VITE_RECAPTCHA_PUBLIC_KEY;

export default function Register() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [formData, setFormData] = useState({
    email: "",
    full_name: "",
    nenosiri: "",
    thibitisha_nenosiri: "",
    phone_number: "",
    recaptcha_token: "",
  });

  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) =>
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleRecaptcha = (token) =>
    setFormData((prev) => ({ ...prev, recaptcha_token: token }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setErrors({});

    if (formData.nenosiri !== formData.thibitisha_nenosiri) {
      setErrors({ thibitisha_nenosiri: t("auth_register.errors.password_mismatch") });
      setSubmitting(false);
      return;
    }

    if (!formData.recaptcha_token) {
      setErrors({ general: t("auth_register.errors.recaptcha_required") });
      setSubmitting(false);
      return;
    }

    if (!formData.nenosiri || formData.nenosiri.length < 6) {
      setErrors({ nenosiri: t("auth_register.errors.password_length") });
      setSubmitting(false);
      return;
    }

    try {
      const payload = {
        email: formData.email,
        full_name: formData.full_name,
        phone_number: formData.phone_number,
        recaptcha_token: formData.recaptcha_token,
        password: formData.nenosiri,
        confirm_password: formData.thibitisha_nenosiri,
      };

      const result = await registerUser(payload);

      if (!result.success) {
        setErrors({ general: result.message });
        setSubmitting(false);
        return;
      }

      alert(t("auth_register.success"));
      navigate("/security/login");
    } catch (error) {
      setErrors({ general: t("auth_register.errors.network") });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white dark:bg-gray-800 rounded shadow">
      <h2 className="text-xl font-semibold mb-4 text-center text-gray-800 dark:text-white">
        {t("auth_register.title")}
      </h2>

      {errors.general && (
        <p className="text-red-500 mb-2 text-center">{errors.general}</p>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <InputField
          label={t("auth_register.email_label")}
          name="email"
          type="email"
          icon={Icons.Mail}
          placeholder={t("auth_register.email_placeholder")}
          value={formData.email}
          onChange={handleChange}
          error={errors.email}
        />

        <InputField
          label={t("auth_register.name_label")}
          name="full_name"
          type="text"
          icon={Icons.User}
          placeholder={t("auth_register.name_placeholder")}
          value={formData.full_name}
          onChange={handleChange}
          error={errors.full_name}
        />

        <PasswordField
          password={formData.nenosiri}
          confirmPassword={formData.thibitisha_nenosiri}
          onPasswordChange={(val) =>
            setFormData((prev) => ({ ...prev, nenosiri: val }))
          }
          onConfirmChange={(val) =>
            setFormData((prev) => ({ ...prev, thibitisha_nenosiri: val }))
          }
          error={errors.nenosiri || errors.password || errors.thibitisha_nenosiri}
        />

        <InputField
          label={t("auth_register.phone_label")}
          name="phone_number"
          type="text"
          icon={Icons.Phone}
          placeholder={t("auth_register.phone_placeholder")}
          value={formData.phone_number}
          onChange={handleChange}
          error={errors.phone_number}
        />

        <div className="flex justify-center">
          <ReCAPTCHA sitekey={RECAPTCHA_V2_SITE_KEY} onChange={handleRecaptcha} />
        </div>

        <button
          type="submit"
          disabled={submitting || !formData.recaptcha_token}
          className={`w-full py-2 px-4 rounded text-white font-semibold transition ${
            submitting
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {submitting ? t("auth_register.loading") : t("auth_register.submit")}
        </button>
      </form>
    </div>
  );
}