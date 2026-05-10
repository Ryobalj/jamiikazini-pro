import React from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import InputField from "@/components/InputField";

export default function Step4LocationPicker({
  formData,
  updateForm,
  goNext,
  goBack,
  errors,
}) {
  const { t } = useTranslation();

  const handleUseGPS = () => {
    if (!navigator.geolocation) {
      alert(t("Kipengele cha GPS hakipatikani kwenye kifaa chako."));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        updateForm({ lat: latitude, lon: longitude });
      },
      (error) => {
        console.error("GPS Error:", error);
        alert(t("Imeshindikana kupata eneo. Tafadhali hakikisha GPS imewashwa."));
      }
    );
  };

  return (
    <div className="space-y-4">
      <InputField
        label={t("Latitude")}
        name="lat"
        type="number"
        value={formData.lat || ""}
        onChange={(e) => updateForm({ lat: parseFloat(e.target.value) })}
        placeholder={t("Ingiza latitude ya eneo")}
        error={errors.location}
      />

      <InputField
        label={t("Longitude")}
        name="lon"
        type="number"
        value={formData.lon || ""}
        onChange={(e) => updateForm({ lon: parseFloat(e.target.value) })}
        placeholder={t("Ingiza longitude ya eneo")}
        error={errors.location}
      />

      <div className="flex justify-between items-center">
        <Button variant="outline" onClick={goBack}>
          {t("Rudi")}
        </Button>

        <div className="space-x-2">
          <Button variant="secondary" onClick={handleUseGPS}>
            {t("Tumia GPS ya Simu")}
          </Button>
          <Button onClick={goNext}>{t("Endelea")}</Button>
        </div>
      </div>
    </div>
  );
}