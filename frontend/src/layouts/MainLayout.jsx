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
  const fixedBarRef = useRef();
  // The fixed TopBar+TabBar's real height, measured live instead of
  // guessed via a hardcoded pt-[80px]/[88px] - a guess that can drift out
  // of sync (font rendering, zoom, content changes) and let page content
  // render partly underneath the fixed bar. Starts at the old guessed
  // value so there's no flash of 0 padding before the first measurement.
  const [fixedBarHeight, setFixedBarHeight] = useState(88);

  useEffect(() => {
    // TopBar and TabBar are each independently position:fixed, so their
    // shared wrapper div collapses to 0 height (out-of-flow children never
    // contribute to a parent's auto height) - measuring the wrapper itself
    // would always read 0. TabBar is the lower of the two, so its own
    // bottom edge (in viewport coordinates, which already accounts for
    // TopBar's height via TabBar's own "top" offset) is the real total to
    // reserve. It's the wrapper's last DOM child regardless of the fixed
    // positioning, so no ref needs to be threaded through TabBar itself.
    const tabBarEl = fixedBarRef.current?.lastElementChild;
    if (!tabBarEl) return;
    const measure = () => setFixedBarHeight(tabBarEl.getBoundingClientRect().bottom);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(tabBarEl);
    window.addEventListener("resize", measure);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, []);

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
        <div ref={fixedBarRef} className="fixed top-0 left-0 right-0 z-50">
          <TopBar onLogoClick={handleLogoClick} ref={topBarRef} />
          <TabBar layout={layout} />
        </div>

        {/* Main Layout */}
        <div
          className="flex flex-1 overflow-x-hidden"
          style={{ paddingTop: fixedBarHeight }}
          ref={layoutRef}
        >
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