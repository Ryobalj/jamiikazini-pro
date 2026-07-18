// src/app/businesses/components/Step2InstitutionPicker.jsx

import React, { useEffect, useState } from "react";
import SelectInput from "@/components/SelectInput";
import InputField from "@/components/InputField";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import api from "@/lib/axios";
import { Plus, Loader2 } from "lucide-react";

export default function Step2InstitutionPicker({
  formData,
  updateForm,
  goNext,
  goBack,
  errors,
}) {
  const { t } = useTranslation();
  const [institutions, setInstitutions] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [tiers, setTiers] = useState([]);
  const [types, setTypes] = useState([]);
  const [newInstitutionData, setNewInstitutionData] = useState({
    name: "",
    domain: "",
    phone: "",
    email: "",
    address: "",
    tier: "",
    institution_type: "",
  });

  // Fetch institutions za user - SAHIHI URL
  useEffect(() => {
    const fetchInstitutions = async () => {
      setLoading(true);
      try {
        const res = await api.get("/institutions/my/");
        console.log("Institutions fetched:", res.data);
        
        let institutionsList = [];
        if (Array.isArray(res.data)) {
          institutionsList = res.data;
        } else if (res.data.results && Array.isArray(res.data.results)) {
          institutionsList = res.data.results;
        }
        
        setInstitutions(institutionsList);
        
        // Auto-pick if exactly one institution
        if (institutionsList.length === 1 && !formData.institution) {
          const firstInstitution = institutionsList[0];
          updateForm({
            institution: firstInstitution.id,
            institution_name: firstInstitution.name,
            create_new_institution: false,
          });
          
          setTimeout(() => {
            goNext();
          }, 300);
        }
      } catch (error) {
        console.error("Failed to fetch institutions:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchInstitutions();
  }, []);

  // Fetch tiers na types
  useEffect(() => {
    const fetchTiersAndTypes = async () => {
      try {
        const [tiersRes, typesRes] = await Promise.all([
          api.get("/kiini/institution-tiers/"),
          api.get("/kiini/institution-types/")
        ]);
        
        const tiersList = tiersRes.data.results || tiersRes.data;
        const typesList = typesRes.data.results || typesRes.data;
        
        setTiers(Array.isArray(tiersList) ? tiersList : []);
        setTypes(Array.isArray(typesList) ? typesList : []);
      } catch (error) {
        console.error("Failed to fetch tiers/types:", error);
      }
    };
    fetchTiersAndTypes();
  }, []);

  // Build website domain
  useEffect(() => {
    const name = formData.name?.toLowerCase().trim().replace(/\s+/g, "-");
    const selectedInstitution = institutions.find(i => i.id === formData.institution);
    const institutionName = (
      formData.institution_name || selectedInstitution?.name || ""
    ).toLowerCase().trim().replace(/\s+/g, "-");

    if (name && institutionName) {
      const domain =
        name === institutionName
          ? `${institutionName}.jamiikazini.com`
          : `${name}.${institutionName}.jamiikazini.com`;

      if (!formData.website || formData.website !== domain) {
        updateForm({ website: domain });
      }
    }
  }, [formData.institution, formData.institution_name, formData.name, institutions, updateForm]);

  const handleInstitutionSelect = (e) => {
    const selectedId = e.target.value;
    if (selectedId) {
      const selected = institutions.find(i => i.id === selectedId);
      updateForm({ 
        institution: selectedId,
        institution_name: selected?.name || "",
        create_new_institution: false,
      });
    }
  };

  const handleCreateNewInstitution = async () => {
    const institutionName = newInstitutionData.name.trim() || formData.name?.trim();
    
    if (!institutionName) {
      alert(t("Tafadhali jaza jina la taasisi."));
      return;
    }

    setCreating(true);
    
    try {
      const institutionData = {
        name: institutionName,
        phone: newInstitutionData.phone.trim() || formData.phone || "",
        email: newInstitutionData.email.trim() || formData.email || "",
        address: newInstitutionData.address.trim() || "",
      };

      if (newInstitutionData.domain.trim()) {
        institutionData.domain = newInstitutionData.domain.trim();
      }
      if (newInstitutionData.tier) {
        institutionData.tier = newInstitutionData.tier;
      }
      if (newInstitutionData.institution_type) {
        institutionData.institution_type = newInstitutionData.institution_type;
      }

      console.log("Creating institution:", institutionData);

      const res = await api.post("/kiini/institutions/", institutionData);
      
      console.log("Institution created:", res.data);
      
      updateForm({
        institution: res.data.id,
        institution_name: res.data.name,
        create_new_institution: true,
      });
      
      // Refresh institutions list
      const institutionsRes = await api.get("/institutions/my/");
      const institutionsList = Array.isArray(institutionsRes.data) 
        ? institutionsRes.data 
        : institutionsRes.data.results || [];
      setInstitutions(institutionsList);
      
      setShowCreateForm(false);
      setNewInstitutionData({
        name: "",
        domain: "",
        phone: "",
        email: "",
        address: "",
        tier: "",
        institution_type: "",
      });
      
      alert(t("Taasisi imeundwa kikamilifu!"));
      
    } catch (error) {
      console.error("Failed to create institution:", error.response?.data);
      
      let errorMsg = t("Imeshindwa kuunda taasisi");
      const errorData = error.response?.data;
      
      if (errorData) {
        if (errorData.name) {
          errorMsg = Array.isArray(errorData.name) ? errorData.name[0] : errorData.name;
        } else if (errorData.domain) {
          errorMsg = "Domain: " + (Array.isArray(errorData.domain) ? errorData.domain[0] : errorData.domain);
        } else if (errorData.detail) {
          errorMsg = errorData.detail;
        }
      }
      
      alert(errorMsg);
    } finally {
      setCreating(false);
    }
  };

  const institutionOptions = institutions.map((i) => ({
    value: i.id,
    label: i.name,
  }));

  const tierOptions = tiers.map((t) => ({
    value: t.id,
    label: t.name_display || t.name,
  }));

  const typeOptions = types.map((t) => ({
    value: t.id,
    label: t.name_display || t.name,
  }));

  // Loading state
  if (loading) {
    return (
      <div className="text-center py-8">
        <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600" />
        <p className="text-gray-500 dark:text-gray-400 mt-2">
          {t("Inakagua taasisi zako...")}
        </p>
      </div>
    );
  }

  // Kama user ana institutions
  if (institutions.length > 0 && !showCreateForm) {
    return (
      <div className="space-y-4">
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <SelectInput
              label={t("Chagua Taasisi")}
              name="institution"
              value={formData.institution || ""}
              onChange={handleInstitutionSelect}
              options={institutionOptions}
              placeholder={t("Chagua taasisi")}
              error={errors.institution}
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCreateForm(true)}
            className="mb-0.5"
            title={t("Unda taasisi mpya")}
          >
            <Plus size={16} />
          </Button>
        </div>

        <div className="flex justify-between pt-4">
          <Button onClick={goBack} variant="outline">
            {t("Rudi")}
          </Button>
          <Button
            onClick={() => {
              if (formData.institution) {
                goNext();
              } else {
                alert(t("Tafadhali chagua taasisi ili kuendelea."));
              }
            }}
          >
            {t("Endelea")}
          </Button>
        </div>
      </div>
    );
  }

  // Onyesha form ya kuunda
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {institutions.length === 0 
            ? t("Huna taasisi yoyote bado. Jaza taarifa za taasisi mpya.")
            : t("Jaza taarifa za taasisi mpya")}
        </p>
        {institutions.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setShowCreateForm(false);
              setNewInstitutionData({
                name: "",
                domain: "",
                phone: "",
                email: "",
                address: "",
                tier: "",
                institution_type: "",
              });
            }}
          >
            {t("Ghairi")}
          </Button>
        )}
      </div>

      <InputField
        label={t("Jina la Taasisi") + " *"}
        name="institution_name_new"
        value={newInstitutionData.name}
        onChange={(e) => setNewInstitutionData({ ...newInstitutionData, name: e.target.value })}
        placeholder={formData.name || t("Jina la taasisi")}
        inputProps={{ style: { fontSize: "16px" } }}
      />

      <InputField
        label={t("Domain (Hiari)")}
        name="institution_domain"
        value={newInstitutionData.domain}
        onChange={(e) => setNewInstitutionData({ ...newInstitutionData, domain: e.target.value })}
        placeholder={t("Mfano: taasisi.jamiikazini.com")}
        inputProps={{ style: { fontSize: "16px" } }}
      />

      <SelectInput
        label={t("Kiwango cha Taasisi (Hiari)")}
        name="tier"
        value={newInstitutionData.tier}
        onChange={(e) => setNewInstitutionData({ ...newInstitutionData, tier: e.target.value })}
        options={tierOptions}
        placeholder={t("Chagua kiwango")}
      />

      <SelectInput
        label={t("Aina ya Taasisi (Hiari)")}
        name="institution_type"
        value={newInstitutionData.institution_type}
        onChange={(e) => setNewInstitutionData({ ...newInstitutionData, institution_type: e.target.value })}
        options={typeOptions}
        placeholder={t("Chagua aina")}
      />

      <InputField
        label={t("Namba ya Simu (Hiari)")}
        name="institution_phone"
        value={newInstitutionData.phone}
        onChange={(e) => setNewInstitutionData({ ...newInstitutionData, phone: e.target.value })}
        placeholder={formData.phone || t("Mfano: +2557XXXXXXX")}
        inputProps={{ style: { fontSize: "16px" } }}
      />

      <InputField
        label={t("Barua Pepe (Hiari)")}
        name="institution_email"
        type="email"
        value={newInstitutionData.email}
        onChange={(e) => setNewInstitutionData({ ...newInstitutionData, email: e.target.value })}
        placeholder={formData.email || t("Mfano: taasisi@email.com")}
        inputProps={{ style: { fontSize: "16px" } }}
      />

      <InputField
        label={t("Anwani (Hiari)")}
        name="institution_address"
        value={newInstitutionData.address}
        onChange={(e) => setNewInstitutionData({ ...newInstitutionData, address: e.target.value })}
        placeholder={t("Anwani ya taasisi")}
        inputProps={{ style: { fontSize: "16px" } }}
      />

      <div className="flex justify-between pt-4">
        <Button 
          variant="outline" 
          onClick={() => {
            if (institutions.length > 0) {
              setShowCreateForm(false);
            } else {
              goBack();
            }
          }} 
          disabled={creating}
        >
          {institutions.length > 0 ? t("Ghairi") : t("Rudi")}
        </Button>
        <Button onClick={handleCreateNewInstitution} disabled={creating}>
          {creating ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              {t("Inaunda...")}
            </>
          ) : (
            t("Unda Taasisi")
          )}
        </Button>
      </div>
    </div>
  );
}