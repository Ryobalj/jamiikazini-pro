// src/app/businesses/components/products/ProductCard.jsx

import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Package, Eye, Trash2, CheckCircle, XCircle, Box, ChevronLeft, ChevronRight,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { useCurrency } from "@/context/CurrencyContext";
import { getAllProductImages } from "@/utils/productHelpers";

export function ProductCard({ product, onView, onDelete }) {
  const { t } = useTranslation("businesses");
  const { formatCurrency } = useCurrency();
  const [imgIndex, setImgIndex] = useState(0);
  
  const images = getAllProductImages(product);

  return (
    <Card className="group relative overflow-hidden hover:shadow-lg transition-all duration-300 cursor-pointer">
      <div 
        className="relative h-48 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700"
        onClick={onView}
      >
        {images.length > 0 ? (
          <>
            <img
              src={images[imgIndex]}
              alt={product.name}
              className="w-full h-full object-cover"
              onError={(e) => { e.target.style.display = "none"; }}
            />
            {images.length > 1 && (
              <>
                <button
                  onClick={(e) => { e.stopPropagation(); setImgIndex(p => p > 0 ? p - 1 : images.length - 1); }}
                  className="absolute left-2 top-1/2 -translate-y-1/2 p-1 bg-black/50 rounded-full text-white opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); setImgIndex(p => p < images.length - 1 ? p + 1 : 0); }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 bg-black/50 rounded-full text-white opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
                <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                  {images.map((_, i) => (
                    <span key={i} className={`w-1.5 h-1.5 rounded-full ${i === imgIndex ? "bg-white" : "bg-white/50"}`} />
                  ))}
                </div>
              </>
            )}
          </>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <Package className="w-16 h-16 text-gray-400" />
          </div>
        )}
        
        <div className="absolute top-3 left-3">
          {product.is_available && product.quantity_in_stock > 0 ? (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
              <CheckCircle className="w-3 h-3" /> {t("products.available")}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-400">
              <XCircle className="w-3 h-3" /> {t("products.unavailable")}
            </span>
          )}
        </div>

        {product.is_featured && (
          <div className="absolute top-3 right-3">
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400">
              ⭐ {t("products.featured")}
            </span>
          </div>
        )}

        {product.quantity_in_stock > 0 && (
          <div className="absolute bottom-3 left-3">
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
              <Box className="w-3 h-3" /> {product.quantity_in_stock} {product.unit_display || product.unit}
            </span>
          </div>
        )}
        
        {images.length > 1 && (
          <div className="absolute bottom-3 right-3 bg-black/50 text-white text-xs px-2 py-0.5 rounded-full">
            {images.length} 📸
          </div>
        )}
      </div>

      <CardContent className="p-4" onClick={onView}>
        <h3 className="font-semibold text-gray-900 dark:text-white truncate">{product.name}</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
          {product.description || t("products.no_description")}
        </p>

        <div className="flex items-baseline gap-2 mt-3">
          {product.discount_price ? (
            <>
              <span className="text-xl font-bold text-gray-900 dark:text-white">
                {product.currency_symbol || "TSh"} {formatCurrency(product.discount_price)}
              </span>
              <span className="text-sm text-gray-400 line-through">
                {product.currency_symbol || "TSh"} {formatCurrency(product.price)}
              </span>
            </>
          ) : (
            <span className="text-xl font-bold text-gray-900 dark:text-white">
              {product.currency_symbol || "TSh"} {formatCurrency(product.price)}
            </span>
          )}
        </div>

        {product.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {product.tags.slice(0, 3).map((tag, idx) => (
              <span key={idx} className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded-full text-xs text-gray-600 dark:text-gray-400">{tag}</span>
            ))}
            {product.tags.length > 3 && (
              <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded-full text-xs text-gray-600 dark:text-gray-400">+{product.tags.length - 3}</span>
            )}
          </div>
        )}
      </CardContent>

      <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
        <div className="flex gap-1">
          <button onClick={(e) => { e.stopPropagation(); onView(); }} className="p-2 bg-white dark:bg-gray-800 rounded-full shadow-lg hover:bg-gray-100 dark:hover:bg-gray-700" title={t("products.view_details")}>
            <Eye className="w-4 h-4" />
          </button>
          <button onClick={(e) => { e.stopPropagation(); onDelete(); }} className="p-2 bg-white dark:bg-gray-800 rounded-full shadow-lg hover:bg-red-100 dark:hover:bg-red-900" title={t("products.delete")}>
            <Trash2 className="w-4 h-4 text-red-500" />
          </button>
        </div>
      </div>
    </Card>
  );
}