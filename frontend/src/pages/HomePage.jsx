// src/pages/HomePage.jsx

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAppContext } from "@/context/AppContext";
import { useTranslation } from "react-i18next";
import { TrendingUp, Megaphone, Store, Loader2 } from "lucide-react";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";

export default function HomePage() {
  const { user } = useAppContext();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { formatCurrency } = useCurrency();

  const [trending, setTrending] = useState([]);
  const [loadingTrending, setLoadingTrending] = useState(true);
  const [featured, setFeatured] = useState([]);
  const [loadingFeatured, setLoadingFeatured] = useState(true);

  useEffect(() => {
    api
      .get("/products/trending/")
      .then((res) => setTrending(res.data))
      .catch(() => setTrending([]))
      .finally(() => setLoadingTrending(false));

    api
      .get("/featured-listings/active/")
      .then((res) => setFeatured(res.data))
      .catch(() => setFeatured([]))
      .finally(() => setLoadingFeatured(false));
  }, []);

  return (
    <div className="font-sans px-4 py-8 sm:px-8 space-y-10">
      {!user && (
        <button
          onClick={() => navigate("/security/login/")}
          className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow transition"
        >
          {t("home.login_cta")}
        </button>
      )}

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
    </div>
  );
}
