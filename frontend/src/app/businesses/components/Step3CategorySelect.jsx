import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import axios from "@/lib/axios";
import SelectInput from "@/components/SelectInput";
import { Button } from "@/components/ui/button";

export default function Step3CategorySelect({
  formData,
  updateForm,
  goNext,
  goBack,
  errors,
}) {
  const { t } = useTranslation();
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchCategories = async () => {
      setLoading(true);
      try {
        const res = await axios.get("/categories/");
        const options = res.data.map((cat) => ({
          value: cat.id,
          label: cat.name,
        }));
        setCategories(options);
      } catch (error) {
        console.error("Hitilafu ya kupata kategoria:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchCategories();
  }, []);

  const handleNext = () => {
    // ✅ Check institution exists (UUID or new name)
    if (!formData.institution && !formData.institution_name) {
      alert(t("Tafadhali chagua au unda taasisi kabla ya kuendelea."));
      return;
    }

    // ✅ Ensure category is selected
    if (!formData.category) {
      alert(t("Tafadhali chagua kategoria ya biashara."));
      return;
    }

    goNext();
  };

  return (
    <div className="space-y-4">

      <SelectInput
        label={t("Chagua Kategoria ya Biashara")}
        name="category"
        value={formData.category || ""}
        onChange={(e) => updateForm({ category: e.target.value })}
        options={categories}
        placeholder={t("Tafadhali chagua kategoria")}
        error={errors.category}
        loading={loading}
      />

      <div className="flex justify-between pt-4">
        <Button variant="outline" onClick={goBack}>
          {t("Rudi")}
        </Button>
        <Button onClick={handleNext}>
          {t("Endelea")}
        </Button>
      </div>
    </div>
  );
}