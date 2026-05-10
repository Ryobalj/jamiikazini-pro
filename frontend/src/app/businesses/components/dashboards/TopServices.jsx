// src/app/businesses/components/dashboards/TopServices.jsx

import React from 'react';
import { Star } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const TopServices = ({ services = [] }) => {
  const { t } = useTranslation("businesses");

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow p-4">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-800 dark:text-white">
        <Star size={18} className="text-orange-500" />
        {t('top_services.title')}
      </h3>

      {services.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {t('top_services.empty')}
        </p>
      ) : (
        <ul className="space-y-3">
          {services.map((service, index) => (
            <li key={index} className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-gray-800 dark:text-white">{service.name}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{service.category}</p>
              </div>
              <div className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                {t('top_services.used', { count: service.usage })}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TopServices;