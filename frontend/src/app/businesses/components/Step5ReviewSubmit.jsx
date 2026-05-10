// src/app/businesses/components/Step5ReviewSubmit.jsx

import React from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import api from "@/lib/axios";

export default function Step5ReviewSubmit({
  formData,
  goBack,
  onSubmit,
  isSubmitting,
}) {
  const { t } = useTranslation();

  const getInstitutionDisplay = () => {
    if (formData.institution_name) return formData.institution_name;
    if (formData.institution) {
      if (typeof formData.institution === 'object' && formData.institution.name) {
        return formData.institution.name;
      }
      return String(formData.institution);
    }
    return "-";
  };

  const getCategoryDisplay = () => {
    if (!formData.category) return "-";
    if (typeof formData.category === 'object') {
      return formData.category.name || formData.category.label || String(formData.category.id || "");
    }
    return String(formData.category);
  };

  const formatWebsiteUrl = (url) => {
    if (!url) return "#";
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    return `https://${url}`;
  };

  const handleSubmitClick = async () => {
    console.log("=== BUTTON CLICKED - DIRECT API CALL ===");
    console.log("formData:", formData);
    
    const submitData = {
      name: formData.name?.trim() || "Test Business " + Date.now(),
      institution: formData.institution,
    };
    
    if (formData.description?.trim()) {
      submitData.description = formData.description.trim();
    }
    
    if (formData.phone?.trim()) {
      submitData.phone = formData.phone.trim();
    }
    
    if (formData.email?.trim()) {
      submitData.email = formData.email.trim();
    }
    
    if (formData.category) {
      submitData.category = formData.category;
    }
    
    if (formData.lat && formData.lon) {
      submitData.lat = parseFloat(formData.lat);
      submitData.lon = parseFloat(formData.lon);
    }
    
    console.log("Sending data:", JSON.stringify(submitData, null, 2));
    
    try {
      const res = await api.post("/businesses/", submitData);
      console.log("=== SUCCESS ===");
      console.log("Response:", res.data);
      console.log("Business ID:", res.data.id);
      alert("Business created successfully! ID: " + res.data.id);
      
      // Call original onSubmit if needed
      if (onSubmit) {
        onSubmit();
      }
    } catch (err) {
      console.error("=== ERROR ===");
      console.error("Status:", err.response?.status);
      console.error("Data:", err.response?.data);
      alert("Error: " + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded shadow-sm space-y-3 text-sm">
        <div>
          <strong className="text-gray-900 dark:text-gray-100">{t("Jina la Biashara")}:</strong>{" "}
          <span className="text-gray-700 dark:text-gray-300">{formData.name || "-"}</span>
        </div>
        <div>
          <strong className="text-gray-900 dark:text-gray-100">{t("Maelezo ya Biashara")}:</strong>{" "}
          <span className="text-gray-700 dark:text-gray-300">{formData.description || "-"}</span>
        </div>
        <div>
          <strong className="text-gray-900 dark:text-gray-100">{t("Namba ya Simu")}:</strong>{" "}
          <span className="text-gray-700 dark:text-gray-300">{formData.phone || "-"}</span>
        </div>
        <div>
          <strong className="text-gray-900 dark:text-gray-100">{t("Barua Pepe")}:</strong>{" "}
          {formData.email ? (
            <a href={`mailto:${formData.email}`} className="text-blue-600 dark:text-blue-400 underline">
              {formData.email}
            </a>
          ) : (
            <span className="text-gray-700 dark:text-gray-300">-</span>
          )}
        </div>
        <div>
          <strong className="text-gray-900 dark:text-gray-100">{t("Tovuti")}:</strong>{" "}
          {formData.website ? (
            <a 
              href={formatWebsiteUrl(formData.website)} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="text-blue-600 dark:text-blue-400 underline"
            >
              {formData.website}
            </a>
          ) : (
            <span className="text-gray-700 dark:text-gray-300">-</span>
          )}
        </div>
        <div>
          <strong className="text-gray-900 dark:text-gray-100">{t("Taasisi")}:</strong>{" "}
          <span className="text-gray-700 dark:text-gray-300">{getInstitutionDisplay()}</span>
        </div>
        <div>
          <strong className="text-gray-900 dark:text-gray-100">{t("Aina ya Biashara")}:</strong>{" "}
          <span className="text-gray-700 dark:text-gray-300">{getCategoryDisplay()}</span>
        </div>
        <div>
          <strong className="text-gray-900 dark:text-gray-100">{t("Latitude")}:</strong>{" "}
          <span className="text-gray-700 dark:text-gray-300">{formData.lat ?? "-"}</span>
        </div>
        <div>
          <strong className="text-gray-900 dark:text-gray-100">{t("Longitude")}:</strong>{" "}
          <span className="text-gray-700 dark:text-gray-300">{formData.lon ?? "-"}</span>
        </div>
      </div>

      <div className="flex justify-between">
        <Button variant="outline" onClick={goBack} disabled={isSubmitting}>
          {t("Rudi")}
        </Button>
        <Button onClick={handleSubmitClick} disabled={isSubmitting}>
          {isSubmitting ? t("Inatuma...") : t("Thibitisha na Tuma")}
        </Button>
      </div>
    </div>
  );
}