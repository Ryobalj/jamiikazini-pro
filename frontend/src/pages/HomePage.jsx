// src/pages/HomePage.jsx

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { TrendingUp, Megaphone, Store, Loader2, Wrench, BadgeCheck, LayoutGrid } from "lucide-react";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";

export default function HomePage() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const { formatCurrency } = useCurrency();

  const [trending, setTrending] = useState([]);
  const [loadingTrending, setLoadingTrending] = useState(true);
  const [trendingServices, setTrendingServices] = useState([]);
  const [loadingTrendingServices, setLoadingTrendingServices] = useState(true);
  const [featured, setFeatured] = useState([]);
  const [loadingFeatured, setLoadingFeatured] = useState(true);
  const [verifiedBusinesses, setVerifiedBusinesses] = useState([]);
  const [loadingVerifiedBusinesses, setLoadingVerifiedBusinesses] = useState(true);
  const [categories, setCategories] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(true);

  useEffect(() => {
    api
      .get("/products/trending/")
      .then((res) => setTrending(res.data))
      .catch(() => setTrending([]))
      .finally(() => setLoadingTrending(false));

    api
      .get("/services/trending/")
      .then((res) => setTrendingServices(res.data))
      .catch(() => setTrendingServices([]))
      .finally(() => setLoadingTrendingServices(false));

    api
      .get("/featured-listings/active/")
      .then((res) => setFeatured(res.data))
      .catch(() => setFeatured([]))
      .finally(() => setLoadingFeatured(false));

    api
      .get("/businesses/verified/")
      .then((res) => setVerifiedBusinesses(res.data))
      .catch(() => setVerifiedBusinesses([]))
      .finally(() => setLoadingVerifiedBusinesses(false));

    api
      .get("/categories/top/")
      .then((res) => setCategories(res.data))
      .catch(() => setCategories([]))
      .finally(() => setLoadingCategories(false));
  }, [i18n.language]);

  return (
    <div className="font-sans px-4 py-8 sm:px-8 space-y-10">
      {/* Sponsored / Featured listings */}
      {!loadingFeatured && featured.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Megaphone className="w-5 h-5 text-amber-500" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t("home.sponsored_heading", "Matangazo Yaliyodhaminiwa")}
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {featured.map((f) => (
              <button
                key={f.id}
                onClick={() => navigate(`/store/${f.business_id}`)}
                className="text-left rounded-xl border border-amber-200 dark:border-amber-900/50 bg-amber-50 dark:bg-amber-900/10 overflow-hidden hover:shadow-md transition"
              >
                {f.product_image ? (
                  <img src={f.product_image} alt={f.product_name || f.business_name} className="w-full h-28 object-cover" />
                ) : (
                  <div className="w-full h-28 bg-amber-100 dark:bg-amber-900/20 flex items-center justify-center">
                    <Store className="w-8 h-8 text-amber-400" />
                  </div>
                )}
                <div className="p-3">
                  <p className="text-xs uppercase tracking-wide text-amber-600 dark:text-amber-400 font-medium">
                    {t("home.sponsored_tag", "Tangazo")}
                  </p>
                  <p className="font-medium text-gray-900 dark:text-white truncate">
                    {f.product_name || f.business_name}
                  </p>
                  {f.product_price != null && (
                    <p className="text-sm text-blue-600 dark:text-blue-400 font-semibold mt-0.5">
                      {formatCurrency(f.product_price)}
                    </p>
                  )}
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">{f.business_name}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Trending products */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("home.trending_heading", "Bidhaa Maarufu")}
          </h2>
        </div>

        {loadingTrending ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : trending.length === 0 ? (
          <p className="text-sm text-gray-400 dark:text-gray-500">
            {t("home.trending_empty", "Bado hakuna bidhaa za kuonesha.")}
          </p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {trending.map((p) => (
              <button
                key={p.id}
                onClick={() => navigate(`/store/${p.business_id}`)}
                className="text-left rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-md transition bg-white dark:bg-gray-800"
              >
                {p.image ? (
                  <img src={p.image} alt={p.name} className="w-full h-24 object-cover" />
                ) : (
                  <div className="w-full h-24 bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                    <Store className="w-6 h-6 text-gray-300 dark:text-gray-600" />
                  </div>
                )}
                <div className="p-2">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{p.name}</p>
                  <p className="text-xs text-blue-600 dark:text-blue-400 font-semibold">
                    {formatCurrency(p.final_price ?? p.price)}
                  </p>
                  <p className="text-[11px] text-gray-400 dark:text-gray-500 truncate">{p.business_name}</p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Trending services */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Wrench className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("home.trending_services_heading", "Huduma Maarufu")}
          </h2>
        </div>

        {loadingTrendingServices ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : trendingServices.length === 0 ? (
          <p className="text-sm text-gray-400 dark:text-gray-500">
            {t("home.trending_services_empty", "Bado hakuna huduma za kuonesha.")}
          </p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {trendingServices.map((s) => (
              <button
                key={s.id}
                onClick={() => navigate(`/store/${s.business_id}`)}
                className="text-left rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-md transition bg-white dark:bg-gray-800 p-3"
              >
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{s.name}</p>
                <p className="text-xs text-blue-600 dark:text-blue-400 font-semibold">
                  {formatCurrency(s.price)}
                  {s.billing_type_display ? ` / ${s.billing_type_display}` : ""}
                </p>
                <p className="text-[11px] text-gray-400 dark:text-gray-500 truncate mt-1">{s.business_name}</p>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Verified businesses */}
      {!loadingVerifiedBusinesses && verifiedBusinesses.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <BadgeCheck className="w-5 h-5 text-emerald-600" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t("home.verified_businesses_heading", "Biashara Zilizothibitishwa")}
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {verifiedBusinesses.map((b) => (
              <button
                key={b.id}
                onClick={() => navigate(`/store/${b.id}`)}
                className="text-left rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 hover:shadow-md transition flex items-start gap-3"
              >
                <div className="w-10 h-10 rounded-full bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center shrink-0">
                  <Store className="w-5 h-5 text-emerald-500" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1">
                    <p className="font-medium text-gray-900 dark:text-white truncate">{b.name}</p>
                    <BadgeCheck className="w-4 h-4 text-emerald-500 shrink-0" />
                  </div>
                  {b.category_name && (
                    <p className="text-xs text-gray-400 dark:text-gray-500">{b.category_name}</p>
                  )}
                  {b.description && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{b.description}</p>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Browse by category */}
      {!loadingCategories && categories.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <LayoutGrid className="w-5 h-5 text-purple-600" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t("home.categories_heading", "Vinjari kwa Aina")}
            </h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {categories.map((c) => (
              <button
                key={c.id}
                onClick={() => navigate(`/category/${c.slug}`)}
                className="text-center rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-3 hover:shadow-md hover:border-purple-300 dark:hover:border-purple-700 transition"
              >
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{c.name}</p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
