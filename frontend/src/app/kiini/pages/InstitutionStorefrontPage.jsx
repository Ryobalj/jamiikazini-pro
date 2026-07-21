// src/app/kiini/pages/InstitutionStorefrontPage.jsx
//
// Public "venue" page for an Institution that houses several tenant
// Businesses (e.g. a shopping mall like Mlimani City) - lets a shopper
// browse every active shop under one roof from a single page instead of
// finding each one separately via nearby search.

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Building2, Loader2, Phone, Mail, MapPin, Store, ShieldCheck, Package, Wrench } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import api from "@/lib/axios";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";

export default function InstitutionStorefrontPage() {
  const { id: institutionId } = useParams();
  const { t } = useTranslation("kiini");
  const navigate = useNavigate();

  const [institution, setInstitution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useDocumentTitle(institution?.name);

  useEffect(() => {
    if (!institutionId) return;
    setLoading(true);
    api
      .get(`/kiini/institutions/${institutionId}/public/`)
      .then((res) => setInstitution(res.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [institutionId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !institution) {
    return (
      <div className="text-center py-20">
        <Building2 className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
        <p className="text-gray-500 dark:text-gray-400">
          {t("institution_storefront.not_found", "Jengo/taasisi hii haipatikani.")}
        </p>
      </div>
    );
  }

  const businesses = institution.businesses || [];

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row sm:items-start gap-4">
            <div className="w-16 h-16 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0">
              <Building2 className="w-8 h-8 text-purple-600 dark:text-purple-400" />
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{institution.name}</h1>
              {institution.type_name && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{institution.type_name}</p>
              )}

              <div className="flex flex-wrap gap-4 mt-3 text-sm text-gray-500 dark:text-gray-400">
                {institution.address && (
                  <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {institution.address}</span>
                )}
                {institution.phone && (
                  <span className="flex items-center gap-1"><Phone className="w-3.5 h-3.5" /> {institution.phone}</span>
                )}
                {institution.email && (
                  <span className="flex items-center gap-1"><Mail className="w-3.5 h-3.5" /> {institution.email}</span>
                )}
              </div>

              <p className="text-sm font-medium text-purple-600 dark:text-purple-400 mt-3">
                {t("institution_storefront.tenant_count", { count: businesses.length }) ||
                  `${businesses.length} ${t("institution_storefront.tenants_heading", "Maduka")}`}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tenant businesses */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
          {t("institution_storefront.tenants_heading", "Maduka Ndani ya Jengo Hili")}
        </h2>

        {businesses.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
            {t("institution_storefront.empty", "Hakuna duka lililosajiliwa hapa bado.")}
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {businesses.map((business) => (
              <Card
                key={business.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => navigate(`/store/${business.id}`)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900 flex items-center justify-center flex-shrink-0">
                      <Store className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">{business.name}</h3>
                        {business.is_verified && (
                          <ShieldCheck className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" />
                        )}
                      </div>
                      {business.category_name && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{business.category_name}</p>
                      )}
                      {business.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 line-clamp-2">
                          {business.description}
                        </p>
                      )}
                      <div className="flex flex-wrap gap-3 mt-3 text-xs text-gray-500 dark:text-gray-400">
                        {business.product_count > 0 && (
                          <span className="flex items-center gap-1">
                            <Package className="w-3.5 h-3.5" /> {business.product_count}
                          </span>
                        )}
                        {business.service_count > 0 && (
                          <span className="flex items-center gap-1">
                            <Wrench className="w-3.5 h-3.5" /> {business.service_count}
                          </span>
                        )}
                        {business.phone && (
                          <span className="flex items-center gap-1">
                            <Phone className="w-3.5 h-3.5" /> {business.phone}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
