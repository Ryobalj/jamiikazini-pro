// src/app/kiini/pages/InstitutionFormPage.jsx

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import api from "@/lib/axios";
import { ArrowLeft, Loader2, Building2, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";

const EMPTY_FORM = { name: "", email: "", phone: "", address: "", domain: "", institution_type: "", tier: "" };

export default function InstitutionFormPage() {
  const { t } = useTranslation("kiini");
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);

  const [form, setForm] = useState(EMPTY_FORM);
  const [types, setTypes] = useState([]);
  const [tiers, setTiers] = useState([]);
  const [loading, setLoading] = useState(isEdit);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get("/kiini/institution-types/").then((res) => setTypes(res.data?.results || res.data || [])).catch(() => {});
    api.get("/kiini/institution-tiers/").then((res) => setTiers(res.data?.results || res.data || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (!isEdit) return;
    api
      .get(`/kiini/institutions/${id}/`)
      .then((res) => {
        const inst = res.data;
        setForm({
          name: inst.name || "",
          email: inst.email || "",
          phone: inst.phone || "",
          address: inst.address || "",
          domain: inst.domain || "",
          institution_type: inst.institution_type || "",
          tier: inst.tier || "",
        });
      })
      .catch(() => toast.error(t("form.errors.load_failed") || "Imeshindwa kupakia taasisi."))
      .finally(() => setLoading(false));
  }, [id, isEdit, t]);

  const handleChange = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) {
      toast.error(t("form.errors.name_required") || "Weka jina la taasisi.");
      return;
    }
    setSubmitting(true);
    const payload = {
      ...form,
      institution_type: form.institution_type || null,
      tier: form.tier || null,
    };
    try {
      if (isEdit) {
        await api.patch(`/kiini/institutions/${id}/`, payload);
        toast.success(t("form.updated") || "Taasisi imesasishwa.");
        navigate(`/kiini/institutions/${id}`);
      } else {
        const res = await api.post("/kiini/institutions/", payload);
        toast.success(t("form.created") || "Taasisi imeundwa.");
        navigate(`/kiini/institutions/${res.data.id}`);
      }
    } catch (error) {
      const errors = error.response?.data;
      const firstError = errors && typeof errors === "object" ? Object.values(errors)[0] : null;
      toast.error((Array.isArray(firstError) ? firstError[0] : firstError) || t("form.errors.failed") || "Imeshindwa.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        {t("back") || "Rudi"}
      </button>

      <Card>
        <CardHeader
          title={isEdit ? t("form.edit_title") || "Hariri Taasisi" : t("form.create_title") || "Sajili Taasisi"}
          icon={<Building2 className="w-5 h-5" />}
          divider
        />
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Field label={t("form.name") || "Jina la Taasisi"} value={form.name} onChange={handleChange("name")} required />
            <Field label={t("form.email") || "Barua Pepe"} type="email" value={form.email} onChange={handleChange("email")} />
            <Field label={t("form.phone") || "Simu"} value={form.phone} onChange={handleChange("phone")} placeholder="+255..." />
            <Field label={t("form.address") || "Anwani"} value={form.address} onChange={handleChange("address")} />
            <Field
              label={t("form.domain") || "Domain (subdomain)"}
              value={form.domain}
              onChange={handleChange("domain")}
              placeholder="jinalataasisi"
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("form.institution_type") || "Aina ya Taasisi"}
              </label>
              <select
                value={form.institution_type}
                onChange={handleChange("institution_type")}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
              >
                <option value="">{t("form.select") || "Chagua..."}</option>
                {types.map((ty) => (
                  <option key={ty.id} value={ty.id}>{ty.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("form.tier") || "Kiwango (Tier)"}
              </label>
              <select
                value={form.tier}
                onChange={handleChange("tier")}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
              >
                <option value="">{t("form.select") || "Chagua..."}</option>
                {tiers.map((tr) => (
                  <option key={tr.id} value={tr.id}>{tr.name}</option>
                ))}
              </select>
            </div>

            <Button type="submit" disabled={submitting} className="w-full bg-purple-600 hover:bg-purple-700">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
              {submitting ? t("form.saving") || "Inahifadhi..." : t("form.save") || "Hifadhi"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function Field({ label, value, onChange, type = "text", placeholder, required }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
      />
    </div>
  );
}
