// src/app/kiini/pages/InstitutionTiers.jsx

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import api from "@/lib/axios";
import { Layers, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function InstitutionTiers() {
  const { t } = useTranslation("kiini");
  const [tiers, setTiers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/kiini/institution-tiers/")
      .then((res) => setTiers(res.data?.results || res.data || []))
      .catch(() => setTiers([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <Card>
        <CardHeader title={t("tiers.title") || "Viwango vya Taasisi"} icon={<Layers className="w-5 h-5" />} divider />
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : tiers.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
              {t("tiers.empty") || "Hakuna viwango bado."}
            </p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {tiers.map((tier) => (
                <div key={tier.id} className="py-3">
                  <p className="font-medium text-gray-900 dark:text-white">{tier.name_display || tier.name}</p>
                  {tier.description && (
                    <p className="text-sm text-gray-500 dark:text-gray-400">{tier.description}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
