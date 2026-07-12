// src/app/kiini/pages/KiiniDashboard.jsx

import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Building2, Users, Layers, Tag, PlusCircle } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useAppContext } from "@/context/AppContext";

const LINKS = [
  { to: "/kiini/dashboard/institutions", icon: Building2, label: "Taasisi Zangu" },
  { to: "/kiini/dashboard/departments", icon: Layers, label: "Idara" },
  { to: "/kiini/dashboard/staff-profiles", icon: Users, label: "Wafanyakazi" },
  { to: "/kiini/dashboard/institution-types", icon: Tag, label: "Aina za Taasisi" },
  { to: "/kiini/dashboard/institution-tiers", icon: Tag, label: "Viwango vya Taasisi" },
];

export default function KiiniDashboard() {
  const { t } = useTranslation("kiini");
  const { user } = useAppContext();

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          {t("dashboard.title") || "Dashibodi ya Taasisi"}
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          {t("dashboard.welcomeMessage") || "Karibu"}, {user?.full_name || user?.email}
        </p>
      </div>

      {user?.institution ? (
        <Card>
          <CardHeader title={t("dashboard.your_institution") || "Taasisi Yako"} icon={<Building2 className="w-5 h-5" />} divider />
          <CardContent>
            <Link
              to={`/kiini/institutions/${user.institution.id}`}
              className="font-medium text-purple-600 dark:text-purple-400 hover:underline"
            >
              {user.institution.name}
            </Link>
            {user.institution.domain && (
              <p className="text-sm text-gray-500 dark:text-gray-400">{user.institution.domain}</p>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="text-center py-6">
            <p className="text-gray-500 dark:text-gray-400 mb-3">
              {t("dashboard.no_institution") || "Bado hujajiunga na taasisi yoyote."}
            </p>
            <Link
              to="/institutions/create"
              className="inline-flex items-center gap-1 text-purple-600 dark:text-purple-400 font-medium hover:underline"
            >
              <PlusCircle className="w-4 h-4" />
              {t("dashboard.create_institution") || "Sajili Taasisi"}
            </Link>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {LINKS.map(({ to, icon: Icon, label }) => (
          <Link
            key={to}
            to={to}
            className="flex flex-col items-center justify-center gap-2 p-5 bg-white dark:bg-gray-800 rounded-2xl shadow-soft hover:shadow-medium transition-shadow"
          >
            <Icon className="w-6 h-6 text-purple-600" />
            <span className="text-sm text-center text-gray-700 dark:text-gray-200">{label}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
