// src/app/kiini/pages/InstitutionsListPage.jsx

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import api from "@/lib/axios";
import { Building2, Loader2, PlusCircle, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function InstitutionsListPage() {
  const { t } = useTranslation("kiini");
  const [institutions, setInstitutions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/kiini/institutions/")
      .then((res) => setInstitutions(res.data?.results || res.data || []))
      .catch(() => setInstitutions([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <Card>
        <CardHeader
          title={t("institutions_list.title") || "Taasisi Zangu"}
          icon={<Building2 className="w-5 h-5" />}
          actions={
            <Link to="/institutions/create">
              <Button size="sm" className="bg-purple-600 hover:bg-purple-700">
                <PlusCircle className="w-4 h-4 mr-1" />
                {t("institutions_list.new") || "Mpya"}
              </Button>
            </Link>
          }
          divider
        />
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : institutions.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
              {t("institutions_list.empty") || "Hujasajili taasisi yoyote bado."}
            </p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {institutions.map((inst) => (
                <Link
                  key={inst.id}
                  to={`/kiini/institutions/${inst.id}`}
                  className="flex items-center justify-between py-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 -mx-2 px-2 rounded-lg transition-colors"
                >
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{inst.name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {inst.type_name || t("institutions_list.no_type") || "Bila aina"}
                      {inst.is_active === false && ` · ${t("institutions_list.inactive") || "Imezimwa"}`}
                    </p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
