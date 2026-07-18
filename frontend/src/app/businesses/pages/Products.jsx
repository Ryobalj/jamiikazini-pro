// src/app/businesses/pages/Products.jsx

import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Plus, Loader2, Package } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";

import { useProducts } from "@/hooks/useProducts";
import { useCurrencies } from "@/hooks/useCurrencies";
import { ProductFilters } from "@/app/businesses/components/products/ProductFilters";
import { ProductCard } from "@/app/businesses/components/products/ProductCard";
import { ProductListItem } from "@/app/businesses/components/products/ProductListItem";
import { AddProductModal } from "@/app/businesses/components/products/AddProductModal";
import { ProductDetailModal } from "@/app/businesses/components/products/ProductDetailModal";
import { DeleteConfirmModal } from "@/app/businesses/components/products/DeleteConfirmModal";
import { filterAndSortProducts } from "@/utils/productHelpers";

export default function Products() {
  const { id: businessId } = useParams();
  const { t } = useTranslation("businesses");
  
  const { products, loading, toggleAvailability, deleteProduct } = useProducts(businessId);
  const { currencies, getDefaultCurrency } = useCurrencies();
  
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState("grid");
  const [filterAvailable, setFilterAvailable] = useState("all");
  const [sortBy, setSortBy] = useState("newest");
  const [categoryFilter, setCategoryFilter] = useState("all");
  
  const [showAddModal, setShowAddModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  const categoryOptions = [...new Set(products.map(p => p.category_name).filter(Boolean))].sort();

  useEffect(() => {
    let filtered = [...products];

    if (filterAvailable === "available") {
      filtered = filtered.filter(p => p.is_available && p.quantity_in_stock > 0);
    } else if (filterAvailable === "unavailable") {
      filtered = filtered.filter(p => !p.is_available || p.quantity_in_stock === 0);
    }

    if (categoryFilter !== "all") {
      filtered = filtered.filter(p => p.category_name === categoryFilter);
    }

    const sorted = filterAndSortProducts(filtered, searchQuery, sortBy);
    setFilteredProducts(sorted);
  }, [products, searchQuery, sortBy, filterAvailable, categoryFilter]);

  const handleProductCreated = () => {
    setShowAddModal(false);
    toast.success(t("products.success.created"));
  };

  const handleDeleteClick = (product) => {
    setSelectedProduct(product);
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = async () => {
    if (!selectedProduct) return;
    
    const result = await deleteProduct(selectedProduct.slug);
    if (result.success) {
      toast.success(t("products.success.deleted"));
      setShowDeleteConfirm(false);
      setSelectedProduct(null);
    } else {
      toast.error(t("products.errors.delete_failed"));
    }
  };

  const handleToggleAvailability = async (product) => {
    const result = await toggleAvailability(product);
    if (result.success) {
      toast.success(t("products.success.updated"));
    } else {
      toast.error(t("products.errors.update_failed"));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-[1600px] mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
            {t("dashboard.products")}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {filteredProducts.length} {t("products.total")}
          </p>
        </div>
        <Button onClick={() => setShowAddModal(true)} className="gap-2">
          <Plus className="w-4 h-4" /> {t("products.add_product")}
        </Button>
      </div>

      <ProductFilters
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        filterAvailable={filterAvailable}
        onFilterChange={setFilterAvailable}
        sortBy={sortBy}
        onSortChange={setSortBy}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        categoryFilter={categoryFilter}
        onCategoryFilterChange={setCategoryFilter}
        categoryOptions={categoryOptions}
      />

      {filteredProducts.length > 0 ? (
        viewMode === "grid" ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredProducts.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onView={() => { setSelectedProduct(product); setShowDetailModal(true); }}
                onDelete={() => handleDeleteClick(product)}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredProducts.map((product) => (
              <ProductListItem
                key={product.id}
                product={product}
                onView={() => { setSelectedProduct(product); setShowDetailModal(true); }}
                onDelete={() => handleDeleteClick(product)}
              />
            ))}
          </div>
        )
      ) : (
        <Card>
          <CardContent className="text-center py-12">
            <Package className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {t("products.no_products")}
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              {t("products.no_products_desc")}
            </p>
            <Button onClick={() => setShowAddModal(true)}>
              <Plus className="w-4 h-4 mr-2" /> {t("products.add_first")}
            </Button>
          </CardContent>
        </Card>
      )}

      {showAddModal && (
        <AddProductModal
          businessId={businessId}
          currencies={currencies}
          defaultCurrencyId={getDefaultCurrency()?.id}
          onClose={() => setShowAddModal(false)}
          onSuccess={handleProductCreated}
        />
      )}

      {showDetailModal && selectedProduct && (
        <ProductDetailModal
          product={selectedProduct}
          onClose={() => { setShowDetailModal(false); setSelectedProduct(null); }}
          onToggleAvailability={handleToggleAvailability}
          onDelete={() => handleDeleteClick(selectedProduct)}
        />
      )}

      {showDeleteConfirm && selectedProduct && (
        <DeleteConfirmModal
          productName={selectedProduct.name}
          onClose={() => { setShowDeleteConfirm(false); setSelectedProduct(null); }}
          onConfirm={handleDeleteConfirm}
        />
      )}
    </div>
  );
}