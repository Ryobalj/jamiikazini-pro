// src/app/jamiiwallet/pages/JamiiWalletPage.jsx

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import {
  Wallet,
  ArrowUp,
  ArrowDown,
  Send,
  History,
  CreditCard,
  Loader2,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Eye,
  EyeOff,
  Smartphone,
  Globe,
  Plus,
  ChevronRight,
  DollarSign,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";
import { useAppContext } from "@/context/AppContext";
import { useCurrency } from "@/context/CurrencyContext";

export default function JamiiWalletPage() {
  const { t } = useTranslation("jamiiwallet");
  const navigate = useNavigate();
  const { user } = useAppContext();
  
  const { 
    currency, 
    formatCurrency, 
    formatCompact,
    changeCurrency, 
    refreshRates,
    getCurrencySymbol,
    getSupportedCurrenciesWithNames,
    loading: ratesLoading,
    lastUpdated,
    autoRefresh,
  } = useCurrency();
  
  const [loading, setLoading] = useState(true);
  const [walletData, setWalletData] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [showBalance, setShowBalance] = useState(true);
  const [activeTab, setActiveTab] = useState("transactions");
  const [refreshing, setRefreshing] = useState(false);
  const [topupAmount, setTopupAmount] = useState("");
  const [showTopupModal, setShowTopupModal] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState("");
  const [monthlyStats, setMonthlyStats] = useState({ income: 0, expenses: 0 });

  useEffect(() => {
    fetchWalletData();
    fetchTransactions();
  }, []);

  useEffect(() => {
    if (transactions.length > 0) {
      calculateMonthlyStats();
    }
  }, [transactions]);

  const fetchWalletData = async () => {
    try {
      const res = await api.get("/jamiiwallet/wallet/");
      setWalletData(res.data);
    } catch (error) {
      console.error("Failed to fetch wallet:", error);
      toast.error(t("errors.failed_to_load_wallet"));
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async () => {
    try {
      const res = await api.get("/jamiiwallet/transactions/");
      const txList = Array.isArray(res.data) ? res.data : res.data.results || [];
      setTransactions(txList);
    } catch (error) {
      console.error("Failed to fetch transactions:", error);
      setTransactions([]);
    }
  };

  const calculateMonthlyStats = () => {
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    
    let income = 0;
    let expenses = 0;
    
    transactions.forEach(tx => {
      const txDate = new Date(tx.created_at);
      if (txDate >= startOfMonth && tx.status === "COMPLETED") {
        const amount = parseFloat(tx.amount);
        if (tx.transaction_type === "TOP_UP" || tx.transaction_type === "REFUND") {
          income += amount;
        } else {
          expenses += amount;
        }
      }
    });
    
    setMonthlyStats({ income, expenses });
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchWalletData(), fetchTransactions()]);
    setRefreshing(false);
    toast.success(t("refreshed"));
  };

  const handleTopup = async () => {
    if (!topupAmount || parseFloat(topupAmount) <= 0) {
      toast.error(t("invalid_amount"));
      return;
    }

    try {
      await api.post("/jamiiwallet/topup/", {
        amount: parseFloat(topupAmount),
        channel: selectedChannel || "pawapay",
      });
      
      toast.success(t("topup_initiated"));
      setShowTopupModal(false);
      setTopupAmount("");
      setSelectedChannel("");
      
      setTimeout(() => {
        fetchWalletData();
        fetchTransactions();
      }, 2000);
    } catch (error) {
      console.error("Topup failed:", error);
      toast.error(t("topup_failed"));
    }
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case "TOP_UP": return <ArrowUp className="w-4 h-4 text-green-500" />;
      case "WITHDRAWAL": return <ArrowDown className="w-4 h-4 text-red-500" />;
      case "TRANSFER": return <Send className="w-4 h-4 text-blue-500" />;
      case "PAYMENT": return <CreditCard className="w-4 h-4 text-orange-500" />;
      case "REFUND": return <RefreshCw className="w-4 h-4 text-purple-500" />;
      default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "COMPLETED": return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "PENDING": return <Clock className="w-4 h-4 text-yellow-500" />;
      case "FAILED": return <XCircle className="w-4 h-4 text-red-500" />;
      case "REVERSED": return <AlertCircle className="w-4 h-4 text-orange-500" />;
      default: return null;
    }
  };

  const getTransactionLabel = (type) => {
    return t(`transaction_types.${type.toLowerCase()}`) || type;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 dark:from-purple-900 dark:to-indigo-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center">
                <Wallet className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold">{t("title")}</h1>
                <p className="text-white/80 text-sm mt-1">
                  {user?.full_name || user?.email}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <select
                value={currency}
                onChange={(e) => changeCurrency(e.target.value)}
                className="bg-white/20 text-white border-0 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-white/50"
              >
                {getSupportedCurrenciesWithNames().map((c) => (
                  <option key={c.code} value={c.code} className="text-gray-900">
                    {c.code} - {c.name}
                  </option>
                ))}
              </select>
              
              <button
                onClick={refreshRates}
                disabled={ratesLoading}
                className="p-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors disabled:opacity-50"
                title={lastUpdated 
                  ? `${t("currencies.last_updated", { ns: "translation" })}: ${lastUpdated.toLocaleTimeString()}` 
                  : t("currencies.refresh_rates", { ns: "translation" })
                }
              >
                <RefreshCw className={`w-4 h-4 ${ratesLoading ? "animate-spin" : ""}`} />
              </button>
              
              <Button
                variant="secondary"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
                className="bg-white/20 hover:bg-white/30 text-white border-0"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
                {refreshing ? t("refreshing") : t("refresh")}
              </Button>
            </div>
          </div>
          
          {lastUpdated && (
            <p className="text-white/60 text-xs mt-2">
              {t("currencies.last_updated", { ns: "translation" })}: {lastUpdated.toLocaleTimeString()}
              {autoRefresh && ` (${t("currencies.auto_refresh", { ns: "translation" })})`}
            </p>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-green-500/10 rounded-full -mr-16 -mt-16" />
            <CardContent className="pt-6 relative">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t("available_balance")}
                </p>
                <button onClick={() => setShowBalance(!showBalance)} className="text-gray-400 hover:text-gray-600">
                  {showBalance ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
                {showBalance ? formatCurrency(walletData?.balance || 0) : "••••••"}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {getCurrencySymbol()} {currency}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                {t("this_month")}
              </p>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-green-500" />
                  <div>
                    <p className="text-xs text-gray-500">{t("income")}</p>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {showBalance ? formatCompact(monthlyStats.income) : "••••"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingDown className="w-5 h-5 text-red-500" />
                  <div>
                    <p className="text-xs text-gray-500">{t("expenses")}</p>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {showBalance ? formatCompact(monthlyStats.expenses) : "••••"}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                {t("quick_actions")}
              </p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  className="flex-1 bg-purple-600 hover:bg-purple-700"
                  onClick={() => setShowTopupModal(true)}
                >
                  <Plus className="w-4 h-4 mr-1" />
                  {t("topup")}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1"
                  onClick={() => navigate("/jamiiwallet/send")}
                >
                  <Send className="w-4 h-4 mr-1" />
                  {t("send")}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1"
                  onClick={() => navigate("/jamiiwallet/request")}
                >
                  <ArrowDown className="w-4 h-4 mr-1" />
                  {t("request")}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex gap-4 border-b border-gray-200 dark:border-gray-700">
          {["transactions", "cards", "beneficiaries"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-3 px-2 text-sm font-medium transition-colors relative ${
                activeTab === tab
                  ? "text-purple-600 dark:text-purple-400"
                  : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
              }`}
            >
              {t(`tabs.${tab}`)}
              {activeTab === tab && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-600 dark:bg-purple-400" />
              )}
            </button>
          ))}
        </div>

        {activeTab === "transactions" && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {t("recent_transactions")}
              </h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/jamiiwallet/transactions")}
              >
                {t("view_all")}
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>

            {transactions.length > 0 ? (
              <Card>
                <CardContent className="p-0">
                  <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {transactions.slice(0, 10).map((tx) => (
                      <div
                        key={tx.id}
                        className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
                        onClick={() => navigate(`/jamiiwallet/transactions/${tx.id}`)}
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                            {getTransactionIcon(tx.transaction_type)}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-gray-100">
                              {getTransactionLabel(tx.transaction_type)}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {new Date(tx.created_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`font-semibold ${
                            tx.transaction_type === "TOP_UP" || tx.transaction_type === "REFUND"
                              ? "text-green-600 dark:text-green-400"
                              : "text-red-600 dark:text-red-400"
                          }`}>
                            {tx.transaction_type === "TOP_UP" || tx.transaction_type === "REFUND" ? "+" : "-"}
                            {formatCurrency(tx.amount)}
                          </p>
                          <div className="flex items-center justify-end gap-1 mt-1">
                            {getStatusIcon(tx.status)}
                            <span className="text-xs text-gray-500">
                              {t(`status.${tx.status.toLowerCase()}`)}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="text-center py-8">
                  <History className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-500 dark:text-gray-400">
                    {t("no_transactions")}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {activeTab === "cards" && (
          <div className="mt-6">
            <Card>
              <CardHeader title={t("payment_methods")} icon={<CreditCard className="w-5 h-5" />} divider />
              <CardContent className="text-center py-8">
                <CreditCard className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  {t("no_cards")}
                </p>
                <Button onClick={() => navigate("/jamiiwallet/add-card")}>
                  <Plus className="w-4 h-4 mr-2" />
                  {t("add_card")}
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "beneficiaries" && (
          <div className="mt-6">
            <Card>
              <CardHeader title={t("saved_beneficiaries")} icon={<Users className="w-5 h-5" />} divider />
              <CardContent className="text-center py-8">
                <Users className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  {t("no_beneficiaries")}
                </p>
                <Button onClick={() => navigate("/jamiiwallet/add-beneficiary")}>
                  <Plus className="w-4 h-4 mr-2" />
                  {t("add_beneficiary")}
                </Button>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {showTopupModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <Card className="max-w-md w-full">
            <CardHeader title={t("topup_wallet")} icon={<Wallet className="w-5 h-5" />} divider />
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t("amount")} ({currency})
                  </label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="number"
                      value={topupAmount}
                      onChange={(e) => setTopupAmount(e.target.value)}
                      placeholder="0.00"
                      className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                  {topupAmount && (
                    <p className="text-xs text-gray-500 mt-1">
                      ≈ {formatCurrency(topupAmount)}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t("payment_channel")}
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { id: "pawapay", name: "PawaPay", icon: Smartphone },
                      { id: "flutterwave", name: "Flutterwave", icon: Globe },
                      { id: "stripe", name: "Stripe", icon: CreditCard },
                    ].map((channel) => (
                      <button
                        key={channel.id}
                        onClick={() => setSelectedChannel(channel.id)}
                        className={`p-3 rounded-lg border text-center transition-all ${
                          selectedChannel === channel.id
                            ? "border-purple-500 bg-purple-50 dark:bg-purple-900/30"
                            : "border-gray-200 dark:border-gray-700 hover:border-gray-300"
                        }`}
                      >
                        <channel.icon className="w-5 h-5 mx-auto mb-1" />
                        <span className="text-xs">{channel.name}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 pt-4">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => {
                      setShowTopupModal(false);
                      setTopupAmount("");
                      setSelectedChannel("");
                    }}
                  >
                    {t("cancel")}
                  </Button>
                  <Button className="flex-1 bg-purple-600 hover:bg-purple-700" onClick={handleTopup}>
                    {t("confirm_topup")}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

function Users({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}