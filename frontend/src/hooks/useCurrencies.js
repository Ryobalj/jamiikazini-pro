// src/hooks/useCurrencies.js

import { useState, useEffect } from "react";
import api from "@/lib/axios";

export function useCurrencies() {
  const [currencies, setCurrencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCurrencies = async () => {
      try {
        setLoading(true);
        const res = await api.get("/payments/currencies/");
        const currencyList = Array.isArray(res.data) ? res.data : res.data.results || [];
        setCurrencies(currencyList.filter(c => c.is_active));
        setError(null);
      } catch (err) {
        console.error("Failed to fetch currencies:", err);
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchCurrencies();
  }, []);

  const getDefaultCurrency = () => {
    return currencies.find(c => c.code === "TZS") || currencies[0];
  };

  const getCurrencyById = (id) => currencies.find(c => c.id === id);
  
  const getCurrencyByCode = (code) => currencies.find(c => c.code === code);

  return {
    currencies,
    loading,
    error,
    getDefaultCurrency,
    getCurrencyById,
    getCurrencyByCode
  };
}