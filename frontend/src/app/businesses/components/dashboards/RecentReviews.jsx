// src/app/businesses/components/dashboards/RecentReviews.jsx


import React from 'react';
import { FaStar } from 'react-icons/fa'; // ✅ react-icons
import { format } from 'date-fns';
import { useTranslation } from 'react-i18next';

const RecentReviews = ({ reviews = [] }) => {
  const { t } = useTranslation("businesses");

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow p-4">
      <h3 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">
        {t('recent_reviews.title')}
      </h3>

      {reviews.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {t('recent_reviews.empty')}
        </p>
      ) : (
        <ul className="space-y-4">
          {reviews.map((review, index) => (
            <li
              key={index}
              className="border-b pb-3 last:border-none border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center justify-between">
                <div className="font-medium text-sm text-gray-800 dark:text-white">
                  {review.user}
                </div>
                <div className="flex space-x-1 text-yellow-500">
                  {[...Array(5)].map((_, i) => (
                    <FaStar
                      key={i}
                      size={14}
                      className={i < review.rating ? 'text-yellow-400' : 'text-gray-300 dark:text-gray-600'}
                    />
                  ))}
                </div>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{review.comment}</p>
              {review.created_at && (
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  {format(new Date(review.created_at), 'dd MMM yyyy')}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default RecentReviews;