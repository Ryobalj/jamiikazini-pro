// src/context/CurrencyContext.jsx

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import api from "@/lib/axios";

const CurrencyContext = createContext();

const DEFAULT_CURRENCY = "TZS";

const SUPPORTED_CURRENCIES = [
  { code: "TZS", symbol: "TSh", nameKey: "currencies.tzs" },
  { code: "KES", symbol: "KSh", nameKey: "currencies.kes" },
  { code: "UGX", symbol: "USh", nameKey: "currencies.ugx" },
  { code: "RWF", symbol: "RF", nameKey: "currencies.rwf" },
  { code: "BIF", symbol: "FBu", nameKey: "currencies.bif" },
  { code: "USD", symbol: "$", nameKey: "currencies.usd" },
  { code: "EUR", symbol: "€", nameKey: "currencies.eur" },
  { code: "GBP", symbol: "£", nameKey: "currencies.gbp" },
];

export const CurrencyProvider = ({ children }) => {
  const { t, i18n } = useTranslation();
  
  const [currency, setCurrency] = useState(DEFAULT_CURRENCY);
  const [rates, setRates] = useState({ [DEFAULT_CURRENCY]: 1 });
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Load preferred currency from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("preferred_currency");
    if (saved && SUPPORTED_CURRENCIES.some(c => c.code === saved)) {
      setCurrency(saved);
    }
  }, []);

  const fetchRates = useCallback(async (showToast = false) => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      console.log(t("currencies.errors.no_token"));
      setLoading(false);
      setError(t("currencies.errors.not_authenticated"));
      setAutoRefresh(false);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const res = await api.get("/payments/exchange-rates/");
      
      if (res.data) {
        const ratesList = Array.isArray(res.data) ? res.data : res.data.results || [];
        const ratesObj = { TZS: 1 };
        
        ratesList.forEach(rate => {
          const baseCode = rate.base_currency?.code || rate.base_currency_code;
          const targetCode = rate.target_currency?.code || rate.target_currency_code;
          const rateValue = parseFloat(rate.rate);
          
          if (baseCode === "TZS" && targetCode) {
            ratesObj[targetCode] = rateValue;
          }
        });
        
        setRates(ratesObj);
        setLastUpdated(new Date());
        console.log(t("currencies.success.rates_updated", { count: Object.keys(ratesObj).length }));
        
        if (showToast) {
          toast.success(t("currencies.success.rates_refreshed"));
        }
      } else {
        throw new Error(t("currencies.errors.invalid_response"));
      }
    } catch (err) {
      console.error(t("currencies.errors.fetch_failed"), err);
      
      if (err.response?.status === 401) {
        console.warn(t("currencies.errors.unauthorized"));
        setAutoRefresh(false);
        setError(t("currencies.errors.auth_required"));
        if (showToast) {
          toast.error(t("currencies.errors.session_expired"));
        }
      } else if (err.response?.status === 500) {
        setError(t("currencies.errors.server_error"));
        if (showToast) {
          toast.error(t("currencies.errors.server_error"));
        }
      } else {
        setError(t("currencies.warnings.using_estimated"));
        if (showToast) {
          toast.warning(t("currencies.warnings.using_fallback"));
        }
      }
      
      // Set fallback rates
      setRates({
        TZS: 1,
        KES: 0.047,
        UGX: 28,
        RWF: 0.83,
        BIF: 0.87,
        USD: 0.00037,
        EUR: 0.00034,
        GBP: 0.00029,
      });
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
    }
  }, [t]);

  // Initial fetch
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      fetchRates();
    } else {
      setLoading(false);
      setError(t("currencies.errors.not_authenticated"));
      setAutoRefresh(false);
    }
  }, [fetchRates, t]);

  // Auto-refresh rates
  useEffect(() => {
    if (!autoRefresh) return;
    
    const token = localStorage.getItem("access_token");
    if (!token) {
      setAutoRefresh(false);
      return;
    }
    
    const interval = setInterval(() => {
      console.log(t("currencies.info.auto_refreshing"));
      fetchRates();
    }, 15 * 60 * 1000); // 15 minutes
    
    return () => clearInterval(interval);
  }, [fetchRates, autoRefresh, t]);

  // Refresh when language changes (if rates are older than 5 minutes)
  useEffect(() => {
    if (lastUpdated) {
      const age = Date.now() - lastUpdated.getTime();
      if (age > 5 * 60 * 1000) {
        fetchRates();
      }
    }
  }, [i18n.language, lastUpdated, fetchRates]);

  const changeCurrency = (code) => {
    if (SUPPORTED_CURRENCIES.some(c => c.code === code)) {
      setCurrency(code);
      localStorage.setItem("preferred_currency", code);
      
      const token = localStorage.getItem("access_token");
      if (token) {
        api.patch("/auth/me/", { preferred_currency: code })
          .catch(err => {
            console.warn(t("currencies.errors.save_preference_failed"), err);
          });
      }
      
      toast.success(t("currencies.success.currency_changed", { currency: code }));
    }
  };

  const convert = (amount, fromCurrency = "TZS", toCurrency = currency) => {
    if (!amount) return 0;
    
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount)) return 0;
    
    if (fromCurrency === toCurrency) return numAmount;
    
    const fromRate = rates[fromCurrency] || 1;
    const toRate = rates[toCurrency] || 1;
    
    const amountInTZS = fromCurrency === "TZS" ? numAmount : numAmount / fromRate;
    return amountInTZS * toRate;
  };

  const formatCurrency = (amount, options = {}) => {
    const converted = convert(amount);
    const { 
      minimumFractionDigits = 0, 
      maximumFractionDigits = 2,
      showSymbol = true,
      showCode = false,
    } = options;
    
    const formatted = converted.toLocaleString(i18n.language, {
      minimumFractionDigits,
      maximumFractionDigits,
    });
    
    if (showSymbol) {
      const symbol = getCurrencySymbol();
      return `${symbol} ${formatted}`;
    }
    
    if (showCode) {
      return `${currency} ${formatted}`;
    }
    
    return formatted;
  };

  const formatCompact = (amount) => {
    const converted = convert(amount);
    const symbol = getCurrencySymbol();
    
    if (converted >= 1000000) {
      return `${symbol} ${(converted / 1000000).toFixed(1)}M`;
    }
    if (converted >= 1000) {
      return `${symbol} ${(converted / 1000).toFixed(1)}K`;
    }
    return `${symbol} ${converted.toFixed(2)}`;
  };

  const getCurrencySymbol = (code = currency) => {
    const curr = SUPPORTED_CURRENCIES.find(c => c.code === code);
    return curr?.symbol || code;
  };

  const getCurrencyName = (code = currency) => {
    const curr = SUPPORTED_CURRENCIES.find(c => c.code === code);
    return curr?.nameKey ? t(curr.nameKey) : code;
  };

  const getSupportedCurrenciesWithNames = () => {
    return SUPPORTED_CURRENCIES.map(c => ({
      ...c,
      name: t(c.nameKey),
    }));
  };

  const refreshRates = () => {
    const token = localStorage.getItem("access_token");
    if (token) {
      fetchRates(true);
    } else {
      toast.error(t("currencies.errors.login_required"));
    }
  };

  const toggleAutoRefresh = (enabled) => {
    setAutoRefresh(enabled);
    if (enabled) {
      toast.info(t("currencies.info.auto_refresh_enabled"));
    } else {
      toast.info(t("currencies.info.auto_refresh_disabled"));
    }
  };

  return (
    <CurrencyContext.Provider
      value={{
        currency,
        rates,
        loading,
        error,
        lastUpdated,
        convert,
        formatCurrency,
        formatCompact,
        changeCurrency,
        refreshRates,
        toggleAutoRefresh,
        autoRefresh,
        getCurrencySymbol,
        getCurrencyName,
        getSupportedCurrenciesWithNames,
        supportedCurrencies: SUPPORTED_CURRENCIES,
      }}
    >
      {children}
    </CurrencyContext.Provider>
  );
};

export const useCurrency = () => {
  const context = useContext(CurrencyContext);
  if (!context) {
    throw new Error("useCurrency must be used within CurrencyProvider");
  }
  return context;
};