// src/app/businesses/layouts/BusinessDashboardLayout.jsx

import React from "react";
import { Outlet } from "react-router-dom";

export default function BusinessDashboardLayout() {
  return (
    <div className="flex min-h-screen">
      {/* Main content */}
      <main className="flex-1 p-6 bg-gray-50 dark:bg-gray-900">
        <Outlet />
      </main>
    </div>
  );
}