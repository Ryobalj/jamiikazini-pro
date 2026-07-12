// src/app/kiini/pages/InstitutionSettingsPage.jsx

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams, Link } from "react-router-dom";
import api from "@/lib/axios";
import { ArrowLeft, Loader2, Settings, Users, Building, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";

export default function InstitutionSettingsPage() {
  const { t } = useTranslation("kiini");
  const navigate = useNavigate();
  const { id } = useParams();

  const [institution, setInstitution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .get(`/kiini/institutions/${id}/`)
      .then((res) => setInstitution(res.data))
      .catch(() => toast.error(t("settings.errors.load_failed") || "Imeshindwa kupakia taasisi."))
      .finally(() => setLoading(false));
  }, [id, t]);

  const toggleActive = async () => {
    setSaving(true);
    try {
      const res = await api.patch(`/kiini/institutions/${id}/`, { is_active: !institution.is_active });
      setInstitution(res.data);
      toast.success(t("settings.updated") || "Mipangilio imesasishwa.");
    } catch {
      toast.error(t("settings.errors.failed") || "Imeshindwa kusasisha.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!institution) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-6 text-center text-gray-500 dark:text-gray-400">
        {t("settings.not_found") || "Taasisi haikupatikana."}
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <button
        onClick={() => navigate(`/kiini/institutions/${id}`)}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        {t("back") || "Rudi"}
      </button>

      <Card className="mb-6">
        <CardHeader title={t("settings.title") || "Mipangilio ya Taasisi"} icon={<Settings className="w-5 h-5" />} divider />
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">{institution.name}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">{institution.domain || t("settings.no_domain") || "Hakuna domain"}</p>
            </div>
            <Link to={`/kiini/institutions/${id}/edit`}>
              <Button size="sm" variant="outline">
                <Pencil className="w-4 h-4 mr-1" />
                {t("settings.edit_profile") || "Hariri Taarifa"}
              </Button>
            </Link>
          </div>

          <div className="flex items-center justify-between py-3 border-t border-gray-100 dark:border-gray-700">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">
                {t("settings.is_active") || "Taasisi Inafanya Kazi"}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t("settings.is_active_hint") || "Ukizima, taasisi haitaonekana kwa umma."}
              </p>
            </div>
            <Button
              size="sm"
              disabled={saving}
              className={institution.is_active ? "bg-green-600 hover:bg-green-700" : "bg-gray-400 hover:bg-gray-500"}
              onClick={toggleActive}
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : institution.is_active ? t("settings.active") || "Hai" : t("settings.inactive") || "Imezimwa"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader title={t("settings.manage") || "Usimamizi"} divider />
        <CardContent className="space-y-2">
          <Link
            to="/kiini/dashboard/departments"
            className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
          >
            <Building className="w-5 h-5 text-purple-600" />
            <span className="text-gray-900 dark:text-white">{t("settings.departments") || "Idara"}</span>
          </Link>
          <Link
            to="/kiini/dashboard/staff-profiles"
            className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
          >
            <Users className="w-5 h-5 text-purple-600" />
            <span className="text-gray-900 dark:text-white">{t("settings.staff") || "Wafanyakazi"}</span>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
