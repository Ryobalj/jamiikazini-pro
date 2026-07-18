// src/app/cart/pages/CartPage.jsx

import React from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Trash2, Plus, Minus, ShoppingBag, ArrowLeft, Store } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useCart } from "@/context/CartContext";
import { useCurrency } from "@/context/CurrencyContext";

// Mirrors businesses.models.product.WHOLE_UNIT_TYPES - units that can't be fractional.
const WHOLE_UNIT_TYPES = new Set(["pcs", "box", "pack", "dozen", "pair", "set", "session", "gunia", "debe", "fungu", "roli", "bale"]);

export default function CartPage() {
  const { t } = useTranslation("cart");
  const navigate = useNavigate();
  const { items, updateQuantity, removeItem, clearCart, totalPrice, itemsByBusiness } = useCart();
  const { formatCurrency } = useCurrency();

  if (items.length === 0) {
    return (
      <div className="max-w-2xl mx-auto p-6 text-center py-20">
        <ShoppingBag className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          {t("empty_title", "Kikapu chako kiko tupu")}
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mb-6">
          {t("empty_desc", "Tembelea duka la mfanyabiashara uongeze bidhaa kwenye kikapu.")}
        </p>
        <Button onClick={() => navigate("/nearby")}>
          {t("browse_businesses", "Tafuta Biashara")}
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t("title", "Kikapu Changu")}
        </h1>
      </div>

      {itemsByBusiness.length > 1 && (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {t("multi_seller_note", "Bidhaa zako zitatumwa kama oda tofauti kwa kila muuzaji.")}
        </p>
      )}

      {itemsByBusiness.map((group) => (
        <Card key={group.businessId} className="!p-0 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-900/40 border-b border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-1.5 text-sm font-medium text-gray-700 dark:text-gray-300">
              <Store className="w-3.5 h-3.5" /> {group.businessName}
            </div>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {formatCurrency(group.subtotal)}
            </span>
          </div>
          <CardContent className="divide-y divide-gray-100 dark:divide-gray-700 !p-0">
            {group.items.map((item) => (
              <div key={item.productId} className="flex items-center gap-3 p-4">
                {item.image ? (
                  <img src={item.image} alt={item.name} className="w-16 h-16 rounded-lg object-cover flex-shrink-0" />
                ) : (
                  <div className="w-16 h-16 rounded-lg bg-gray-100 dark:bg-gray-700 flex-shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 dark:text-white truncate">{item.name}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {formatCurrency(item.price)} / {item.unit || "pcs"}
                  </p>
                  {WHOLE_UNIT_TYPES.has(item.unit || "pcs") ? (
                    <div className="flex items-center gap-2 mt-2">
                      <button
                        onClick={() => updateQuantity(item.productId, item.quantity - 1)}
                        className="p-1 rounded-full border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        <Minus className="w-3.5 h-3.5" />
                      </button>
                      <span className="w-8 text-center text-sm">{item.quantity}</span>
                      <button
                        onClick={() => updateQuantity(item.productId, item.quantity + 1)}
                        className="p-1 rounded-full border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        <Plus className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 mt-2">
                      <input
                        type="number"
                        min="0.1"
                        step="0.1"
                        value={item.quantity}
                        onChange={(e) => updateQuantity(item.productId, Number(e.target.value))}
                        className="w-20 p-1.5 text-sm text-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg"
                      />
                      <span className="text-sm text-gray-500 dark:text-gray-400">{item.unit}</span>
                    </div>
                  )}
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {formatCurrency(item.price * item.quantity)}
                  </p>
                  <button
                    onClick={() => removeItem(item.productId)}
                    className="text-red-500 hover:text-red-600 mt-2"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      ))}

      <div className="flex items-center justify-between px-2">
        <button onClick={clearCart} className="text-sm text-gray-500 hover:text-red-500">
          {t("clear_cart", "Ondoa Vyote")}
        </button>
        <div className="text-right">
          <p className="text-sm text-gray-500 dark:text-gray-400">{t("total", "Jumla")}</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white">
            {formatCurrency(totalPrice)}
          </p>
        </div>
      </div>

      <Button onClick={() => navigate("/checkout")} className="w-full" size="lg">
        {t("proceed_checkout", "Endelea na Malipo")}
      </Button>
    </div>
  );
}
