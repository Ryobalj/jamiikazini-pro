// src/app/businesses/components/dashboards/RevenueChart.jsx

import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  XAxis,
  YAxis,
  Tooltip,
  Bar,
  CartesianGrid,
} from 'recharts';
import { useTranslation } from 'react-i18next';

const RevenueChart = ({ data }) => {
  const { t } = useTranslation("businesses");

  const safeData = Array.isArray(data) ? data : [];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-700 p-2 rounded shadow text-sm text-gray-900 dark:text-white">
          <p>{label}</p>
          <p>
            {t('revenue.amount')}: <strong>${payload[0].value}</strong>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow p-4">
      <h3 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">
        {t('revenue.chart')}
      </h3>

      {safeData.length > 0 ? (
        <ResponsiveContainer width="100%" height={250}>
          <BarChart
            data={safeData}
            margin={{ top: 10, right: 20, bottom: 10, left: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" />
            <YAxis />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="value" fill="#2E7D32" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <p className="text-gray-500 text-sm dark:text-gray-400">
          {t('revenue.no_data')}
        </p>
      )}
    </div>
  );
};

export default RevenueChart;