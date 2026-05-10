// src/app/businesses/components/Step1BasicInfo.jsx

import React, { useState } from "react";
import InputField from "@/components/InputField";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Copy, Check, Info } from "lucide-react";
import api from "@/lib/axios";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui/tooltip";

export default function Step1BasicInfo({ formData, updateForm, goNext, goBack, errors }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const [checking, setChecking] = useState(false);
  const [domainAvailable, setDomainAvailable] = useState(null);

  const handleAutoWebsite = async () => {
    const name = formData.name?.toLowerCase().trim().replace(/\s+/g, "-");
    const institutionName = formData.institution_name?.toLowerCase().trim().replace(/\s+/g, "-");

    if (name && institutionName) {
      const domain =
        name === institutionName
          ? `${institutionName}.jamiikazini.com`
          : `${name}.${institutionName}.jamiikazini.com`;

      updateForm({ website: domain });

      // Check domain availability
      setChecking(true);
      try {
        const res = await api.get(`/businesses/check-domain/?domain=${domain}`);
        setDomainAvailable(res.data?.available);
      } catch (error) {
        console.error("Domain check failed:", error);
        setDomainAvailable(null);
      } finally {
        setChecking(false);
      }
    }
  };

  const handleNext = () => {
    if (!formData.name?.trim()) {
      updateForm({ name: "" });
      return;
    }
    goNext();
  };

  const handleCopy = () => {
    if (formData.website) {
      navigator.clipboard.writeText(formData.website);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <TooltipProvider>
      <div className="space-y-4">
        <InputField
          label={t("Jina la Biashara")}
          name="name"
          value={formData.name || ""}
          onChange={(e) => updateForm({ name: e.target.value })}
          error={errors.name}
          placeholder={t("Ingiza jina la biashara")}
          inputProps={{ style: { fontSize: "16px" } }}
        />

        <InputField
          label={t("Maelezo ya Biashara")}
          name="description"
          type="textarea"
          rows={3}
          value={formData.description || ""}
          onChange={(e) => updateForm({ description: e.target.value })}
          placeholder={t("Maelezo mafupi ya biashara")}
        />

        <InputField
          label={t("Namba ya Simu ya Biashara")}
          name="phone"
          type="tel"
          value={formData.phone || ""}
          onChange={(e) => updateForm({ phone: e.target.value })}
          placeholder={t("Mfano: +2557XXXXXXX")}
          inputProps={{ style: { fontSize: "16px" } }}
        />

        <InputField
          label={t("Barua Pepe ya Biashara")}
          name="email"
          type="email"
          value={formData.email || ""}
          onChange={(e) => updateForm({ email: e.target.value })}
          placeholder={t("Mfano: biashara@email.com")}
          inputProps={{ style: { fontSize: "16px" } }}
        />

        <div className="relative">
          <InputField
            label={
              <div className="flex items-center gap-1">
                {t("Anwani ya Tovuti ya Biashara")}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Info size={16} className="text-gray-400 cursor-pointer" />
                  </TooltipTrigger>
                  <TooltipContent className="text-xs max-w-xs">
                    {t("Mfano: biashara.jamiikazini.com, Jina hili hutegemea jina la biashara na taasisi.")}
                  </TooltipContent>
                </Tooltip>
              </div>
            }
            name="website"
            value={formData.website || ""}
            onChange={(e) => updateForm({ website: e.target.value })}
            onBlur={handleAutoWebsite}
            placeholder={t("Mfano: biashara.jamiikazini")}
            inputProps={{ style: { fontSize: "16px" } }}
          />

          {/* Website preview + copy */}
          {formData.website && (
            <div className="mt-1 flex items-center gap-2 text-sm text-blue-600 italic">
              <span>🌐 {formData.website}</span>
              <button
                type="button"
                onClick={handleCopy}
                className="text-blue-600 hover:text-blue-800"
                title={t("Nakili tovuti")}
              >
                {copied ? <Check size={16} /> : <Copy size={16} />}
              </button>
              {checking && <span className="text-xs text-gray-400">{t("Inakagua...")}</span>}
              {domainAvailable === false && (
                <span className="text-xs text-red-500">{t("Tovuti tayari imetumika")}</span>
              )}
              {domainAvailable === true && (
                <span className="text-xs text-green-600">{t("Tovuti inapatikana")}</span>
              )}
            </div>
          )}
        </div>

        {formData.created_institution_id && (
          <p className="text-sm text-gray-500 italic">
            {t("Anwani ya tovuti imeundwa kutokana na jina la biashara na taasisi")}
          </p>
        )}

        <div className="flex justify-between pt-4">
          <Button onClick={handleNext}>{t("Endelea")}</Button>
        </div>
      </div>
    </TooltipProvider>
  );
}