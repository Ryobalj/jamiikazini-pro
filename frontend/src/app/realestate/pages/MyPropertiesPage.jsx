// src/app/realestate/pages/MyPropertiesPage.jsx

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import { ArrowLeft, Home, Plus, Upload, Loader2, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useCurrency } from "@/context/CurrencyContext";
import { useCurrencies } from "@/hooks/useCurrencies";

const STATUS_STYLES = {
  AVAILABLE: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  RESERVED: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  RENTED: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
  SOLD: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
};

const INQUIRY_STATUS_STYLES = {
  PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  RESERVED: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  COMPLETED: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  CANCELLED: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
  REJECTED: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};

export default function MyPropertiesPage() {
  const { t } = useTranslation("realestate");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();
  const { currencies } = useCurrencies();

  const [business, setBusiness] = useState(null);
  const [loadingBusiness, setLoadingBusiness] = useState(true);
  const [listings, setListings] = useState([]);
  const [inquiries, setInquiries] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [actingId, setActingId] = useState(null);

  const [form, setForm] = useState({
    listing_type: "RENT", property_type: "HOUSE", address_text: "", price: "",
    deposit_amount: "", currency: "", lease_duration_months: "", bedrooms: "",
    bathrooms: "", size_sqm: "", description: "", title_deed_number: "",
  });
  const [location, setLocation] = useState(null);

  useEffect(() => {
    api
      .get("/businesses/")
      .then((res) => {
        const list = Array.isArray(res.data) ? res.data : res.data?.results || [];
        setBusiness(list[0] || null);
      })
      .catch(() => setBusiness(null))
      .finally(() => setLoadingBusiness(false));

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => setLocation(null)
      );
    }
  }, []);

  const fetchData = () => {
    setLoadingData(true);
    Promise.all([
      api.get("/realestate/properties/mine/").then((r) => r.data).catch(() => []),
      api.get("/realestate/inquiries/incoming/").then((r) => r.data).catch(() => []),
    ]).then(([l, i]) => {
      setListings(l);
      setInquiries(i);
    }).finally(() => setLoadingData(false));
  };

  useEffect(() => {
    if (business) fetchData();
  }, [business]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!location) {
      toast.error(t("location_required", "Tunahitaji eneo lako kutangaza mali hii."));
      return;
    }
    if (!form.price) {
      toast.error(t("price_required", "Weka bei."));
      return;
    }
    setCreating(true);
    try {
      await api.post("/realestate/properties/", {
        business: business.id,
        listing_type: form.listing_type,
        property_type: form.property_type,
        lat: location.lat, lng: location.lng,
        address_text: form.address_text,
        price: form.price,
        deposit_amount: form.listing_type === "RENT" ? (form.deposit_amount || undefined) : undefined,
        currency: form.currency || undefined,
        lease_duration_months: form.lease_duration_months || undefined,
        bedrooms: form.bedrooms || undefined,
        bathrooms: form.bathrooms || undefined,
        size_sqm: form.size_sqm || undefined,
        description: form.description,
        title_deed_number: form.title_deed_number,
      });
      toast.success(t("listing_created", "Tangazo limeundwa."));
      setShowForm(false);
      setForm({
        listing_type: "RENT", property_type: "HOUSE", address_text: "", price: "",
        deposit_amount: "", currency: "", lease_duration_months: "", bedrooms: "",
        bathrooms: "", size_sqm: "", description: "", title_deed_number: "",
      });
      fetchData();
    } catch (error) {
      toast.error(t("listing_create_failed", "Imeshindwa kuunda tangazo."));
    } finally {
      setCreating(false);
    }
  };

  const runInquiryAction = async (id, action, successMsg) => {
    setActingId(id);
    try {
      await api.post(`/realestate/inquiries/${id}/${action}/`);
      toast.success(successMsg);
      fetchData();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("action_failed", "Imeshindwa. Jaribu tena."));
    } finally {
      setActingId(null);
    }
  };

  if (loadingBusiness) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
      </div>
    );
  }

  if (!business) {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center space-y-3">
        <ShieldAlert className="w-10 h-10 text-yellow-500 mx-auto" />
        <p className="text-gray-600 dark:text-gray-300">
          {t("no_business", "Lazima ujisajili kama biashara kwanza kabla ya kutangaza mali isiyohamishika.")}
        </p>
        <Button onClick={() => navigate("/businesses/register")}>{t("register_business", "Sajili Biashara")}</Button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 space-y-5">
      <button
        onClick={() => navigate("/realestate")}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
      >
        <ArrowLeft className="w-4 h-4" /> {t("back", "Rudi")}
      </button>

      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("my_listings_title", "Matangazo Yangu")}
        </h1>
        <Button size="sm" onClick={() => setShowForm((v) => !v)}>
          <Plus className="w-4 h-4 mr-1" /> {t("new_listing", "Tangazo Jipya")}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader title={t("new_listing", "Tangazo Jipya")} icon={<Home className="w-5 h-5" />} divider />
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <select
                  value={form.listing_type}
                  onChange={(e) => setForm((f) => ({ ...f, listing_type: e.target.value }))}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="RENT">{t("listing_type_rent", "Kukodisha")}</option>
                  <option value="SALE">{t("listing_type_sale", "Kuuza")}</option>
                </select>
                <select
                  value={form.property_type}
                  onChange={(e) => setForm((f) => ({ ...f, property_type: e.target.value }))}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="LAND">{t("property_type_land", "Kiwanja")}</option>
                  <option value="HOUSE">{t("property_type_house", "Nyumba")}</option>
                  <option value="APARTMENT">{t("property_type_apartment", "Ghorofa")}</option>
                  <option value="COMMERCIAL">{t("property_type_commercial", "Biashara")}</option>
                </select>
              </div>

              <input
                type="text" value={form.address_text}
                onChange={(e) => setForm((f) => ({ ...f, address_text: e.target.value }))}
                placeholder={t("address_placeholder", "Anwani (mf. Mikocheni, Dar es Salaam)")}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />

              <div className="grid grid-cols-3 gap-3">
                <input
                  type="number" min="0" step="0.01" value={form.price}
                  onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))}
                  placeholder={t("price_label", "Bei")}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                {form.listing_type === "RENT" && (
                  <input
                    type="number" min="0" step="0.01" value={form.deposit_amount}
                    onChange={(e) => setForm((f) => ({ ...f, deposit_amount: e.target.value }))}
                    placeholder={t("deposit_label", "Amana (hiari)")}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                )}
                <select
                  value={form.currency}
                  onChange={(e) => setForm((f) => ({ ...f, currency: e.target.value }))}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">TZS</option>
                  {currencies.map((c) => (
                    <option key={c.id} value={c.id}>{c.code}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <input
                  type="number" min="0" value={form.bedrooms}
                  onChange={(e) => setForm((f) => ({ ...f, bedrooms: e.target.value }))}
                  placeholder={t("bedrooms", "Vyumba")}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                <input
                  type="number" min="0" value={form.bathrooms}
                  onChange={(e) => setForm((f) => ({ ...f, bathrooms: e.target.value }))}
                  placeholder={t("bathrooms", "Bafu")}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                <input
                  type="number" min="0" step="0.01" value={form.size_sqm}
                  onChange={(e) => setForm((f) => ({ ...f, size_sqm: e.target.value }))}
                  placeholder={t("size_sqm_label", "Ukubwa (m²)")}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>

              <input
                type="text" value={form.title_deed_number}
                onChange={(e) => setForm((f) => ({ ...f, title_deed_number: e.target.value }))}
                placeholder={t("title_deed_placeholder", "Namba ya Hati (hiari)")}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />

              <textarea
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                rows={3}
                placeholder={t("description_placeholder", "Maelezo ya mali...")}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />

              {!location && (
                <p className="text-xs text-yellow-600 dark:text-yellow-400">
                  {t("location_pending", "Tunasubiri ruhusa ya eneo lako...")}
                </p>
              )}

              <Button type="submit" disabled={creating} className="w-full">
                {creating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Upload className="w-4 h-4 mr-2" />}
                {t("submit_listing", "Chapisha Tangazo")}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {loadingData ? (
        <div className="flex justify-center py-10">
          <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
        </div>
      ) : (
        <>
          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase">
              {t("listings_heading", "Matangazo")} ({listings.length})
            </h2>
            {listings.length === 0 ? (
              <p className="text-sm text-gray-400">{t("no_listings_yet", "Bado hujatangaza mali yoyote.")}</p>
            ) : (
              listings.map((l) => (
                <Card key={l.id}>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{l.address_text || l.property_type}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{formatCurrency(l.price)}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_STYLES[l.status]}`}>
                      {t(`property_status_${l.status?.toLowerCase()}`, l.status)}
                    </span>
                  </CardContent>
                </Card>
              ))
            )}
          </div>

          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase">
              {t("incoming_inquiries_heading", "Nia za Wanunuzi")} ({inquiries.length})
            </h2>
            {inquiries.length === 0 ? (
              <p className="text-sm text-gray-400">{t("no_incoming_inquiries", "Hakuna nia kwa sasa.")}</p>
            ) : (
              inquiries.map((inq) => (
                <Card key={inq.id}>
                  <CardContent className="p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-gray-900 dark:text-white">{inq.buyer_name}</p>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${INQUIRY_STATUS_STYLES[inq.status]}`}>
                        {t(`status_${inq.status?.toLowerCase()}`, inq.status)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{inq.property_address}</p>
                    {inq.message && <p className="text-xs text-gray-500 dark:text-gray-400 italic">"{inq.message}"</p>}

                    {inq.status === "RESERVED" && (
                      <div className="flex gap-2 pt-1">
                        <Button
                          size="sm"
                          disabled={actingId === inq.id || !!inq.owner_confirmed_at}
                          onClick={() => runInquiryAction(inq.id, "confirm-handover", t("confirmed_success", "Umethibitisha handover."))}
                        >
                          {inq.owner_confirmed_at
                            ? t("already_confirmed_owner", "Umeshathibitisha - Inasubiri Mnunuzi")
                            : t("confirm_handover_owner", "Thibitisha Umekabidhi")}
                        </Button>
                        <Button size="sm" variant="secondary" disabled={actingId === inq.id} onClick={() => runInquiryAction(inq.id, "cancel", t("cancelled_success", "Nia imeghairiwa."))}>
                          {t("cancel", "Ghairi")}
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
