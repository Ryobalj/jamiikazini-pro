// src/app/businesses/components/products/DeleteConfirmModal.jsx

import React from "react";
import { useTranslation } from "react-i18next";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function DeleteConfirmModal({ productName, onClose, onConfirm }) {
  const { t } = useTranslation("businesses");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <Card className="max-w-md w-full">
        <CardContent className="p-6 text-center">
          <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {t("products.delete_confirm_title")}
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">
            {t("products.delete_confirm_desc", { name: productName })}
          </p>
          <div className="flex gap-3">
            <Button variant="outline" onClick={onClose} className="flex-1">
              {t("cancel")}
            </Button>
            <Button variant="destructive" onClick={onConfirm} className="flex-1">
              {t("products.delete")}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}