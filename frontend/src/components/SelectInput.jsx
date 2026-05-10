import React from "react";
import { useTranslation } from "react-i18next";

export default function SelectInput({
  label,
  name,
  value,
  onChange,
  options = [],
  placeholder = "",
  error,
  disabled = false,
  loading = false,
  required = false,
}) {
  const { t } = useTranslation();

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={name}
          className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-200"
        >
          {label}
        </label>
      )}

      <select
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        disabled={disabled || loading}
        required={required}
        className={`w-full py-2 px-3 text-sm rounded border focus:outline-none focus:ring-2
          bg-white dark:bg-gray-700
          text-gray-900 dark:text-white
          border-gray-300 dark:border-gray-600
          focus:ring-blue-500
          ${error ? "border-red-500 focus:ring-red-500" : ""}
        `}
      >
        {placeholder && (
          <option value="" disabled hidden>
            {loading ? t("common.loading") : placeholder}
          </option>
        )}

        {loading ? (
          <option value="" disabled>
            {t("common.loading")}...
          </option>
        ) : (
          options.map((opt) =>
            opt.options ? (
              // Grouped option (optgroup)
              <optgroup key={opt.label} label={opt.label}>
                {opt.options.map((child) => (
                  <option key={child.value} value={child.value}>
                    {child.label}
                  </option>
                ))}
              </optgroup>
            ) : (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            )
          )
        )}
      </select>

      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  );
}