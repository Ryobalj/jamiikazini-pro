// src/app/realestate/pages/PropertyDetailPage.jsx

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams, useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import { ArrowLeft, MapPin, BedDouble, Bath, Ruler, Home, ShieldCheck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useCurrency } from "@/context/CurrencyContext";

export default function PropertyDetailPage() {
  const { id } = useParams();
  const { t } = useTranslation("realestate");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();

  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeImage, setActiveImage] = useState(0);
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api
      .get(`/realestate/properties/${id}/`)
      .then((res) => setListing(res.data))
      .catch(() => setListing(null))
      .finally(() => setLoading(false));
  }, [id]);

  const handleInquire = async () => {
    setSubmitting(true);
    try {
      await api.post("/realestate/inquiries/", { property: id, message: message.trim() });
      toast.success(t("inquiry_sent", "Ombi lako limetumwa kwa mmiliki."));
      navigate("/realestate/inquiries/mine");
    } catch (error) {
      const detail = error.response?.data?.detail || error.response?.data?.property?.[0];
      toast.error(typeof detail === "string" ? detail : t("inquiry_failed", "Imeshindwa kutuma ombi."));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
      </div>
    );
  }

  if (!listing) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-gray-500 dark:text-gray-400">{t("not_found", "Tangazo hili halipatikani.")}</p>
      </div>
    );
  }

  const images = listing.images || [];

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 space-y-4">
      <button
        onClick={() => navigate("/realestate")}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
      >
        <ArrowLeft className="w-4 h-4" /> {t("back", "Rudi")}
      </button>

      <div className="aspect-video bg-gray-100 dark:bg-gray-800 rounded-xl overflow-hidden">
        {images.length > 0 ? (
          <img src={images[activeImage]?.image} alt={listing.address_text} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300 dark:text-gray-600">
            <Home className="w-16 h-16" />
          </div>
        )}
      </div>
      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto">
          {images.map((img, idx) => (
            <button
              key={img.id}
              onClick={() => setActiveImage(idx)}
              className={`shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 ${
                idx === activeImage ? "border-purple-600" : "border-transparent"
              }`}
            >
              <img src={img.image} alt="" className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      )}

      <Card>
        <CardContent className="p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">
              {listing.listing_type === "RENT" ? t("listing_type_rent", "Kukodisha") : t("listing_type_sale", "Kuuza")}
            </span>
            {listing.owner_verified && (
              <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                <ShieldCheck className="w-4 h-4" /> {t("verified_owner", "Mmiliki Amethibitishwa")}
              </span>
            )}
          </div>

          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {formatCurrency(listing.price)}
            {listing.listing_type === "RENT" && (
              <span className="text-sm font-normal text-gray-400">/{t("per_month", "mwezi")}</span>
            )}
          </h1>

          {listing.address_text && (
            <p className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
              <MapPin className="w-4 h-4" /> {listing.address_text}
            </p>
          )}

          <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-300">
            {listing.bedrooms != null && (
              <span className="flex items-center gap-1"><BedDouble className="w-4 h-4" /> {listing.bedrooms} {t("bedrooms", "vyumba")}</span>
            )}
            {listing.bathrooms != null && (
              <span className="flex items-center gap-1"><Bath className="w-4 h-4" /> {listing.bathrooms} {t("bathrooms", "bafu")}</span>
            )}
            {listing.size_sqm && (
              <span className="flex items-center gap-1"><Ruler className="w-4 h-4" /> {listing.size_sqm} m²</span>
            )}
          </div>

          {listing.description && (
            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line">{listing.description}</p>
          )}

          {listing.title_deed_number && (
            <p className="text-xs text-gray-400 dark:text-gray-500">
              {t("title_deed_label", "Namba ya Hati")}: {listing.title_deed_number} - {t("title_deed_disclaimer", "imetolewa na muuzaji, haijathibitishwa na ardhi.go.tz")}
            </p>
          )}

          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t("listed_by", "Imetangazwa na")}: {listing.owner_name}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-5 space-y-3">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            {t("message_label", "Ujumbe kwa Mmiliki (hiari)")}
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={3}
            placeholder={t("message_placeholder", "Nataka kuona nyumba hii...")}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
          <Button onClick={handleInquire} disabled={submitting} className="w-full">
            {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
            {t("send_inquiry", "Tuma Nia Yangu")}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
