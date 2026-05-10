// src/hooks/useProductForm.js

import { useReducer, useState } from "react";

const initialState = {
  name: "",
  description: "",
  type: "physical",
  price: "",
  discount_price: "",
  currency: "",
  quantity_in_stock: "",
  unit: "pcs",
  is_available: true,
  is_featured: false,
  tags: [],
  tax_inclusive: true,
  tax_rate: "0",
  external_link: "",
  language_code: "en",
};

function formReducer(state, action) {
  switch (action.type) {
    case "SET_FIELD":
      return { ...state, [action.field]: action.value };
    case "SET_MULTIPLE":
      return { ...state, ...action.fields };
    case "RESET":
      return { ...initialState, currency: action.defaultCurrency };
    default:
      return state;
  }
}

export function useProductForm(defaultCurrencyId) {
  const [state, dispatch] = useReducer(formReducer, {
    ...initialState,
    currency: defaultCurrencyId || "",
  });
  
  const [uploadedImages, setUploadedImages] = useState([]);
  const [imagePreviewUrls, setImagePreviewUrls] = useState([]);

  const setField = (field, value) => {
    dispatch({ type: "SET_FIELD", field, value });
  };

  const setFields = (fields) => {
    dispatch({ type: "SET_MULTIPLE", fields });
  };

  const resetForm = () => {
    imagePreviewUrls.forEach(url => URL.revokeObjectURL(url));
    dispatch({ type: "RESET", defaultCurrency: defaultCurrencyId });
    setUploadedImages([]);
    setImagePreviewUrls([]);
  };

  const addImages = (files) => {
    const newImages = [...uploadedImages, ...files];
    setUploadedImages(newImages);
    const newPreviews = files.map(file => URL.createObjectURL(file));
    setImagePreviewUrls([...imagePreviewUrls, ...newPreviews]);
  };

  const removeImage = (index) => {
    const newImages = uploadedImages.filter((_, i) => i !== index);
    setUploadedImages(newImages);
    URL.revokeObjectURL(imagePreviewUrls[index]);
    const newPreviews = imagePreviewUrls.filter((_, i) => i !== index);
    setImagePreviewUrls(newPreviews);
  };

  const buildFormData = () => {
    const formData = new FormData();
    
    formData.append("name", state.name);
    formData.append("price", state.price);
    formData.append("currency", state.currency);
    
    if (state.description) formData.append("description", state.description);
    formData.append("type", state.type);
    formData.append("quantity_in_stock", state.quantity_in_stock || "0");
    formData.append("unit", state.unit);
    formData.append("is_available", state.is_available ? "true" : "false");
    formData.append("is_featured", state.is_featured ? "true" : "false");
    formData.append("language_code", state.language_code);
    formData.append("tax_inclusive", state.tax_inclusive ? "true" : "false");
    formData.append("tax_rate", state.tax_rate || "0");
    
    if (state.discount_price) formData.append("discount_price", state.discount_price);
    if (state.external_link) formData.append("external_link", state.external_link);
    if (state.tags?.length > 0) formData.append("tags", JSON.stringify(state.tags));
    if (uploadedImages.length > 0) formData.append("image", uploadedImages[0]);
    
    return formData;
  };

  const validateForm = () => {
    const errors = {};
    
    if (!state.name?.trim()) errors.name = "Product name is required";
    if (!state.price || parseFloat(state.price) <= 0) errors.price = "Valid price is required";
    if (!state.currency) errors.currency = "Currency is required";
    
    if (state.discount_price && parseFloat(state.discount_price) >= parseFloat(state.price)) {
      errors.discount_price = "Discount price must be less than regular price";
    }
    
    return { isValid: Object.keys(errors).length === 0, errors };
  };

  return {
    formData: state,
    setField,
    setFields,
    resetForm,
    uploadedImages,
    imagePreviewUrls,
    addImages,
    removeImage,
    buildFormData,
    validateForm,
  };
}