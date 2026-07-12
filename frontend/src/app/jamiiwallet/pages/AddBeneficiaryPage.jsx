// src/app/jamiiwallet/pages/AddBeneficiaryPage.jsx

import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import { ArrowLeft, Loader2, UserPlus, Send, Trash2, BadgeCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";

export default function AddBeneficiaryPage() {
  const { t } = useTranslation("jamiiwallet");
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [beneficiaries, setBeneficiaries] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [deletingId, setDeletingId] = useState(null);

  const fetchBeneficiaries = useCallback(() => {
    setLoadingList(true);
    api
      .get("/jamiiwallet/beneficiaries/")
      .then((res) => setBeneficiaries(res.data?.results || res.data || []))
      .catch(() => setBeneficiaries([]))
      .finally(() => setLoadingList(false));
  }, []);

  useEffect(() => {
    fetchBeneficiaries();
  }, [fetchBeneficiaries]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !identifier.trim()) {
      toast.error(t("beneficiary.errors.required") || "Jaza jina na namba/email.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/jamiiwallet/beneficiaries/", { name: name.trim(), identifier: identifier.trim() });
      toast.success(t("beneficiary.success") || "Mpokeaji ameongezwa.");
      setName("");
      setIdentifier("");
      fetchBeneficiaries();
    } catch (error) {
      const errors = error.response?.data?.errors || error.response?.data;
      const firstError =
        (errors && typeof errors === "object" && Object.values(errors)[0]) || error.response?.data?.detail;
      toast.error((Array.isArray(firstError) ? firstError[0] : firstError) || t("beneficiary.errors.failed") || "Imeshindwa.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    setDeletingId(id);
    try {
      await api.delete(`/jamiiwallet/beneficiaries/${id}/`);
      setBeneficiaries((prev) => prev.filter((b) => b.id !== id));
    } catch {
      toast.error(t("beneficiary.errors.delete_failed") || "Imeshindwa kufuta.");
    } finally {
      setDeletingId(null);
    }
  };

  const sendTo = (identifier) => {
    navigate(`/jamiiwallet/send?recipient=${encodeURIComponent(identifier)}`);
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <button
        onClick={() => navigate("/jamiiwallet")}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        {t("back") || "Rudi"}
      </button>

      <Card className="mb-6">
        <CardHeader title={t("beneficiary.title") || "Ongeza Mpokeaji"} icon={<UserPlus className="w-5 h-5" />} divider />
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("beneficiary.name") || "Jina la kumbukumbu"}
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Mfano: Mama, Rafiki John"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("beneficiary.identifier") || "Namba ya simu au barua pepe"}
              </label>
              <input
                type="text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="+255XXXXXXXXX au email@mfano.com"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <Button type="submit" disabled={submitting} className="w-full bg-purple-600 hover:bg-purple-700">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <UserPlus className="w-4 h-4 mr-2" />}
              {submitting ? t("beneficiary.saving") || "Inahifadhi..." : t("beneficiary.submit") || "Hifadhi"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader title={t("beneficiary.saved") || "Wapokeaji Waliohifadhiwa"} divider />
        <CardContent>
          {loadingList ? (
            <Loader2 className="w-5 h-5 animate-spin mx-auto text-gray-400" />
          ) : beneficiaries.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("beneficiary.empty") || "Hujahifadhi mpokeaji yeyote bado."}
            </p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {beneficiaries.map((b) => (
                <div key={b.id} className="flex items-center justify-between py-3">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <p className="font-medium text-gray-900 dark:text-white">{b.name}</p>
                      {b.is_registered && <BadgeCheck className="w-4 h-4 text-purple-500" />}
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{b.identifier}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" className="bg-purple-600 hover:bg-purple-700" onClick={() => sendTo(b.identifier)}>
                      <Send className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={deletingId === b.id}
                      onClick={() => handleDelete(b.id)}
                    >
                      {deletingId === b.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4 text-red-500" />
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
