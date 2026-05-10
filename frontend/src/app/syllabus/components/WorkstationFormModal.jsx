// src/app/syllabus/components/WorkstationFormModal.jsx
import React, { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "../../../lib/axios.js";

export default function WorkstationFormModal({ open, onSubmit }) {
  const { t } = useTranslation("syllabus");
  const navigate = useNavigate();

  const [form, setForm] = useState({
    school_name: "",
    district: "",
    ward: "",
    region: "",
    is_active: true,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const firstInputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setForm({
        school_name: "",
        district: "",
        ward: "",
        region: "",
        is_active: true,
      });
      setError(null);
      setTimeout(() => firstInputRef.current?.focus(), 100);
    }
  }, [open]);

  const normalizeName = (value, field) => {
    if (!value) return "";
    const commonWords = {
      school_name: ["shule", "ya", "primary", "secondary", "msingi", "p/s", "s/m", "school"],
      ward: ["kata", "ya", "ward"],
      district: ["halimashauri", "ya", "wilaya", "district", "council"],
      region: ["mkoa", "wa", "region"],
    };

    let words = value.toLowerCase();
    (commonWords[field] || []).forEach((w) => {
      words = words.replace(new RegExp(`\\b${w}\\b`, "gi"), "");
    });

    return words
      .trim()
      .split(" ")
      .filter(Boolean)
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ")
      .slice(0, 50);
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === "checkbox" ? checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        ...form,
        school_name: normalizeName(form.school_name, "school_name"),
        district: normalizeName(form.district, "district"),
        ward: normalizeName(form.ward, "ward"),
        region: normalizeName(form.region, "region"),
      };

      const res = await api.post("/syllabus/teacher-workstations/", payload);
      onSubmit(res.data);
      setForm({ school_name: "", district: "", ward: "", region: "", is_active: true });
    } catch (err) {
      setError(
        err.response?.data?.teacher?.[0] ||
        err.response?.data?.detail ||
        "Tatizo limejitokeza"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    navigate("/home"); // redirect user to home page
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-auto">
      <div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded-lg p-6 w-full max-w-md shadow-lg">
        <h2 className="text-lg font-semibold mb-4">{t("workstation.add_title")}</h2>

        {error && <p className="text-red-600 dark:text-red-400 mb-3">{error}</p>}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* School Name */}
          <div>
            <label className="block mb-1 font-medium">{t("workstation.school_name")}</label>
            <input
              type="text"
              name="school_name"
              value={form.school_name}
              onChange={handleChange}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring focus:ring-blue-500 dark:focus:ring-blue-400"
              placeholder={t("workstation.school_help")}
              required
              ref={firstInputRef}
              maxLength={100}
            />
          </div>

          {/* District */}
          <div>
            <label className="block mb-1 font-medium">{t("workstation.district")}</label>
            <input
              type="text"
              name="district"
              value={form.district}
              onChange={handleChange}
              placeholder={t("workstation.district_help")}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring focus:ring-blue-500 dark:focus:ring-blue-400"
              required
              maxLength={50}
            />
          </div>

          {/* Ward */}
          <div>
            <label className="block mb-1 font-medium">{t("workstation.ward")}</label>
            <input
              type="text"
              name="ward"
              value={form.ward}
              onChange={handleChange}
              placeholder={t("workstation.ward_help")}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring focus:ring-blue-500 dark:focus:ring-blue-400"
              maxLength={50}
            />
          </div>

          {/* Region */}
          <div>
            <label className="block mb-1 font-medium">{t("workstation.region")}</label>
            <input
              type="text"
              name="region"
              value={form.region}
              onChange={handleChange}
              placeholder={t("workstation.region_help")}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring focus:ring-blue-500 dark:focus:ring-blue-400"
              maxLength={50}
            />
          </div>

          {/* Active */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              name="is_active"
              checked={form.is_active}
              onChange={handleChange}
              className="accent-blue-600 dark:accent-blue-400"
            />
            <span>{t("workstation.active")}</span>
          </div>

          {/* Buttons */}
          <div className="flex justify-end gap-2 pt-4">
            <button
              type="button"
              onClick={handleCancel}
              className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700"
              disabled={loading}
            >
              {t("common.cancel")}
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
              disabled={loading}
            >
              {loading ? t("common.saving") : t("common.save")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}