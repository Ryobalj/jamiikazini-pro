// src/app/businesses/pages/Overview.jsx

import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '@/lib/axios';
import { useCurrency } from '@/context/CurrencyContext';
import {
  Loader2,
  Package,
  CheckCircle,
  XCircle,
  Wrench,
  Building2,
  Receipt,
  Star,
  MessageSquare,
  DollarSign,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  ChevronDown,
  RefreshCw,
  Store,
  Users,
  Clock,
  AlertCircle,
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import RecentReviews from '@/app/businesses/components/dashboards/RecentReviews';
import RevenueChart from '@/app/businesses/components/dashboards/RevenueChart';
import TopProducts from '@/app/businesses/components/dashboards/TopProducts';
import TopServices from '@/app/businesses/components/dashboards/TopServices';

export default function BusinessDashboard() {
  const { id } = useParams();
  const { t } = useTranslation("businesses");
  const { formatCurrency } = useCurrency();
  
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [range, setRange] = useState('30d');
  const [showRangeDropdown, setShowRangeDropdown] = useState(false);

  useEffect(() => {
    fetchStats();
  }, [id, range]);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/businesses/${id}/stats/?range=${range}`);
      setStats(res.data);
      setError('');
    } catch (err) {
      console.error(err);
      setError(t('errors.failedToLoad'));
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchStats();
    setRefreshing(false);
  };

  const rangeOptions = [
    { value: '7d', label: t('ranges.7days') },
    { value: '30d', label: t('ranges.30days') },
    { value: '90d', label: t('ranges.90days') },
    { value: 'all', label: t('ranges.all') },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-4">
        <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
          <AlertCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          {t('errors.title')}
        </h3>
        <p className="text-gray-500 dark:text-gray-400 text-center mb-4">{error}</p>
        <Button onClick={handleRefresh}>
          <RefreshCw className="w-4 h-4 mr-2" />
          {t('try_again')}
        </Button>
      </div>
    );
  }

  if (!stats || !stats.business || !stats.stats) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-4">
        <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
          <Store className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          {t('no_data')}
        </h3>
        <p className="text-gray-500 dark:text-gray-400">{t('empty')}</p>
      </div>
    );
  }

  const s = stats.stats;
  const revenue = s.revenue || {};
  const recentReviews = s.recent_reviews || [];
  
  // Calculate trends (mock - replace with real data)
  const productTrend = s.products_count > 0 ? '+12%' : '0%';
  const revenueTrend = revenue.last_30_days > revenue.last_7_days * 4 ? '+8%' : '-3%';

  const statCards = [
    {
      title: t('stats.products'),
      value: s.products_count,
      icon: Package,
      color: 'blue',
      trend: productTrend,
      trendUp: true,
    },
    {
      title: t('stats.activeProducts'),
      value: s.active_products_count,
      icon: CheckCircle,
      color: 'green',
    },
    {
      title: t('stats.inactiveProducts'),
      value: s.inactive_products_count,
      icon: XCircle,
      color: 'yellow',
    },
    {
      title: t('stats.services'),
      value: s.services_count,
      icon: Wrench,
      color: 'purple',
    },
    {
      title: t('stats.branches'),
      value: s.branches_count,
      icon: Building2,
      color: 'orange',
    },
    {
      title: t('stats.orders'),
      value: s.orders_count,
      icon: Receipt,
      color: 'pink',
    },
    {
      title: t('stats.rating'),
      value: s.average_rating?.toFixed(1) || '0.0',
      icon: Star,
      color: 'yellow',
      suffix: '★',
    },
    {
      title: t('stats.reviews'),
      value: s.reviews_count,
      icon: MessageSquare,
      color: 'indigo',
    },
  ];

  const getColorClasses = (color) => {
    const colors = {
      blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-800',
      green: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 border-green-200 dark:border-green-800',
      yellow: 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800',
      purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 border-purple-200 dark:border-purple-800',
      orange: 'bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400 border-orange-200 dark:border-orange-800',
      pink: 'bg-pink-50 dark:bg-pink-900/20 text-pink-600 dark:text-pink-400 border-pink-200 dark:border-pink-800',
      indigo: 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 border-indigo-200 dark:border-indigo-800',
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
            {stats.business.name}
          </h1>
          <div className="flex items-center gap-3 mt-1">
            <p className="text-gray-500 dark:text-gray-400">
              {t('title')}
            </p>
            {stats.business.is_active ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                <CheckCircle className="w-3 h-3" />
                {t('active')}
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-400">
                <XCircle className="w-3 h-3" />
                {t('inactive')}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Range Selector */}
          <div className="relative">
            <button
              onClick={() => setShowRangeDropdown(!showRangeDropdown)}
              className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <Calendar className="w-4 h-4" />
              {rangeOptions.find(r => r.value === range)?.label || range}
              <ChevronDown className="w-4 h-4" />
            </button>
            
            {showRangeDropdown && (
              <>
                <div 
                  className="fixed inset-0 z-10" 
                  onClick={() => setShowRangeDropdown(false)} 
                />
                <div className="absolute right-0 mt-2 w-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20">
                  {rangeOptions.map(option => (
                    <button
                      key={option.value}
                      onClick={() => {
                        setRange(option.value);
                        setShowRangeDropdown(false);
                      }}
                      className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg ${
                        range === option.value 
                          ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20' 
                          : 'text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        {statCards.map((stat, index) => (
          <Card key={index} className="relative overflow-hidden group hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-lg ${getColorClasses(stat.color)}`}>
                  <stat.icon className="w-5 h-5" />
                </div>
                {stat.trend && (
                  <span className={`inline-flex items-center gap-0.5 text-xs font-medium ${
                    stat.trendUp 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {stat.trendUp ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : (
                      <TrendingDown className="w-3 h-3" />
                    )}
                    {stat.trend}
                  </span>
                )}
              </div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stat.value}
                {stat.suffix && <span className="text-yellow-500 ml-1">{stat.suffix}</span>}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                {stat.title}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Revenue Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Summary */}
        <Card className="lg:col-span-1">
          <CardHeader 
            title={t('revenue.summary')}
            icon={<DollarSign className="w-5 h-5 text-green-600 dark:text-green-400" />}
            divider
          />
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('revenue.last7')}</p>
                  <p className="text-xl font-bold text-gray-900 dark:text-white">
                    {formatCurrency(revenue.last_7_days || 0)}
                  </p>
                </div>
                <ArrowUpRight className="w-5 h-5 text-green-500" />
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('revenue.last30')}</p>
                  <p className="text-xl font-bold text-gray-900 dark:text-white">
                    {formatCurrency(revenue.last_30_days || 0)}
                  </p>
                </div>
                <ArrowUpRight className="w-5 h-5 text-green-500" />
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('revenue.total')}</p>
                  <p className="text-xl font-bold text-gray-900 dark:text-white">
                    {formatCurrency(revenue.all_time || 0)}
                  </p>
                </div>
                <DollarSign className="w-5 h-5 text-blue-500" />
              </div>

              {/* Revenue Trend */}
              <div className="pt-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">{t('revenue.trend')}</span>
                  <span className={`flex items-center gap-1 font-medium ${
                    revenueTrend.startsWith('+') 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {revenueTrend.startsWith('+') ? (
                      <TrendingUp className="w-4 h-4" />
                    ) : (
                      <TrendingDown className="w-4 h-4" />
                    )}
                    {revenueTrend}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Revenue Chart */}
        <Card className="lg:col-span-2">
          <CardHeader 
            title={t('revenue.chart')}
            icon={<TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400" />}
            divider
          />
          <CardContent>
            <RevenueChart data={revenue} />
          </CardContent>
        </Card>
      </div>

      {/* Top Products & Services */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TopProducts businessId={id} />
        <TopServices businessId={id} />
      </div>

      {/* Recent Reviews */}
      <RecentReviews reviews={recentReviews} />
    </div>
  );
}