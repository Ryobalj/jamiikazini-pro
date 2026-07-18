// src/app/realestate/pages/PropertyListPage.jsx

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, Link } from "react-router-dom";
import api from "@/lib/axios";
import { Home, MapPin, BedDouble, Bath, Ruler, Loader2, ShieldCheck } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { useCurrency } from "@/context/CurrencyContext";

export default function PropertyListPage() {
  const { t } = useTranslation("realestate");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();

  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [listingType, setListingType] = useState("");
  const [propertyType, setPropertyType] = useState("");

  const fetchListings = () => {
    setLoading(true);
    const params = {};
    if (listingType) params.listing_type = listingType;
    if (propertyType) params.property_type = propertyType;
    api
      .get("/realestate/properties/", { params })
      .then((res) => setListings(Array.isArray(res.data) ? res.data : res.data?.results || []))
      .catch(() => setListings([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchListings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listingType, propertyType]);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Home className="w-6 h-6 text-purple-600" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t("title", "Mali Isiyohamishika")}
          </h1>
        </div>
        <div className="flex gap-2">
          <Link
            to="/realestate/mine"
            className="text-sm px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
          >
            {t("my_listings_link", "Matangazo Yangu")}
          </Link>
          <Link
            to="/realestate/inquiries/mine"
            className="text-sm px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
          >
            {t("my_inquiries_link", "Maombi Yangu")}
          </Link>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <select
          value={listingType}
          onChange={(e) => setListingType(e.target.value)}
          className="px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
        >
          <option value="">{t("filter_all_types", "Kodi na Uuzaji")}</option>
          <option value="RENT">{t("listing_type_rent", "Kukodisha")}</option>
          <option value="SALE">{t("listing_type_sale", "Kuuza")}</option>
        </select>
        <select
          value={propertyType}
          onChange={(e) => setPropertyType(e.target.value)}
          className="px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
        >
          <option value="">{t("filter_all_property_types", "Aina Zote")}</option>
          <option value="LAND">{t("property_type_land", "Kiwanja")}</option>
          <option value="HOUSE">{t("property_type_house", "Nyumba")}</option>
          <option value="APARTMENT">{t("property_type_apartment", "Ghorofa")}</option>
          <option value="COMMERCIAL">{t("property_type_commercial", "Biashara")}</option>
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
        </div>
      ) : listings.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-16">
          {t("no_listings", "Hakuna matangazo kwa sasa.")}
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {listings.map((p) => (
            <Card
              key={p.id}
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => navigate(`/realestate/${p.id}`)}
            >
              <div className="aspect-video bg-gray-100 dark:bg-gray-800 rounded-t-xl overflow-hidden">
                {p.cover_image ? (
                  <img src={p.cover_image} alt={p.address_text} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-300 dark:text-gray-600">
                    <Home className="w-10 h-10" />
                  </div>
                )}
              </div>
              <CardContent className="p-4 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">
                    {p.listing_type === "RENT" ? t("listing_type_rent", "Kukodisha") : t("listing_type_sale", "Kuuza")}
                  </span>
                  {p.owner_verified && <ShieldCheck className="w-4 h-4 text-green-500" />}
                </div>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {formatCurrency(p.price)}{p.listing_type === "RENT" && <span className="text-xs font-normal text-gray-400">/{t("per_month", "mwezi")}</span>}
                </p>
                {p.address_text && (
                  <p className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
                    <MapPin className="w-3.5 h-3.5" /> {p.address_text}
                  </p>
                )}
                <div className="flex items-center gap-3 text-xs text-gray-400 pt-1">
                  {p.bedrooms != null && (
                    <span className="flex items-center gap-1"><BedDouble className="w-3.5 h-3.5" /> {p.bedrooms}</span>
                  )}
                  {p.bathrooms != null && (
                    <span className="flex items-center gap-1"><Bath className="w-3.5 h-3.5" /> {p.bathrooms}</span>
                  )}
                  {p.size_sqm && (
                    <span className="flex items-center gap-1"><Ruler className="w-3.5 h-3.5" /> {p.size_sqm} m²</span>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
