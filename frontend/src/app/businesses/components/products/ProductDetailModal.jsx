// src/app/businesses/components/products/ProductDetailModal.jsx

import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { X, ChevronLeft, ChevronRight, Package, CheckCircle, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useCurrency } from "@/context/CurrencyContext";
import { getAllProductImages } from "@/utils/productHelpers";

export function ProductDetailModal({ product, onClose, onToggleAvailability, onDelete }) {
  const { t } = useTranslation("businesses");
  const { formatCurrency } = useCurrency();
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  
  const images = getAllProductImages(product);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={onClose}>
      <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="relative h-64 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700">
          {images.length > 0 ? (
            <>
              <img
                src={images[currentImageIndex]}
                alt={product.name}
                className="w-full h-full object-cover"
                onError={(e) => { e.target.src = ""; }}
              />
              {images.length > 1 && (
                <>
                  <button
                    onClick={() => setCurrentImageIndex(p => p > 0 ? p - 1 : images.length - 1)}
                    className="absolute left-4 top-1/2 -translate-y-1/2 p-2 bg-black/50 rounded-full text-white hover:bg-black/70"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => setCurrentImageIndex(p => p < images.length - 1 ? p + 1 : 0)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 p-2 bg-black/50 rounded-full text-white hover:bg-black/70"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                  <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1.5">
                    {images.map((_, i) => (
                      <button
                        key={i}
                        onClick={() => setCurrentImageIndex(i)}
                        className={`w-2 h-2 rounded-full transition-all ${
                          i === currentImageIndex ? "bg-white w-4" : "bg-white/50 hover:bg-white/70"
                        }`}
                      />
                    ))}
                  </div>
                  <div className="absolute bottom-4 right-4 bg-black/50 text-white text-xs px-2 py-1 rounded-full">
                    {currentImageIndex + 1} / {images.length}
                  </div>
                </>
              )}
            </>
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <Package className="w-20 h-20 text-gray-400" />
            </div>
          )}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 bg-black/50 rounded-full text-white hover:bg-black/70"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <CardContent className="p-6">
          <div className="space-y-4">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{product.name}</h2>
                {product.is_featured && (
                  <span className="px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 text-xs rounded-full">
                    ⭐ {t("products.featured")}
                  </span>
                )}
              </div>
              <p className="text-gray-500 dark:text-gray-400 mt-2">
                {product.description || t("products.no_description")}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2 text-sm">
              <div><span className="text-gray-500">{t("products.type")}:</span> {t(`products.types.${product.type}`)}</div>
              <div><span className="text-gray-500">{t("products.sku")}:</span> {product.sku || "-"}</div>
              <div><span className="text-gray-500">{t("products.unit")}:</span> {product.unit_display || product.unit}</div>
              <div>
                <span className="text-gray-500">{t("products.tax_rate")}:</span> {product.tax_rate}% 
                {product.tax_inclusive && ` (${t("products.tax_inclusive")})`}
              </div>
              <div><span className="text-gray-500">{t("products.language")}:</span> {product.language_display || product.language_code}</div>
              {product.external_link && (
                <div className="col-span-2">
                  <span className="text-gray-500">{t("products.external_link")}:</span>{" "}
                  <a href={product.external_link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    {product.external_link}
                  </a>
                </div>
              )}
            </div>

            {product.tags?.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {product.tags.map((tag, idx) => (
                  <span key={idx} className="px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded-full text-sm">
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">{t("products.price")}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {product.currency_symbol || "TSh"} {formatCurrency(product.discount_price || product.price)}
                </p>
                {product.discount_price && (
                  <p className="text-sm text-gray-400 line-through">
                    {product.currency_symbol || "TSh"} {formatCurrency(product.price)}
                  </p>
                )}
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">{t("products.stock")}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {product.quantity_in_stock} {product.unit_display || product.unit}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${
                product.is_available && product.quantity_in_stock > 0 
                  ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400" 
                  : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
              }`}>
                {product.is_available && product.quantity_in_stock > 0 ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                {product.is_available && product.quantity_in_stock > 0 ? t("products.available") : t("products.unavailable")}
              </span>
            </div>

            <div className="flex gap-3 pt-4">
              <Button variant="outline" onClick={() => onToggleAvailability(product)} className="flex-1">
                {product.is_available ? t("products.mark_unavailable") : t("products.mark_available")}
              </Button>
              <Button variant="destructive" onClick={() => { onClose(); onDelete(); }} className="flex-1">
                {t("products.delete")}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}