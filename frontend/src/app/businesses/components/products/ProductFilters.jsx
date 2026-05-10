// src/app/businesses/components/products/ProductFilters.jsx

import React from "react";
import { useTranslation } from "react-i18next";
import { Search, Grid, List } from "lucide-react";

export function ProductFilters({
  searchQuery,
  onSearchChange,
  filterAvailable,
  onFilterChange,
  sortBy,
  onSortChange,
  viewMode,
  onViewModeChange,
}) {
  const { t } = useTranslation("businesses");

  return (
    <div className="flex flex-col sm:flex-row gap-3">
      <div className="flex-1 relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder={t("products.search_placeholder")}
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="flex gap-2">
        <select
          value={filterAvailable}
          onChange={(e) => onFilterChange(e.target.value)}
          className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
        >
          <option value="all">{t("products.filter_all")}</option>
          <option value="available">{t("products.filter_available")}</option>
          <option value="unavailable">{t("products.filter_unavailable")}</option>
        </select>

        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value)}
          className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
        >
          <option value="newest">{t("products.sort_newest")}</option>
          <option value="price_low">{t("products.sort_price_low")}</option>
          <option value="price_high">{t("products.sort_price_high")}</option>
          <option value="name">{t("products.sort_name")}</option>
        </select>

        <div className="flex border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <button
            onClick={() => onViewModeChange("grid")}
            className={`p-2 ${viewMode === "grid" ? "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400" : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400"}`}
          >
            <Grid className="w-4 h-4" />
          </button>
          <button
            onClick={() => onViewModeChange("list")}
            className={`p-2 ${viewMode === "list" ? "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400" : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400"}`}
          >
            <List className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}