// src/app/businesses/components/products/AddProductModal.jsx

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { X, Loader2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import InputField from "@/components/InputField";
import TagInput from "@/components/TagInput";
import { toast } from "react-toastify";
import { useProductForm } from "@/hooks/useProductForm";
import { useProducts } from "@/hooks/useProducts";
import { extractErrorMessage } from "@/utils/productHelpers";

export function AddProductModal({ businessId, currencies, defaultCurrencyId, onClose, onSuccess }) {
  const { t } = useTranslation("businesses");
  const { createProduct } = useProducts(businessId);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [suggestedTags, setSuggestedTags] = useState([]);
  const [categories, setCategories] = useState([]);
  
  const {
    formData,
    setField,
    resetForm,
    uploadedImages,
    imagePreviewUrls,
    addImages,
    removeImage,
    buildFormData,
    validateForm,
  } = useProductForm(defaultCurrencyId);

  useEffect(() => {
    const fetchBusinessDetails = async () => {
      try {
        const { default: api } = await import("@/lib/axios");
        const { getSuggestedTags } = await import("@/data/suggestedTags");
        const res = await api.get(`/businesses/${businessId}/`);
        const categoryName = res.data.category_name || res.data.category?.name;
        setSuggestedTags(getSuggestedTags(categoryName));
      } catch (error) {
        console.error("Failed to fetch business details:", error);
        const { getSuggestedTags } = await import("@/data/suggestedTags");
        setSuggestedTags(getSuggestedTags("default"));
      }
    };
    
    if (businessId) {
      fetchBusinessDetails();
    }
  }, [businessId]);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const { default: api } = await import("@/lib/axios");
        const res = await api.get("/product-categories/?ordering=name");
        setCategories(Array.isArray(res.data) ? res.data : res.data?.results || []);
      } catch (error) {
        console.error("Failed to fetch product categories:", error);
      }
    };
    fetchCategories();
  }, []);

  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;
    
    if (files.length + uploadedImages.length > 10) {
      toast.error(t("products.errors.max_images", { max: 10 }));
      return;
    }
    
    addImages(files);
  };

  const handleSubmit = async () => {
    const { isValid, errors } = validateForm();
    
    if (!isValid) {
      const firstError = Object.values(errors)[0];
      toast.error(firstError);
      return;
    }

    setIsSubmitting(true);

    try {
      const productData = buildFormData();
      const result = await createProduct(productData);
      
      if (result.success) {
        toast.success(t("products.success.created"));
        resetForm();
        onSuccess();
      } else {
        const errorMsg = extractErrorMessage(result.error, t);
        toast.error(errorMsg);
      }
    } catch (error) {
      console.error("Failed to create product:", error);
      const errorMsg = extractErrorMessage(error, t);
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white dark:bg-gray-800 px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {t("products.add_product")}
          </h2>
          <button onClick={handleClose} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <CardContent className="p-6">
          <div className="space-y-4">
            <InputField
              label={t("products.name") + " *"}
              value={formData.name}
              onChange={(e) => setField("name", e.target.value)}
              placeholder={t("products.name_placeholder")}
            />

            <div>
              <label className="block text-sm font-medium mb-2">{t("products.description")}</label>
              <textarea
                value={formData.description}
                onChange={(e) => setField("description", e.target.value)}
                rows={3}
                className="w-full p-3 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg"
                placeholder={t("products.description_placeholder")}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">{t("products.type")}</label>
                <select
                  value={formData.type}
                  onChange={(e) => setField("type", e.target.value)}
                  className="w-full p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <option value="physical">{t("products.types.physical")}</option>
                  <option value="digital">{t("products.types.digital")}</option>
                  <option value="service">{t("products.types.service")}</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">{t("products.currency")} *</label>
                <select
                  value={formData.currency}
                  onChange={(e) => setField("currency", e.target.value)}
                  className="w-full p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <option value="">{t("products.select_currency")}</option>
                  {currencies.map(c => (
                    <option key={c.id} value={c.id}>{c.code} ({c.symbol})</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <InputField
                label={t("products.price") + " *"}
                type="number"
                step="0.01"
                value={formData.price}
                onChange={(e) => setField("price", e.target.value)}
                placeholder="0.00"
              />
              <InputField
                label={t("products.discount_price")}
                type="number"
                step="0.01"
                value={formData.discount_price}
                onChange={(e) => setField("discount_price", e.target.value)}
                placeholder="0.00"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <InputField
                label={t("products.stock")}
                type="number"
                value={formData.quantity_in_stock}
                onChange={(e) => setField("quantity_in_stock", e.target.value)}
                placeholder="0"
                step="0.001"
                min="0"
              />
              <div>
                <label className="block text-sm font-medium mb-2">{t("products.unit")}</label>
                <select
                  value={formData.unit}
                  onChange={(e) => setField("unit", e.target.value)}
                  className="w-full p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <option value="pcs">pcs</option>
                  <option value="kg">kg</option>
                  <option value="g">g</option>
                  <option value="l">l</option>
                  <option value="ml">ml</option>
                  <option value="box">box</option>
                  <option value="pack">pack</option>
                  <option value="dozen">dozen</option>
                  <option value="pair">pair</option>
                  <option value="set">set</option>
                  <option value="m">m</option>
                  <option value="cm">cm</option>
                  <option value="hour">hour</option>
                  <option value="day">day</option>
                  <option value="session">session</option>
                  <option value="gunia">gunia</option>
                  <option value="debe">debe</option>
                  <option value="fungu">fungu</option>
                  <option value="roli">roli</option>
                  <option value="bale">bale</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">{t("products.tax_rate")} (%)</label>
                <InputField
                  type="number"
                  step="0.01"
                  value={formData.tax_rate}
                  onChange={(e) => setField("tax_rate", e.target.value)}
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">{t("products.language")}</label>
                <select
                  value={formData.language_code}
                  onChange={(e) => setField("language_code", e.target.value)}
                  className="w-full p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <option value="sw">Swahili</option>
                  <option value="en">English</option>
                  <option value="fr">French</option>
                  <option value="ar">Arabic</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">{t("products.category")}</label>
              <select
                value={formData.category}
                onChange={(e) => setField("category", e.target.value)}
                className="w-full p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
              >
                <option value="">{t("products.select_category")}</option>
                {categories.filter((c) => !c.parent).map((parent) => {
                  const children = categories.filter((c) => c.parent === parent.id);
                  if (children.length === 0) {
                    return (
                      <option key={parent.id} value={parent.id}>{parent.name}</option>
                    );
                  }
                  return (
                    <optgroup key={parent.id} label={parent.name}>
                      {children.map((child) => (
                        <option key={child.id} value={child.id}>{child.name}</option>
                      ))}
                    </optgroup>
                  );
                })}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">{t("products.tags")}</label>
              <TagInput
                value={formData.tags}
                onChange={(tags) => setField("tags", tags)}
                suggestions={suggestedTags}
                placeholder={t("products.tags_placeholder")}
                maxTags={15}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t("products.tags_hint")}</p>
            </div>

            <InputField
              label={t("products.external_link")}
              value={formData.external_link}
              onChange={(e) => setField("external_link", e.target.value)}
              placeholder="https://"
            />

            <div>
              <label className="block text-sm font-medium mb-2">
                {t("products.images")} ({uploadedImages.length}/10)
              </label>
              
              {imagePreviewUrls.length > 0 && (
                <div className="grid grid-cols-4 gap-2 mb-3">
                  {imagePreviewUrls.map((url, index) => (
                    <div key={index} className="relative group">
                      <img src={url} alt={`Preview ${index + 1}`} className="w-full h-20 object-cover rounded-lg" />
                      <button
                        type="button"
                        onClick={() => removeImage(index)}
                        className="absolute -top-1 -right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <X className="w-3 h-3" />
                      </button>
                      {index === 0 && (
                        <span className="absolute bottom-1 left-1 bg-black/50 text-white text-xs px-1.5 py-0.5 rounded">
                          Main
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
              
              <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                <div className="flex flex-col items-center justify-center">
                  <Upload className="w-8 h-8 text-gray-400 mb-2" />
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t("products.click_to_upload")}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{t("products.images_hint")}</p>
                </div>
                <input type="file" accept="image/*" multiple onChange={handleImageUpload} className="hidden" />
              </label>
            </div>

            <div className="flex gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_available}
                  onChange={(e) => setField("is_available", e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm">{t("products.available_for_sale")}</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_featured}
                  onChange={(e) => setField("is_featured", e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm">{t("products.featured")}</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.tax_inclusive}
                  onChange={(e) => setField("tax_inclusive", e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm">{t("products.tax_inclusive")}</span>
              </label>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <Button variant="outline" onClick={handleClose} className="flex-1">
              {t("cancel")}
            </Button>
            <Button onClick={handleSubmit} disabled={isSubmitting} className="flex-1">
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {t("products.creating")}
                </>
              ) : (
                t("products.create")
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}