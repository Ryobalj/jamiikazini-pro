// src/app/accounts/pages/EditProfilePage.jsx

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import { useAppContext } from "@/context/AppContext";
import { User, Mail, Phone, Shield, Save, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import InputField from "@/components/InputField";
import { toast } from "react-toastify";

export default function EditProfilePage() {
  const { t } = useTranslation("accounts");
  const navigate = useNavigate();
  const { user, setUser } = useAppContext();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    full_name: "",
    phone_number: "",
    national_id: "",
  });

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || "",
        phone_number: user.phone_number || "",
        national_id: user.national_id || "",
      });
    }
  }, [user]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const res = await api.patch("/auth/me/", formData);
      setUser({ ...user, ...res.data });
      toast.success(t("profile_updated"));
      navigate("/accounts/profile");
    } catch (error) {
      console.error("Failed to update profile:", error);
      toast.error(t("errors.failed_to_update"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <Card>
          <CardHeader title={t("edit_profile.title")} icon={<User className="w-5 h-5" />} divider />
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <InputField
                label={t("full_name")}
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                icon={<User className="w-4 h-4" />}
              />
              
              <InputField
                label={t("phone")}
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                icon={<Phone className="w-4 h-4" />}
                placeholder="+255XXXXXXXXX"
              />
              
              <InputField
                label={t("national_id")}
                name="national_id"
                value={formData.national_id}
                onChange={handleChange}
                icon={<Shield className="w-4 h-4" />}
              />
              
              <div className="flex gap-3 pt-4">
                <Button type="submit" disabled={loading}>
                  {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                  {t("save")}
                </Button>
                <Button variant="outline" onClick={() => navigate("/accounts/profile")}>
                  {t("cancel")}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}