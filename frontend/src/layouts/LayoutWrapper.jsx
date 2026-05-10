// src/layouts/LayoutWrapper.jsx
import React from "react";
import { Outlet } from "react-router-dom";
import MainLayout from "./MainLayout";
import BusinessDashboardLayout from "@/app/businesses/layouts/BusinessDashboardLayout";

const layoutMap = {
  main: MainLayout,
  business: BusinessDashboardLayout,
};

export default function LayoutWrapper({ layout = "main" }) {
  const LayoutComponent = layoutMap[layout] || MainLayout;

  return (
    <MainLayout layout={layout}>
      {layout === "business" ? (
        <BusinessDashboardLayout>
          <Outlet />
        </BusinessDashboardLayout>
      ) : (
        <Outlet />
      )}
    </MainLayout>
  );
}