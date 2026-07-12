// src/app/jamiiwallet/pages/AddCardPage.jsx

import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, CreditCard, ShieldAlert } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

// NB: Bado hatujaunganisha tokenization halisi ya kadi (Stripe Elements /
// Flutterwave inline). Kwa makusudi HATUONESHI fomu ya kuandika namba ya
// kadi hapa - kuandika namba ya kadi moja kwa moja kwenye seva zetu (badala
// ya token kutoka gateway) ni ukiukwaji wa PCI-DSS. Tazama Task #26.
export default function AddCardPage() {
  const { t } = useTranslation("jamiiwallet");
  const navigate = useNavigate();

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <button
        onClick={() => navigate("/jamiiwallet")}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        {t("back") || "Rudi"}
      </button>

      <Card>
        <CardHeader title={t("add_card.title") || "Ongeza Kadi"} icon={<CreditCard className="w-5 h-5" />} divider />
        <CardContent className="text-center py-8">
          <ShieldAlert className="w-12 h-12 mx-auto text-yellow-500 mb-4" />
          <p className="text-gray-700 dark:text-gray-300 font-medium mb-2">
            {t("add_card.unavailable_title") || "Malipo ya kadi bado hayajawezeshwa"}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto">
            {t("add_card.unavailable_body") ||
              "Kwa usalama wako, tunasubiri kuunganisha huduma ya malipo ya kadi (Stripe/Flutterwave) kikamilifu kabla ya kufungua kipengele hiki. Kwa sasa, tumia PawaPay (Tigo/Yas, Airtel, Halotel) kwa kuweka na kutoa pesa."}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
