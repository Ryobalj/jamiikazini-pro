// src/app/kiini/pages/StaffProfiles.jsx

import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import api from "@/lib/axios";
import { Users, Loader2, PlusCircle, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useAppContext } from "@/context/AppContext";

const EMPTY_FORM = { user_email: "", title: "", position: "", phone: "" };

export default function StaffProfiles() {
  const { t } = useTranslation("kiini");
  const { user } = useAppContext();
  const institutionId = user?.institution?.id;

  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const fetchStaff = useCallback(() => {
    if (!institutionId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    api
      .get(`/kiini/institutions/${institutionId}/staff-profiles/`)
      .then((res) => setStaff(res.data?.results || res.data || []))
      .catch(() => setStaff([]))
      .finally(() => setLoading(false));
  }, [institutionId]);

  useEffect(() => {
    fetchStaff();
  }, [fetchStaff]);

  const handleChange = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.user_email.trim()) {
      toast.error(t("staff.errors.email_required") || "Weka barua pepe ya mfanyakazi.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`/kiini/institutions/${institutionId}/staff-profiles/`, form);
      toast.success(t("staff.created") || "Mfanyakazi ameongezwa.");
      setForm(EMPTY_FORM);
      fetchStaff();
    } catch (error) {
      const errors = error.response?.data;
      const firstError = errors && typeof errors === "object" ? Object.values(errors)[0] : null;
      toast.error((Array.isArray(firstError) ? firstError[0] : firstError) || t("staff.errors.failed") || "Imeshindwa.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    setDeletingId(id);
    try {
      await api.delete(`/kiini/institutions/${institutionId}/staff-profiles/${id}/`);
      setStaff((prev) => prev.filter((s) => s.id !== id));
    } catch {
      toast.error(t("staff.errors.delete_failed") || "Imeshindwa kufuta.");
    } finally {
      setDeletingId(null);
    }
  };

  if (!institutionId) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-6 text-center text-gray-500 dark:text-gray-400">
        {t("staff.no_institution") || "Unahitaji kuwa na taasisi kwanza."}
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <Card>
        <CardHeader title={t("staff.add") || "Ongeza Mfanyakazi"} icon={<Users className="w-5 h-5" />} divider />
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="email"
              value={form.user_email}
              onChange={handleChange("user_email")}
              placeholder={t("staff.email") || "Barua pepe ya mfanyakazi (aliyeshajisajili)"}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            />
            <input
              type="text"
              value={form.title}
              onChange={handleChange("title")}
              placeholder={t("staff.title_field") || "Cheo (mfano: Meneja)"}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            />
            <input
              type="text"
              value={form.phone}
              onChange={handleChange("phone")}
              placeholder="+255..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            />
            <Button type="submit" disabled={submitting} className="bg-purple-600 hover:bg-purple-700">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <PlusCircle className="w-4 h-4 mr-2" />}
              {t("staff.submit") || "Ongeza"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader title={t("staff.title") || "Wafanyakazi"} divider />
        <CardContent>
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin mx-auto text-gray-400" />
          ) : staff.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("staff.empty") || "Hakuna wafanyakazi bado."}
            </p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {staff.map((s) => (
                <div key={s.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {s.user_full_name || s.user_email_display}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {s.title || t("staff.no_title") || "Bila cheo"}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={deletingId === s.id}
                    onClick={() => handleDelete(s.id)}
                  >
                    {deletingId === s.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4 text-red-500" />
                    )}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
