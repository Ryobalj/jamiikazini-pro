// src/components/PasswordField.jsx

import React, { useState } from "react";
import { Eye, EyeOff, Lock } from "lucide-react";
import zxcvbn from "zxcvbn";
import { useTranslation } from "react-i18next";

export default function PasswordField({
  password,
  confirmPassword,
  onPasswordChange,
  onConfirmChange,
  error,
}) {
  const { t } = useTranslation();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const strength = password ? zxcvbn(password) : null;
  const score = strength?.score ?? 0;

  const strengthLabels = [
    t("password.strength.very_weak"),
    t("password.strength.weak"),
    t("password.strength.fair"),
    t("password.strength.strong"),
    t("password.strength.very_strong"),
  ];

  const strengthColor = [
    "bg-red-500",
    "bg-orange-500",
    "bg-yellow-500",
    "bg-blue-500",
    "bg-green-600",
  ];

  const passwordsMatch = password === confirmPassword;

  return (
    <div className="space-y-4">
      {/* Password Field */}
      <div className="w-full">
        <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-200">
          {t("auth.password")}
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400 pointer-events-none">
            <Lock size={18} />
          </div>
          <input
            type={showPassword ? "text" : "password"}
            name="password"
            value={password}
            onChange={(e) => onPasswordChange(e.target.value)}
            placeholder={t("auth.password_placeholder")}
            className={`w-full py-2 text-sm rounded border focus:outline-none focus:ring-2
              bg-white dark:bg-gray-700
              text-gray-900 dark:text-white
              border-gray-300 dark:border-gray-600
              focus:ring-blue-500 pl-10 pr-10
              ${error ? "border-red-500 focus:ring-red-500" : ""}
            `}
          />
          <button
            type="button"
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400"
            onClick={() => setShowPassword((prev) => !prev)}
            tabIndex={-1}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>

        {/* Password Strength */}
        {password && (
          <div className="mt-2">
            <div className="w-full h-2 bg-gray-300 dark:bg-gray-600 rounded">
              <div
                className={`h-2 rounded transition-all duration-300 ${strengthColor[score]}`}
                style={{ width: `${(score + 1) * 20}%` }}
              ></div>
            </div>
            <p className={`text-xs mt-1 ${strengthColor[score].replace("bg", "text")}`}>
              {t("password.label")} {strengthLabels[score]}
            </p>
          </div>
        )}
      </div>

      {/* Confirm Password Field */}
      <div className="w-full">
        <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-200">
          {t("auth.confirm_password")}
        </label>
        <div className="relative">
          <input
            type={showConfirm ? "text" : "password"}
            name="confirm_password"
            value={confirmPassword}
            onChange={(e) => onConfirmChange(e.target.value)}
            placeholder={t("auth.confirm_password_placeholder")}
            className={`w-full py-2 text-sm rounded border focus:outline-none focus:ring-2
              bg-white dark:bg-gray-700
              text-gray-900 dark:text-white
              border-gray-300 dark:border-gray-600
              focus:ring-blue-500 pr-10
              ${!passwordsMatch ? "border-red-500 focus:ring-red-500" : ""}
            `}
          />
          <button
            type="button"
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400"
            onClick={() => setShowConfirm((prev) => !prev)}
            tabIndex={-1}
          >
            {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>
        {!passwordsMatch && confirmPassword && (
          <p className="text-sm text-red-500 mt-1">
            {t("auth.passwords_do_not_match")}
          </p>
        )}
      </div>
    </div>
  );
}