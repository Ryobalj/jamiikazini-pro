// src/app/accounts/pages/SettingsPage.jsx

import React from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Settings, Globe, Bell, Lock } from "lucide-react";

export default function SettingsPage() {
  const { t } = useTranslation("accounts");

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">
          <Settings className="inline w-6 h-6 mr-2" />
          {t("settings.title")}
        </h1>
        
        <div className="space-y-6">
          <Card>
            <CardHeader title="Language Preferences" icon={<Globe className="w-5 h-5" />} divider />
            <CardContent>
              <p className="text-gray-500">Language settings coming soon...</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader title="Notification Settings" icon={<Bell className="w-5 h-5" />} divider />
            <CardContent>
              <p className="text-gray-500">Notification settings coming soon...</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader title="Privacy & Security" icon={<Lock className="w-5 h-5" />} divider />
            <CardContent>
              <p className="text-gray-500">Privacy settings coming soon...</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}