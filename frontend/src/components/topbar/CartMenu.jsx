// src/components/topbar/CartMenu.jsx

import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

export default function CartMenu({ cartItems = [], onClose }) {
  const { t } = useTranslation();

  return (
    <div className="absolute right-0 mt-2 w-80 rounded-lg shadow-lg bg-white dark:bg-gray-800 ring-1 ring-gray-200 dark:ring-gray-700 p-3 space-y-3 animate-fade-in z-50">
      <h3 className="text-lg font-semibold">{t("cart.title")}</h3>

      {cartItems.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {t("cart.empty")}
        </p>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {cartItems.map((item, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <div>
                <div className="font-medium">{item.name}</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {item.quantity} × {item.price} TZS
                </div>
              </div>
              <Link
                to="/cart"
                onClick={onClose}
                className="text-blue-500 hover:underline text-sm"
              >
                {t("cart.edit")}
              </Link>
            </div>
          ))}
        </div>
      )}

      {cartItems.length > 0 && (
        <div className="text-right">
          <Link
            to="/checkout"
            onClick={onClose}
            className="inline-block mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            {t("cart.checkout")}
          </Link>
        </div>
      )}
    </div>
  );
}