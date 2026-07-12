// src/app/kiini/pages/InstitutionTypes.jsx

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import api from "@/lib/axios";
import { Tag, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function InstitutionTypes() {
  const { t } = useTranslation("kiini");
  const [types, setTypes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/kiini/institution-types/")
      .then((res) => setTypes(res.data?.results || res.data || []))
      .catch(() => setTypes([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <Card>
        <CardHeader title={t("types.title") || "Aina za Taasisi"} icon={<Tag className="w-5 h-5" />} divider />
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : types.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
              {t("types.empty") || "Hakuna aina za taasisi bado."}
            </p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {types.map((ty) => (
                <div
                  key={ty.id}
                  className="px-3 py-2 rounded-lg bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 text-sm font-medium text-center"
                >
                  {ty.name}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
