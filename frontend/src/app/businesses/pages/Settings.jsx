// src/app/businesses/pages/Settings.jsx

import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "@/lib/axios";
import { Loader2, Package, AlertTriangle, PlusCircle, Store, Globe, ShieldCheck, ShieldAlert, Percent, Copy, Wheat, Link2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";

import { useProducts } from "@/hooks/useProducts";

const LOW_STOCK_THRESHOLD = 5;

export default function Settings() {
  const { id: businessId } = useParams();
  const { t } = useTranslation("businesses");

  const { products, loading: loadingProducts, fetchProducts } = useProducts(businessId);
  const [business, setBusiness] = useState(null);
  const [loadingBusiness, setLoadingBusiness] = useState(true);
  const [restockingSlug, setRestockingSlug] = useState(null);
  const [restockAmounts, setRestockAmounts] = useState({});
  const [licenseNumber, setLicenseNumber] = useState("");
  const [countryCode, setCountryCode] = useState("tz");
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [commissionRate, setCommissionRate] = useState("0.00");
  const [savingCommission, setSavingCommission] = useState(false);
  const [referralCode, setReferralCode] = useState(null);
  const [dealsInImports, setDealsInImports] = useState(false);
  const [savingImports, setSavingImports] = useState(false);
  const [dealsInAgriculture, setDealsInAgriculture] = useState(false);
  const [savingAgriculture, setSavingAgriculture] = useState(false);
  const [domainInput, setDomainInput] = useState("");
  const [savingDomain, setSavingDomain] = useState(false);

  useEffect(() => {
    if (!businessId) return;
    api
      .get(`/businesses/${businessId}/`)
      .then((res) => {
        setBusiness(res.data);
        setCommissionRate(res.data?.broker_commission_rate ?? "0.00");
        setDealsInImports(Boolean(res.data?.deals_in_imports));
        setDealsInAgriculture(Boolean(res.data?.deals_in_agriculture));
        setDomainInput(res.data?.domain || "");
      })
      .catch(() => setBusiness(null))
      .finally(() => setLoadingBusiness(false));
  }, [businessId]);

  useEffect(() => {
    api
      .get("/kiini/referral-code/mine/")
      .then((res) => setReferralCode(res.data?.code || null))
      .catch(() => setReferralCode(null));
  }, []);

  const handleSaveCommission = async () => {
    setSavingCommission(true);
    try {
      const res = await api.patch(`/businesses/${businessId}/`, { broker_commission_rate: commissionRate });
      setBusiness((prev) => (prev ? { ...prev, broker_commission_rate: res.data.broker_commission_rate } : prev));
      toast.success(t("settings.commission_saved") || "Kiwango cha kamisheni kimehifadhiwa.");
    } catch (error) {
      toast.error(error.response?.data?.broker_commission_rate?.[0] || t("settings.errors.commission_save_failed") || "Imeshindwa kuhifadhi.");
    } finally {
      setSavingCommission(false);
    }
  };

  const handleToggleImports = async () => {
    const next = !dealsInImports;
    setSavingImports(true);
    try {
      const res = await api.patch(`/businesses/${businessId}/`, { deals_in_imports: next });
      setDealsInImports(Boolean(res.data.deals_in_imports));
      setBusiness((prev) => (prev ? { ...prev, deals_in_imports: res.data.deals_in_imports } : prev));
      toast.success(
        next
          ? t("settings.imports_enabled") || "Umewashwa kama muagizaji - utaona maombi ya uagizaji."
          : t("settings.imports_disabled") || "Umezimwa kama muagizaji."
      );
    } catch (error) {
      toast.error(t("settings.errors.imports_save_failed") || "Imeshindwa kuhifadhi.");
    } finally {
      setSavingImports(false);
    }
  };

  const handleToggleAgriculture = async () => {
    const next = !dealsInAgriculture;
    setSavingAgriculture(true);
    try {
      const res = await api.patch(`/businesses/${businessId}/`, { deals_in_agriculture: next });
      setDealsInAgriculture(Boolean(res.data.deals_in_agriculture));
      setBusiness((prev) => (prev ? { ...prev, deals_in_agriculture: res.data.deals_in_agriculture } : prev));
      toast.success(
        next
          ? t("settings.agriculture_enabled") || "Umewashwa kama muuzaji wa mazao - utaona mikataba ya mazao."
          : t("settings.agriculture_disabled") || "Umezimwa kama muuzaji wa mazao."
      );
    } catch (error) {
      toast.error(t("settings.errors.agriculture_save_failed") || "Imeshindwa kuhifadhi.");
    } finally {
      setSavingAgriculture(false);
    }
  };

  const handleSaveDomain = async () => {
    const value = domainInput.trim().toLowerCase();
    if (!value) {
      toast.error(t("settings.errors.domain_required") || "Weka jina la subdomain.");
      return;
    }
    setSavingDomain(true);
    try {
      const res = await api.patch(`/businesses/${businessId}/`, { domain: value });
      setBusiness((prev) => (prev ? { ...prev, domain: res.data.domain } : prev));
      setDomainInput(res.data.domain);
      toast.success(t("settings.domain_saved") || "Anwani ya duka imehifadhiwa.");
    } catch (error) {
      toast.error(error.response?.data?.domain?.[0] || t("settings.errors.domain_save_failed") || "Imeshindwa kuhifadhi.");
    } finally {
      setSavingDomain(false);
    }
  };

  const handleCopyStoreLink = () => {
    if (!business?.domain) return;
    const link = `https://${business.domain}.jamiikazini.com`;
    navigator.clipboard?.writeText(link);
    toast.success(t("settings.link_copied") || "Kiungo kimenakiliwa.");
  };

  const handleCopyReferralCode = () => {
    if (!referralCode) return;
    navigator.clipboard?.writeText(referralCode);
    toast.success(t("settings.referral_code_copied") || "Msimbo umenakiliwa.");
  };

  const lowStockProducts = products.filter((p) => p.quantity_in_stock <= LOW_STOCK_THRESHOLD);

  const handleRequestVerification = async () => {
    if (!licenseNumber.trim()) {
      toast.error(t("settings.errors.license_number_required") || "Weka namba ya leseni.");
      return;
    }
    setVerifying(true);
    setVerificationResult(null);
    try {
      const res = await api.post(`/gov/verify/business/${businessId}/license/`, {
        business_license_number: licenseNumber.trim(),
        country_code: countryCode,
      });
      setVerificationResult(res.data);
      if (res.data.status === "VERIFIED") {
        toast.success(t("settings.verification_success") || "Biashara imethibitishwa!");
        setBusiness((prev) => (prev ? { ...prev, is_verified: true } : prev));
      } else {
        toast.error(t("settings.verification_failed") || "Uthibitisho umeshindwa. Angalia namba ya leseni.");
      }
    } catch (error) {
      toast.error(error.response?.data?.business_license_number?.[0] || t("settings.errors.verification_request_failed") || "Ombi limeshindwa.");
    } finally {
      setVerifying(false);
    }
  };

  const handleRestock = async (slug) => {
    const amount = parseInt(restockAmounts[slug], 10);
    if (!amount || amount <= 0) {
      toast.error(t("settings.errors.invalid_quantity") || "Weka kiasi sahihi.");
      return;
    }
    setRestockingSlug(slug);
    try {
      await api.post(`/businesses/${businessId}/products/${slug}/restock/`, { quantity: amount });
      toast.success(t("settings.restocked") || "Stock imeongezwa.");
      setRestockAmounts((prev) => ({ ...prev, [slug]: "" }));
      fetchProducts();
    } catch (error) {
      toast.error(error.response?.data?.quantity?.[0] || t("settings.errors.restock_failed") || "Imeshindwa.");
    } finally {
      setRestockingSlug(null);
    }
  };

  return (
    <div className="p-4 space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
        {t("tabs.settings") || "Mipangilio"}
      </h1>

      <Card>
        <CardHeader title={t("settings.business_info") || "Taarifa za Biashara"} icon={<Store className="w-5 h-5" />} divider />
        <CardContent>
          {loadingBusiness ? (
            <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
          ) : business ? (
            <div className="space-y-1">
              <p className="font-medium text-gray-900 dark:text-white">{business.name}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {business.category_name || t("settings.no_category") || "Bila aina"}
                {business.is_verified && ` · ${t("settings.verified") || "Imethibitishwa"}`}
              </p>
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("settings.load_failed") || "Imeshindwa kupakia biashara."}
            </p>
          )}
        </CardContent>
      </Card>

      {business && (
        <Card>
          <CardHeader
            title={t("settings.share_store") || "Shiriki Duka Lako"}
            icon={<Link2 className="w-5 h-5 text-purple-600" />}
            divider
          />
          <CardContent className="space-y-3">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("settings.share_store_desc") ||
                "Duka lako lina anwani yake mwenyewe unayoweza kushiriki popote - jamiikazini.com/store/... si lazima."}
            </p>
            <div className="flex gap-2">
              <span className="flex items-center px-2 text-sm text-gray-400 border border-r-0 border-gray-200 dark:border-gray-700 rounded-l-lg bg-gray-50 dark:bg-gray-800">
                https://
              </span>
              <input
                type="text"
                value={domainInput}
                onChange={(e) => setDomainInput(e.target.value)}
                placeholder="jina-la-duka"
                className="flex-1 px-2 py-2 border-y border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white"
              />
              <span className="flex items-center px-2 text-sm text-gray-400 border border-l-0 border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                .jamiikazini.com
              </span>
              <Button onClick={handleSaveDomain} disabled={savingDomain} className="rounded-l-none">
                {savingDomain ? <Loader2 className="w-4 h-4 animate-spin" /> : (t("settings.save") || "Hifadhi")}
              </Button>
            </div>
            {business.domain && (
              <div className="flex items-center gap-2">
                <code className="flex-1 p-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm truncate">
                  https://{business.domain}.jamiikazini.com
                </code>
                <Button variant="secondary" onClick={handleCopyStoreLink}>
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {business && (
        <Card>
          <CardHeader
            title={t("settings.broker_commission") || "Kamisheni ya Dalali"}
            icon={<Percent className="w-5 h-5" />}
            divider
          />
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("settings.commission_rate_label") || "Asilimia ya Kamisheni (%)"}
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.01"
                  value={commissionRate}
                  onChange={(e) => setCommissionRate(e.target.value)}
                  className="flex-1 p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white text-sm"
                />
                <Button onClick={handleSaveCommission} disabled={savingCommission}>
                  {savingCommission ? <Loader2 className="w-4 h-4 animate-spin" /> : (t("settings.save") || "Hifadhi")}
                </Button>
              </div>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                {t("settings.commission_hint") || "0 = hakuna kamisheni. Dalali analipwa moja kwa moja kutoka kwenye mauzo yaliyolipwa kupitia JamiiWallet (PICKUP tu kwa sasa)."}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("settings.your_referral_code") || "Msimbo Wako wa Dalali"}
              </label>
              <div className="flex items-center gap-2">
                <code className="flex-1 p-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm">
                  {referralCode || "—"}
                </code>
                <Button variant="secondary" onClick={handleCopyReferralCode} disabled={!referralCode}>
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {business && (
        <Card>
          <CardHeader
            title={t("settings.import_dealer") || "Uagizaji wa Bidhaa (Imports)"}
            icon={<Globe className="w-5 h-5 text-blue-600" />}
            divider
          />
          <CardContent>
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t("settings.import_dealer_desc") ||
                  "Washa kama biashara yako inaweza kuagiza bidhaa kutoka nje ya nchi - utaona maombi ya uagizaji kutoka kwa wanunuzi."}
              </p>
              <Button
                variant={dealsInImports ? "primary" : "secondary"}
                onClick={handleToggleImports}
                disabled={savingImports}
              >
                {savingImports ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : dealsInImports ? (
                  t("settings.imports_on") || "Imewashwa"
                ) : (
                  t("settings.imports_off") || "Imezimwa"
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {business && (
        <Card>
          <CardHeader
            title={t("settings.agriculture_dealer") || "Uuzaji wa Mazao (Kilimo)"}
            icon={<Wheat className="w-5 h-5 text-green-600" />}
            divider
          />
          <CardContent>
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t("settings.agriculture_dealer_desc") ||
                  "Washa kama biashara yako inauza mazao kwa wingi - utaona mikataba ya awali ya mazao (harvest contracts) kutoka kwa wanunuzi."}
              </p>
              <Button
                variant={dealsInAgriculture ? "primary" : "secondary"}
                onClick={handleToggleAgriculture}
                disabled={savingAgriculture}
              >
                {savingAgriculture ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : dealsInAgriculture ? (
                  t("settings.agriculture_on") || "Imewashwa"
                ) : (
                  t("settings.agriculture_off") || "Imezimwa"
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {business && !business.is_verified && (
        <Card>
          <CardHeader
            title={t("settings.verify_business") || "Thibitisha Biashara Yako"}
            icon={<ShieldCheck className="w-5 h-5 text-green-600" />}
            divider
          />
          <CardContent>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
              {t("settings.verify_business_desc") ||
                "Weka namba ya leseni ya biashara ili tuthibitishe na mamlaka husika ya nchi yako."}
            </p>
            <div className="flex flex-col sm:flex-row gap-2">
              <select
                value={countryCode}
                onChange={(e) => setCountryCode(e.target.value)}
                className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
              >
                <option value="tz">Tanzania</option>
                <option value="ke">Kenya</option>
                <option value="ug">Uganda</option>
                <option value="rw">Rwanda</option>
              </select>
              <input
                type="text"
                value={licenseNumber}
                onChange={(e) => setLicenseNumber(e.target.value)}
                placeholder={t("settings.license_number_placeholder") || "Namba ya Leseni ya Biashara"}
                className="flex-1 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
              />
              <Button
                onClick={handleRequestVerification}
                disabled={verifying}
                className="bg-green-600 hover:bg-green-700 whitespace-nowrap"
              >
                {verifying ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  t("settings.verify_now") || "Thibitisha Sasa"
                )}
              </Button>
            </div>
            {verificationResult && verificationResult.status === "FAILED" && (
              <p className="text-sm text-red-500 flex items-center gap-1 mt-2">
                <ShieldAlert className="w-4 h-4" />
                {t("settings.verification_failed_detail") || "Tumeshindwa kuthibitisha namba hii ya leseni."}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent>
          <Link
            to={`/homepage/manage/business/${businessId}`}
            className="flex items-center gap-3 p-3 -m-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
          >
            <Globe className="w-5 h-5 text-purple-600" />
            <span className="text-gray-900 dark:text-white">{t("settings.homepage") || "Homepage ya Umma"}</span>
          </Link>
        </CardContent>
      </Card>

      <Card>
        <CardHeader
          title={t("settings.low_stock") || "Bidhaa Zenye Stock Kidogo"}
          icon={<AlertTriangle className="w-5 h-5 text-yellow-500" />}
          divider
        />
        <CardContent>
          {loadingProducts ? (
            <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
          ) : lowStockProducts.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
              <Package className="w-4 h-4" />
              {t("settings.no_low_stock") || "Bidhaa zote zina stock ya kutosha."}
            </p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {lowStockProducts.map((p) => (
                <div key={p.slug} className="flex items-center justify-between py-3 gap-3">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{p.name}</p>
                    <p className="text-sm text-red-500">
                      {t("settings.stock_remaining", { count: p.quantity_in_stock }) ||
                        `Zimebaki: ${p.quantity_in_stock}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min="1"
                      value={restockAmounts[p.slug] || ""}
                      onChange={(e) => setRestockAmounts((prev) => ({ ...prev, [p.slug]: e.target.value }))}
                      placeholder="+"
                      className="w-16 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                    />
                    <Button
                      size="sm"
                      className="bg-purple-600 hover:bg-purple-700"
                      disabled={restockingSlug === p.slug}
                      onClick={() => handleRestock(p.slug)}
                    >
                      {restockingSlug === p.slug ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <PlusCircle className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
