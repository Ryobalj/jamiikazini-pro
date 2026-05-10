// src/app/kiini/pages/InstitutionProfile.jsx

import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "@/lib/axios";
import {
  Building2,
  Globe,
  Mail,
  Phone,
  MapPin,
  Users,
  Settings,
  Edit3,
  Loader2,
  Store,
  Plus,
  ChevronRight,
  Calendar,
  Shield,
  Award,
  ArrowLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";

export default function InstitutionProfile() {
  const { id } = useParams();
  const { t } = useTranslation("kiini");
  const navigate = useNavigate();
  
  // HAKIKISHA HIZI STATE ZOTE ZIPO
  const [loading, setLoading] = useState(true);
  const [institution, setInstitution] = useState(null);
  const [businesses, setBusinesses] = useState([]);

  useEffect(() => {
    if (id) {
      fetchInstitution();
      fetchBusinesses();
    }
  }, [id]);

  const fetchInstitution = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/kiini/institutions/${id}/`);
      setInstitution(res.data);
    } catch (error) {
      console.error("Failed to fetch institution:", error);
      toast.error(t("institution.errors.failed_to_load"));
    } finally {
      setLoading(false);
    }
  };

  const fetchBusinesses = async () => {
    try {
      const res = await api.get(`/businesses/`, {
        params: { institution: id }
      });
      const businessList = Array.isArray(res.data) 
        ? res.data 
        : res.data.results || [];
      
      const filtered = businessList.filter(b => b.institution === id);
      setBusinesses(filtered);
    } catch (error) {
      console.error("Failed to fetch businesses:", error);
      try {
        const res = await api.get(`/kiini/institutions/${id}/businesses/`);
        setBusinesses(Array.isArray(res.data) ? res.data : res.data.results || []);
      } catch (err) {
        console.error("Alternative endpoint also failed:", err);
        setBusinesses([]);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!institution) {
    return (
      <div className="text-center py-12">
        <Building2 className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300">
          {t("institution.not_found")}
        </h2>
        <Button className="mt-4" onClick={() => navigate("/institutions/create")}>
          <Plus className="w-4 h-4 mr-2" />{t("institution.create")}
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Back Button */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
        <button
          onClick={() => navigate("/accounts/profile")}
          className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{t("institution.back_to_profile")}</span>
        </button>
      </div>

      {/* Institution Header */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 dark:from-green-900 dark:to-emerald-900 text-white mt-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
            <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-xl bg-white/20 flex items-center justify-center text-3xl font-bold">
              {institution.name?.charAt(0)?.toUpperCase() || "T"}
            </div>
            
            <div className="flex-1">
              <h1 className="text-2xl sm:text-3xl font-bold">{institution.name}</h1>
              <div className="flex flex-wrap gap-x-6 gap-y-2 mt-3 text-white/80 text-sm">
                {institution.domain && (
                  <span className="flex items-center gap-1">
                    <Globe className="w-4 h-4" />{institution.domain}
                  </span>
                )}
                {institution.email && (
                  <span className="flex items-center gap-1">
                    <Mail className="w-4 h-4" />{institution.email}
                  </span>
                )}
                {institution.phone && (
                  <span className="flex items-center gap-1">
                    <Phone className="w-4 h-4" />{institution.phone}
                  </span>
                )}
                {institution.address && (
                  <span className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />{institution.address}
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button 
                variant="secondary" 
                size="sm" 
                onClick={() => navigate(`/kiini/institutions/${id}/settings`)} 
                className="bg-white/20 hover:bg-white/30 text-white border-0"
              >
                <Settings className="w-4 h-4 mr-2" />{t("institution.settings")}
              </Button>
              <Button 
                variant="secondary" 
                size="sm" 
                onClick={() => navigate(`/kiini/institutions/${id}/edit`)} 
                className="bg-white/20 hover:bg-white/30 text-white border-0"
              >
                <Edit3 className="w-4 h-4 mr-2" />{t("institution.edit")}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 pb-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Stats & Info */}
          <div className="space-y-6">
            <Card>
              <CardHeader 
                title={t("institution.info.title")}
                icon={<Building2 className="w-5 h-5" />} 
                divider 
              />
              <CardContent>
                <div className="space-y-4">
                  <InfoRow 
                    icon={Calendar} 
                    label={t("institution.info.established")} 
                    value={institution.created_at ? new Date(institution.created_at).toLocaleDateString() : "-"} 
                  />
                  <InfoRow 
                    icon={Award} 
                    label={t("institution.info.tier")} 
                    value={institution.tier_name || institution.tier_display || "-"} 
                  />
                  <InfoRow 
                    icon={Shield} 
                    label={t("institution.info.type")} 
                    value={institution.type_name || institution.type_display || "-"} 
                  />
                  <InfoRow 
                    icon={Store} 
                    label={t("institution.info.businesses")} 
                    value={`${businesses.length} ${t("institution.info.businesses").toLowerCase()}`} 
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader 
                title={t("institution.members.title")}
                icon={<Users className="w-5 h-5" />} 
                divider 
              />
              <CardContent>
                <div className="text-center py-4">
                  <Users className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-500 dark:text-gray-400">{t("institution.members.none")}</p>
                  <Button variant="outline" size="sm" className="mt-3">
                    <Plus className="w-4 h-4 mr-2" />{t("institution.members.invite")}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Businesses */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader 
                title={t("institution.businesses_section.title")}
                icon={<Store className="w-5 h-5" />}
                divider
                actions={
                  <Button size="sm" onClick={() => navigate("/businesses/register/")}>
                    <Plus className="w-4 h-4 mr-1" />{t("institution.businesses_section.create")}
                  </Button>
                }
              />
              <CardContent>
                {businesses.length > 0 ? (
                  <div className="space-y-3">
                    {businesses.map((biz) => (
                      <div 
                        key={biz.id} 
                        className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors" 
                        onClick={() => navigate(`/businesses/dashboard/${biz.id}/overview`)}
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-900 flex items-center justify-center">
                            <Store className="w-5 h-5 text-green-600 dark:text-green-400" />
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-gray-100">{biz.name}</p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              {biz.category_name || biz.description?.substring(0, 50) || "-"}
                            </p>
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-gray-400" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Store className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-500 dark:text-gray-400 mb-4">
                      {t("institution.businesses_section.none")}
                    </p>
                    <Button onClick={() => navigate("/businesses/register/")}>
                      <Plus className="w-4 h-4 mr-2" />{t("institution.businesses_section.create_first")}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start gap-3">
      <Icon className="w-5 h-5 text-gray-400 dark:text-gray-500 mt-0.5 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
        <p className="font-medium text-gray-900 dark:text-gray-100">{value || "-"}</p>
      </div>
    </div>
  );
}