// src/app/businesses/components/products/ProductListItem.jsx

import React from "react";
import { useTranslation } from "react-i18next";
import { Package, Eye, Trash2 } from "lucide-react";
import { useCurrency } from "@/context/CurrencyContext";
import { getAllProductImages } from "@/utils/productHelpers";

export function ProductListItem({ product, onView, onDelete }) {
  const { t } = useTranslation("businesses");
  const { formatCurrency } = useCurrency();
  const images = getAllProductImages(product);

  return (
    <div className="flex items-center gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
      <div className="w-16 h-16 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center overflow-hidden flex-shrink-0">
        {images.length > 0 ? (
          <img src={images[0]} alt={product.name} className="w-full h-full object-cover" />
        ) : (
          <Package className="w-8 h-8 text-gray-400" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="font-medium text-gray-900 dark:text-white truncate">{product.name}</h3>
          <span className={`px-2 py-0.5 rounded-full text-xs whitespace-nowrap ${
            product.is_available && product.quantity_in_stock > 0 
              ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400" 
              : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
          }`}>
            {product.quantity_in_stock} {product.unit_display || product.unit}
          </span>
          {product.is_featured && (
            <span className="px-2 py-0.5 rounded-full text-xs bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 whitespace-nowrap">
              ⭐ {t("products.featured")}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-1 mt-1">
          {product.description || t("products.no_description")}
        </p>
        {product.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {product.tags.slice(0, 5).map((tag, idx) => (
              <span key={idx} className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded-full text-xs text-gray-600 dark:text-gray-400">
                {tag}
              </span>
            ))}
            {product.tags.length > 5 && (
              <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded-full text-xs text-gray-600 dark:text-gray-400">
                +{product.tags.length - 5}
              </span>
            )}
          </div>
        )}
      </div>

      <div className="text-right flex-shrink-0">
        <p className="font-bold text-gray-900 dark:text-white">
          {product.currency_symbol || "TSh"} {formatCurrency(product.discount_price || product.price)}
        </p>
        {product.discount_price && (
          <p className="text-sm text-gray-400 line-through">
            {product.currency_symbol || "TSh"} {formatCurrency(product.price)}
          </p>
        )}
      </div>

      <div className="flex items-center gap-1 flex-shrink-0">
        <button 
          onClick={onView} 
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          title={t("products.view_details")}
        >
          <Eye className="w-4 h-4" />
        </button>
        <button 
          onClick={onDelete} 
          className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
          title={t("products.delete")}
        >
          <Trash2 className="w-4 h-4 text-red-500" />
        </button>
      </div>
    </div>
  );
}