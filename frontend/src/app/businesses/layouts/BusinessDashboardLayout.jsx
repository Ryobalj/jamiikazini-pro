// src/app/businesses/layouts/BusinessDashboardLayout.jsx

import React from "react";
import { Outlet, useParams, NavLink } from "react-router-dom";
import { LayoutDashboard, Package, Wrench, Building2, Settings } from "lucide-react";

export default function BusinessDashboardLayout() {
  const { id } = useParams();
  const base = `/dashboard/${id}`;

  return (
    <div className="flex min-h-screen">
      {/* Main content */}
      <main className="flex-1 p-6 bg-gray-50 dark:bg-gray-900">
        <Outlet />
      </main>
    </div>
  );
}