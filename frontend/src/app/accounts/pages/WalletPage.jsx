// src/app/accounts/pages/WalletPage.jsx

import React from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Wallet, CreditCard, History } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function WalletPage() {
  const { t } = useTranslation("accounts");

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">
          <Wallet className="inline w-6 h-6 mr-2" />
          {t("wallet.title")}
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-gray-500">Balance</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">TZS 0</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-gray-500">Pending</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">TZS 0</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-gray-500">Total Spent</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">TZS 0</p>
            </CardContent>
          </Card>
        </div>
        
        <Card>
          <CardHeader title="Recent Transactions" icon={<History className="w-5 h-5" />} divider />
          <CardContent>
            <p className="text-gray-500 text-center py-8">No transactions yet</p>
            <Button className="w-full">
              <CreditCard className="w-4 h-4 mr-2" />
              Add Money
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}