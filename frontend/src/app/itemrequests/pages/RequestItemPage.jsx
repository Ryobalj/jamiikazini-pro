// src/app/itemrequests/pages/RequestItemPage.jsx

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Search, Loader2, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";

export default function RequestItemPage() {
  const { t } = useTranslation("itemrequests");
  const navigate = useNavigate();

  const [q, setQ] = useState("");
  const [categories, setCategories] = useState([]);
  const [categoryId, setCategoryId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [radiusKm, setRadiusKm] = useState(5);
  const [location, setLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api
      .get("/product-categories/?ordering=name")
      .then((res) => setCategories(Array.isArray(res.data) ? res.data : res.data?.results || []))
      .catch(() => setCategories([]));
  }, []);

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError(t("location_unavailable", "Kifaa chako hakiungi mkono utambuzi wa eneo."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({ lat: position.coords.latitude, lng: position.coords.longitude });
        setLocationError(null);
      },
      () => {
        setLocationError(t("location_permission_denied", "Ruhusa ya eneo imekataliwa. Tafadhali washa huduma za eneo."));
      }
    );
  }, [t]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!q.trim()) return;
    if (!location) {
      toast.error(t("location_required", "Tunahitaji eneo lako ili kutuma ombi kwa maduka ya karibu."));
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post("/item-requests/", {
        q: q.trim(),
        category: categoryId || undefined,
        quantity,
        lat: location.lat,
        lng: location.lng,
        radius_km: radiusKm,
      });
      navigate(`/request-item/${res.data.id}/waiting`);
    } catch (error) {
      const detail = error.response?.data?.q || error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("request_failed", "Imeshindwa kutuma ombi. Jaribu tena."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto p-4 sm:p-6 space-y-4">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t("title", "Tafuta Bidhaa")}
      </h1>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        {t(
          "description",
          "Andika bidhaa unayoitafuta - ombi lako litatumwa kwa maduka ya karibu yenye bidhaa hiyo, na duka la kwanza litakalokubali litakuhudumia."
        )}
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Card>
          <CardContent className="p-4 space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("query_label", "Ninatafuta")}
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder={t("query_placeholder", "Mfano: sukari kilo 2")}
                  className="w-full pl-9 p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("category_label", "Aina ya Bidhaa (hiari)")}
              </label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
              >
                <option value="">{t("category_any", "Aina Yoyote")}</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t("quantity_label", "Idadi")}
                </label>
                <input
                  type="number"
                  min="1"
                  value={quantity}
                  onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
                  className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t("radius_label", "Umbali wa Kutafuta (km)")}
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={radiusKm}
                  onChange={(e) => setRadiusKm(Math.max(1, Number(e.target.value)))}
                  className="w-full p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
              <MapPin className="w-3.5 h-3.5" />
              {location ? (
                <span>{t("location_ready", "Eneo lako limepatikana.")}</span>
              ) : locationError ? (
                <span className="text-red-500">{locationError}</span>
              ) : (
                <span>{t("location_locating", "Inatafuta eneo lako...")}</span>
              )}
            </div>
          </CardContent>
        </Card>

        <Button type="submit" disabled={submitting || !q.trim()} className="w-full" size="lg">
          {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
          {t("submit", "Tuma Ombi kwa Maduka ya Karibu")}
        </Button>
      </form>
    </div>
  );
}
