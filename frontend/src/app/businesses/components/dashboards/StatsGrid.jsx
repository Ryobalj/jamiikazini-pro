// src/app/businesses/components/dashboards/StatsGrid.jsx
import React from 'react';

const StatsGrid = ({ stats = [] }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
      {stats.map((stat, index) => (
        <div
          key={index}
          className="bg-white rounded-2xl shadow p-4 flex items-center justify-between hover:shadow-md transition"
        >
          <div>
            <p className="text-sm text-gray-500">{stat.label}</p>
            <h3 className="text-xl font-semibold text-gray-800">{stat.value}</h3>
          </div>
          <div className="text-4xl text-green-600">{stat.icon}</div>
        </div>
      ))}
    </div>
  );
};

export default StatsGrid;