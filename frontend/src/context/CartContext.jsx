// src/context/CartContext.jsx

import { createContext, useContext, useEffect, useState } from "react";

const CartContext = createContext();

const STORAGE_KEY = "jamiikazini_cart";

function loadCart() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export const CartProvider = ({ children }) => {
  const [items, setItems] = useState(loadCart);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }, [items]);

  // Kikapu kinaweza kuwa na bidhaa kutoka biashara nyingi - checkout hutengeneza
  // order moja kwa kila biashara (angalia CheckoutPage.jsx).
  const addItem = (product, businessId, businessName, quantity = 1) => {
    // An offer-priced item is always kept distinct from a regular-priced cart
    // line for the same product - merging them would corrupt the negotiated price.
    const offerId = product.offerId || null;
    setItems((prev) => {
      const existing = !offerId && prev.find((i) => i.productId === product.id && i.businessId === businessId && !i.offerId);
      if (existing) {
        return prev.map((i) =>
          i.productId === product.id && i.businessId === businessId && !i.offerId
            ? { ...i, quantity: i.quantity + quantity }
            : i
        );
      }
      return [
        ...prev,
        {
          productId: product.id,
          businessId,
          businessName,
          name: product.name,
          price: Number(product.final_price ?? product.price),
          image: product.image || null,
          unit: product.unit || "pcs",
          quantity,
          offerId,
        },
      ];
    });
    return true;
  };

  const removeItem = (productId) => {
    setItems((prev) => prev.filter((i) => i.productId !== productId));
  };

  const updateQuantity = (productId, quantity) => {
    if (quantity <= 0) {
      removeItem(productId);
      return;
    }
    setItems((prev) => prev.map((i) => (i.productId === productId ? { ...i, quantity } : i)));
  };

  const clearCart = () => setItems([]);

  const totalItems = items.reduce((sum, i) => sum + i.quantity, 0);
  const totalPrice = items.reduce((sum, i) => sum + i.price * i.quantity, 0);

  // Group into one section per seller, so cart/checkout can produce one
  // Order per business while still being one cart/one action for the buyer.
  const itemsByBusiness = Object.values(
    items.reduce((groups, item) => {
      const group = groups[item.businessId] || {
        businessId: item.businessId,
        businessName: item.businessName,
        items: [],
        subtotal: 0,
      };
      group.items.push(item);
      group.subtotal += item.price * item.quantity;
      groups[item.businessId] = group;
      return groups;
    }, {})
  );

  return (
    <CartContext.Provider
      value={{
        items,
        addItem,
        removeItem,
        updateQuantity,
        clearCart,
        totalItems,
        totalPrice,
        itemsByBusiness,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => useContext(CartContext);
