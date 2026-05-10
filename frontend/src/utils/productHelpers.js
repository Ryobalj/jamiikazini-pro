// src/utils/productHelpers.js

export function getAllProductImages(product) {
  const images = [];
  if (product.image) images.push(product.image);
  if (product.additional_images) {
    if (Array.isArray(product.additional_images)) {
      images.push(...product.additional_images);
    }
  }
  return images;
}

export function filterAndSortProducts(products, searchQuery, sortBy) {
  let filtered = [...products];

  if (searchQuery?.trim()) {
    const query = searchQuery.toLowerCase();
    filtered = filtered.filter(p =>
      p.name?.toLowerCase().includes(query) ||
      p.description?.toLowerCase().includes(query) ||
      p.tags?.some(tag => tag.toLowerCase().includes(query))
    );
  }

  switch (sortBy) {
    case "price_low":
      filtered.sort((a, b) => (a.discount_price || a.price) - (b.discount_price || b.price));
      break;
    case "price_high":
      filtered.sort((a, b) => (b.discount_price || b.price) - (a.discount_price || a.price));
      break;
    case "name":
      filtered.sort((a, b) => a.name?.localeCompare(b.name || ""));
      break;
    default:
      filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }

  return filtered;
}

export function extractErrorMessage(error, t) {
  let errorMsg = t("products.errors.create_failed");
  
  if (error.response?.data) {
    const data = error.response.data;
    if (typeof data === "string") {
      errorMsg = data;
    } else if (data.detail) {
      errorMsg = data.detail;
    } else if (data.name) {
      errorMsg = Array.isArray(data.name) ? data.name[0] : data.name;
    } else if (data.price) {
      errorMsg = Array.isArray(data.price) ? data.price[0] : data.price;
    } else {
      const firstKey = Object.keys(data)[0];
      const firstError = data[firstKey];
      errorMsg = Array.isArray(firstError) ? firstError[0] : firstError;
    }
  }
  
  return errorMsg;
}