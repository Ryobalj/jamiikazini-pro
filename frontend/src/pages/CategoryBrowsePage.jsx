// src/pages/CategoryBrowsePage.jsx

import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ChevronRight, Store, BadgeCheck, Loader2, LayoutGrid } from "lucide-react";
import api from "@/lib/axios";

export default function CategoryBrowsePage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  const [category, setCategory] = useState(null);
  const [businesses, setBusinesses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.get(`/categories/${slug}/`).catch(() => null),
      api.get(`/categories/${slug}/businesses/`).catch(() => ({ data: [] })),
    ]).then(([categoryRes, businessesRes]) => {
      setCategory(categoryRes?.data ?? null);
      setBusinesses(businessesRes.data ?? []);
      setLoading(false);
    });
  }, [slug, i18n.language]);

  return (
    <div className="font-sans px-4 py-8 sm:px-8 space-y-6">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
      >
        <ChevronRight className="w-4 h-4 rotate-180" />
        {t("topbar.back", "Rudi")}
      </button>

      <div className="flex items-center gap-2">
        <LayoutGrid className="w-6 h-6 text-purple-600" />
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
          {category?.name || slug}
        </h1>
      </div>
      {category?.description && (
        <p className="text-sm text-gray-500 dark:text-gray-400 -mt-4">{category.description}</p>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        </div>
      ) : businesses.length === 0 ? (
        <p className="text-sm text-gray-400 dark:text-gray-500">
          {t("category.empty", "Bado hakuna biashara katika aina hii.")}
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {businesses.map((b) => (
            <button
              key={b.id}
              onClick={() => navigate(`/store/${b.id}`)}
              className="text-left rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 hover:shadow-md transition flex items-start gap-3"
            >
              <div className="w-10 h-10 rounded-full bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center shrink-0">
                <Store className="w-5 h-5 text-blue-500" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1">
                  <p className="font-medium text-gray-900 dark:text-white truncate">{b.name}</p>
                  {b.is_verified && <BadgeCheck className="w-4 h-4 text-emerald-500 shrink-0" />}
                </div>
                {b.description && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{b.description}</p>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
