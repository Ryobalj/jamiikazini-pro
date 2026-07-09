// src/pages/auth/Login.jsx

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import InputField from "@/components/InputField";
import * as Icons from "lucide-react";
import { useAppContext } from "@/context/AppContext";
import { useTranslation } from "react-i18next";
import api from "@/lib/axios";

const RECAPTCHA_V3_SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY;

export default function Login() {
  const navigate = useNavigate();
  const { setUser } = useAppContext();
  const { t } = useTranslation();

  const [formData, setFormData] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [recaptchaReady, setRecaptchaReady] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) navigate("/home", { replace: true });
  }, [navigate]);

  useEffect(() => {
    if (!document.getElementById("recaptcha-v3")) {
      const script = document.createElement("script");
      script.id = "recaptcha-v3";
      script.src = `https://www.google.com/recaptcha/api.js?render=${RECAPTCHA_V3_SITE_KEY}`;
      script.async = true;
      script.defer = true;
      document.body.appendChild(script);
    }

    const waitForRecaptcha = () => {
      if (window.grecaptcha?.execute) {
        setRecaptchaReady(true);
      } else {
        setTimeout(waitForRecaptcha, 300);
      }
    };
    waitForRecaptcha();
  }, []);

  const handleChange = (e) =>
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setErrors({});

    try {
      if (!recaptchaReady) {
        setErrors({ general: t("auth_login.recaptcha_not_ready") });
        setSubmitting(false);
        return;
      }

      const recaptchaToken = await window.grecaptcha.execute(RECAPTCHA_V3_SITE_KEY, {
        action: "login",
      });

      const response = await api.post("/security/login/", {
        email: formData.email,
        password: formData.password,
        recaptcha_token: recaptchaToken,
      });

      console.log("Login response:", response.data);

      const accessToken = response.data.access || 
                          response.data.token || 
                          response.data.access_token;
                          
      const refreshToken = response.data.refresh || 
                           response.data.refresh_token;
                           
      const userData = response.data.user || response.data;

      if (!accessToken) {
        setErrors({ general: t("auth_login.no_token") });
        setSubmitting(false);
        return;
      }

      localStorage.setItem("access_token", accessToken);
      if (refreshToken) {
        localStorage.setItem("refresh_token", refreshToken);
      }
      localStorage.setItem("user", JSON.stringify(userData));
      
      setUser(userData);
      navigate("/home", { replace: true });
      
    } catch (error) {
      console.error("Login error:", error.response?.data);
      
      const errorData = error.response?.data;
      const errorCode = errorData?.code;
      const errorMessage = errorData?.detail || 
                           errorData?.message || 
                           errorData?.error ||
                           error.message;
      
      const errorLower = errorMessage.toLowerCase();
      
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
      
      // CHECK 1: User not found (using code first)
      if (errorCode === "user_not_found" || 
          errorLower.includes("no account found") ||
          errorLower.includes("not found") || 
          errorLower.includes("does not exist") ||
          errorLower.includes("no account") ||
          errorLower.includes("user not found") ||
          errorLower.includes("email not found")) {
        
        navigate("/auth/register/", { 
          state: { 
            email: formData.email,
            message: "Account not found. Please register."
          } 
        });
        return;
      }
      
      // CHECK 2: Invalid password
      if (errorCode === "invalid_password" ||
          errorLower.includes("invalid password") ||
          errorLower.includes("incorrect password") ||
          errorLower.includes("wrong password") ||
          errorLower.includes("invalid credentials")) {
        setErrors({ general: t("auth_login.invalid_credentials") || "Invalid password. Please try again." });
        return;
      }
      
      // CHECK 3: Other errors
      setErrors({ general: errorMessage || t("auth_login.login_failed") });
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegisterRedirect = () => {
    navigate("/auth/register/", { 
      state: { 
        email: formData.email 
      } 
    });
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white dark:bg-gray-800 rounded-xl shadow-md">
      <h2 className="text-xl font-semibold mb-4 text-center text-gray-800 dark:text-white">
        {t("auth_login.title")}
      </h2>

      {errors.general && (
        <p className="text-red-500 mb-2 text-center">{errors.general}</p>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <InputField
          label={t("auth_login.email_label")}
          name="email"
          type="email"
          icon={Icons.Mail}
          placeholder={t("auth_login.email_placeholder")}
          value={formData.email}
          onChange={handleChange}
          error={errors.email}
        />

        <InputField
          label={t("auth_login.password_label")}
          name="password"
          type="password"
          icon={Icons.Lock}
          placeholder={t("auth_login.password_placeholder")}
          value={formData.password}
          onChange={handleChange}
          error={errors.password}
        />

        <button
          type="submit"
          disabled={submitting || !recaptchaReady}
          className={`w-full py-2 px-4 rounded text-white font-semibold transition ${
            submitting || !recaptchaReady
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700"
          }`}
        >
          {submitting ? t("auth_login.loading") : t("auth_login.submit")}
        </button>
      </form>

      <div className="mt-4 text-center">
        <button
          onClick={handleRegisterRedirect}
          className="text-sm text-blue-600 hover:underline dark:text-blue-400"
        >
          {t("auth_login.no_account")}
        </button>
      </div>
    </div>
  );
}
