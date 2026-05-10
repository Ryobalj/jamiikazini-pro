// src/app/businesses/components/dashboards/TopProducts.jsx

import React from 'react';
import { TrendingUp } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const TopProducts = ({ products = [] }) => {
  const { t } = useTranslation("businesses");

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow p-4">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-800 dark:text-white">
        <TrendingUp size={18} className="text-green-600" />
        {t('top_products.title')}
      </h3>

      {products.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {t('top_products.empty')}
        </p>
      ) : (
        <ul className="space-y-3">
          {products.map((product, index) => (
            <li key={index} className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-gray-800 dark:text-white">{product.name}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{product.category}</p>
              </div>
              <div className="text-sm font-semibold text-green-700 dark:text-green-400">
                {t('top_products.sold', { count: product.sales })}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TopProducts;