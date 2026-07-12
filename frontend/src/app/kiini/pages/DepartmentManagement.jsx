// src/app/kiini/pages/DepartmentManagement.jsx

import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import api from "@/lib/axios";
import { Layers, Loader2, PlusCircle, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useAppContext } from "@/context/AppContext";

export default function DepartmentManagement() {
  const { t } = useTranslation("kiini");
  const { user } = useAppContext();
  const institutionId = user?.institution?.id;

  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const fetchDepartments = useCallback(() => {
    if (!institutionId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    api
      .get(`/kiini/institutions/${institutionId}/departments/`)
      .then((res) => setDepartments(res.data?.results || res.data || []))
      .catch(() => setDepartments([]))
      .finally(() => setLoading(false));
  }, [institutionId]);

  useEffect(() => {
    fetchDepartments();
  }, [fetchDepartments]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error(t("departments.errors.name_required") || "Weka jina la idara.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`/kiini/institutions/${institutionId}/departments/`, {
        name: name.trim(),
        description: description.trim(),
      });
      toast.success(t("departments.created") || "Idara imeongezwa.");
      setName("");
      setDescription("");
      fetchDepartments();
    } catch (error) {
      toast.error(error.response?.data?.detail || t("departments.errors.failed") || "Imeshindwa.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    setDeletingId(id);
    try {
      await api.delete(`/kiini/institutions/${institutionId}/departments/${id}/`);
      setDepartments((prev) => prev.filter((d) => d.id !== id));
    } catch {
      toast.error(t("departments.errors.delete_failed") || "Imeshindwa kufuta.");
    } finally {
      setDeletingId(null);
    }
  };

  if (!institutionId) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-6 text-center text-gray-500 dark:text-gray-400">
        {t("departments.no_institution") || "Unahitaji kuwa na taasisi kwanza."}
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <Card>
        <CardHeader title={t("departments.add") || "Ongeza Idara"} icon={<Layers className="w-5 h-5" />} divider />
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t("departments.name") || "Jina la Idara"}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            />
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t("departments.description_placeholder") || "Maelezo (hiari)"}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            />
            <Button type="submit" disabled={submitting} className="bg-purple-600 hover:bg-purple-700">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <PlusCircle className="w-4 h-4 mr-2" />}
              {t("departments.submit") || "Ongeza"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader title={t("departments.title") || "Idara"} divider />
        <CardContent>
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin mx-auto text-gray-400" />
          ) : departments.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("departments.empty") || "Hakuna idara bado."}
            </p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {departments.map((dept) => (
                <div key={dept.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{dept.name}</p>
                    {dept.description && (
                      <p className="text-sm text-gray-500 dark:text-gray-400">{dept.description}</p>
                    )}
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={deletingId === dept.id}
                    onClick={() => handleDelete(dept.id)}
                  >
                    {deletingId === dept.id ? (
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
