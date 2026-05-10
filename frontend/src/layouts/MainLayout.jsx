// src/layouts/MainLayout.jsx

import React, { useState, useRef, useEffect } from "react";
import { useLocation, useNavigate, Outlet } from "react-router-dom";
import TopBar from "@/components/TopBar";
import Sidebar from "@/components/Sidebar";
import TabBar from "@/components/TabBar";

export default function MainLayout({ children, layout = "default", hideSidebar = false }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(!hideSidebar);
  const layoutRef = useRef();
  const topBarRef = useRef();

  const isModal = location.state?.modal;
  const backgroundLocation = location.state?.backgroundLocation || null;

  useEffect(() => {
    if (!hideSidebar) {
      setSidebarOpen(true);
    }
  }, [location.pathname, hideSidebar]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (sidebarOpen && layoutRef.current && !layoutRef.current.contains(e.target)) {
        setSidebarOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [sidebarOpen]);

  const handleLogoClick = () => {
    if (topBarRef.current?.closeAllDropdowns) {
      topBarRef.current.closeAllDropdowns();
    }
    setSidebarOpen((prev) => !prev);
  };

  const handleModalClose = () => {
    if (backgroundLocation) {
      navigate(backgroundLocation.pathname + (backgroundLocation.search || ""), { replace: true });
    } else {
      navigate("/", { replace: true });
    }
  };

  return (
    <>
      <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100 relative">
        {/* Fixed TopBar + TabBar */}
        <div className="fixed top-0 left-0 right-0 z-50">
          <TopBar onLogoClick={handleLogoClick} ref={topBarRef} />
          <TabBar layout={layout} />
        </div>

        {/* Main Layout */}
        <div className="flex flex-1 overflow-x-hidden pt-[80px] sm:pt-[88px]" ref={layoutRef}>
          {!hideSidebar && (
            <div className="relative z-40">
              <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} layout={layout} />
            </div>
          )}
          <div className="flex flex-col flex-1 overflow-x-hidden">
            <main className="flex-1 overflow-y-auto px-4 py-4 sm:px-6 lg:px-8">
              <div className="w-full max-w-6xl mx-auto">
                {/* ✅ Hapa: kama children ipo, render hiyo; vinginevyo render Outlet */}
                {!isModal && (children || <Outlet />)}
              </div>
            </main>
          </div>
        </div>
      </div>

      {/* Modal Overlay */}
      {isModal && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg max-w-3xl w-full max-h-[90vh] overflow-auto relative">
            <button
              onClick={handleModalClose}
              className="absolute top-3 right-3 text-gray-600 dark:text-gray-300 hover:text-red-600"
              aria-label="Close modal"
            >
              ✕
            </button>
            {children || <Outlet />}
          </div>
        </div>
      )}
    </>
  );
}