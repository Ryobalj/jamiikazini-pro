// src/components/dashboards/DashboardLayout.jsx
import React from 'react';

const DashboardLayout = ({ title, actions, children }) => {
  return (
    <section className="p-4 sm:p-6 md:p-8">
      <div className="mb-6 flex items-center justify-between flex-wrap gap-4">
        <h2 className="text-2xl font-bold text-gray-800">{title}</h2>
        {actions && <div className="flex gap-2">{actions}</div>}
      </div>
      <div className="space-y-6">{children}</div>
    </section>
  );
};

export default DashboardLayout;