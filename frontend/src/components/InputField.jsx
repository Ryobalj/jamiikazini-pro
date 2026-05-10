// src/components/InputField.jsx
import React, { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import zxcvbn from "zxcvbn";
import { useTranslation } from "react-i18next";

export default function InputField({
  label,
  name,
  type = "text",
  placeholder = "",
  icon: Icon,
  value,
  onChange,
  error,
  options = [], // Kwa select only
  showStrength = false,
  disabled = false,
  readOnly = false,
  containerClassName = "",
  inputClassName = "",
  rows = 4, // for textarea
}) {
  const { t } = useTranslation();
  const [showPassword, setShowPassword] = useState(false);

  const isPassword = type === "password";
  const inputType = isPassword && showPassword ? "text" : type;

  const strength = isPassword && value ? zxcvbn(value) : null;
  const score = strength?.score ?? 0;

  const strengthLabels = [
    t("password.strength.very_weak"),
    t("password.strength.weak"),
    t("password.strength.fair"),
    t("password.strength.strong"),
    t("password.strength.very_strong"),
  ];

  const strengthColor = [
    "text-red-500",
    "text-orange-500",
    "text-yellow-500",
    "text-blue-500",
    "text-green-600",
  ];

  const baseInputStyles = `
    w-full py-2 text-sm rounded border focus:outline-none focus:ring-2
    bg-white dark:bg-gray-700 text-gray-900 dark:text-white
    border-gray-300 dark:border-gray-600
    focus:ring-blue-500 ${Icon ? "pl-10" : "pl-3"}
    ${isPassword ? "pr-10" : "pr-3"}
    ${error ? "border-red-500 focus:ring-red-500" : ""}
    ${inputClassName}
  `;

  return (
    <div className={`w-full ${containerClassName}`}>
      {label && (
        <label
          htmlFor={name}
          className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-200"
        >
          {label}
        </label>
      )}

      <div className="relative">
        {Icon && typeof Icon === "function" && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400 pointer-events-none">
            <Icon size={18} />
          </div>
        )}

        {/* TEXTAREA */}
        {type === "textarea" ? (
          <textarea
            id={name}
            name={name}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            rows={rows}
            className={baseInputStyles}
            disabled={disabled}
            readOnly={readOnly}
          />
        ) : type === "select" ? (
          // SELECT
          <select
            id={name}
            name={name}
            value={value}
            onChange={onChange}
            className={baseInputStyles}
            disabled={disabled}
          >
            <option value="">{t("form.select_option")}</option>
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        ) : (
          // INPUT (text, email, number, password, etc.)
          <input
            id={name}
            name={name}
            type={inputType}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            className={baseInputStyles}
            disabled={disabled}
            readOnly={readOnly}
          />
        )}

        {/* PASSWORD TOGGLE */}
        {isPassword && (
          <button
            type="button"
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400"
            onClick={() => setShowPassword((prev) => !prev)}
            tabIndex={-1}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>

      {/* ERROR */}
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}

      {/* PASSWORD STRENGTH */}
      {isPassword && value && showStrength && (
        <p className={`text-xs mt-1 ${strengthColor[score]}`}>
          {t("password.label")} {strengthLabels[score]}
        </p>
      )}
    </div>
  );
}