// src/hooks/useProducts.js

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/axios";

export function useProducts(businessId) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchProducts = useCallback(async (filters = {}) => {
    if (!businessId) return;
    
    try {
      setLoading(true);
      const params = { ...filters };
      
      const res = await api.get(`/businesses/${businessId}/products/`, { params });
      const productList = Array.isArray(res.data) ? res.data : res.data.results || [];
      setProducts(productList);
      setError(null);
      return productList;
    } catch (err) {
      console.error("Failed to fetch products:", err);
      setError(err);
      return [];
    } finally {
      setLoading(false);
    }
  }, [businessId]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const createProduct = async (formData) => {
    try {
      const res = await api.post(`/businesses/${businessId}/products/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      await fetchProducts();
      return { success: true, data: res.data };
    } catch (err) {
      console.error("Failed to create product:", err);
      return { success: false, error: err };
    }
  };

  const updateProduct = async (slug, data) => {
    try {
      const res = await api.patch(`/businesses/${businessId}/products/${slug}/`, data);
      await fetchProducts();
      return { success: true, data: res.data };
    } catch (err) {
      console.error("Failed to update product:", err);
      return { success: false, error: err };
    }
  };

  const deleteProduct = async (slug) => {
    try {
      await api.delete(`/businesses/${businessId}/products/${slug}/`);
      await fetchProducts();
      return { success: true };
    } catch (err) {
      console.error("Failed to delete product:", err);
      return { success: false, error: err };
    }
  };

  const toggleAvailability = async (product) => {
    return updateProduct(product.slug, { is_available: !product.is_available });
  };

  return {
    products,
    loading,
    error,
    fetchProducts,
    createProduct,
    updateProduct,
    deleteProduct,
    toggleAvailability
  };
}