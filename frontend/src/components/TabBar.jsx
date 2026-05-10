// src/components/TabBar.jsx

import React, { useState, useEffect, useRef } from "react";
import { X } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { useTranslation } from "react-i18next";

export default function TabBar() {
  const { t: tCommon, i18n } = useTranslation("common");

  const location = useLocation();
  const navigate = useNavigate();
  const scrollRef = useRef(null);
  const visitedTabs = useRef(new Set());

  const staticMap = {
    "/": "tabs.jamiikazini",
    "/settings": "tabs.settings",
    "/profile": "tabs.profile",
    "/wallet": "tabs.wallet",
    "/edit": "tabs.edit_profile",
    "/home": "tabs.home",
    "/auth/register": "tabs.register",
    "/security/login": "tabs.login",
    "/teaching": "tabs.teaching",
};


  const dynamicMap = {
    "/kiini/dashboard/": "tabs.kiini_dashboard",
    "/businesses/dashboard/": "tabs.business_dashboard",
    "/education/dashboard/": "tabs.education_dashboard",
    "/gov_integration/dashboard/": "tabs.gov_dashboard",
    "/health/dashboard/": "tabs.health_dashboard",
    "/jamiichat/dashboard/": "tabs.chat_dashboard",
    "/jamiiwallet/dashboard/": "tabs.wallet_dashboard",
    "/logistics/dashboard/": "tabs.logistics_dashboard",
    "/payments/dashboard/": "tabs.payments_dashboard",
    "/search/dashboard/": "tabs.search_dashboard",
    "/portfolio/dashboard/": "tabs.portfolio_dashboard",
  };

  const appTabKeys = {
    businesses: {
      overview: "dashboard.overview",
      products: "dashboard.products",
      services: "dashboard.services",
      branches: "dashboard.branches",
      settings: "dashboard.settings",
    },
    kiini: {
      institutions: "dashboard.institutions",
      departments: "dashboard.departments",
      "staff-profiles": "dashboard.staff-profiles",
      "institution-tiers": "dashboard.institution-tiers",
      "institution-types": "dashboard.institution-types",
    },
    // ongeza apps nyingine hapa kama education, health, etc.
  };

  const labelFromPath = (path) => {
    if (staticMap[path]) return tCommon(staticMap[path]);

    const dashboardRoot = Object.entries(dynamicMap).find(([prefix]) => path === prefix);
    if (dashboardRoot) return tCommon(dashboardRoot[1]);

    const deepDashboard = Object.entries(dynamicMap).find(([prefix]) => path.startsWith(prefix));
    if (deepDashboard) {
      const [prefix] = deepDashboard;
      const appName = prefix.split("/")[1];
      const tabSegment = path.split("/").filter(Boolean).at(-1);

      const nsKey = appTabKeys[appName]?.[tabSegment];
      if (nsKey) {
        return i18n.exists(nsKey, { ns: appName })
          ? i18n.t(nsKey, { ns: appName })
          : tCommon(nsKey, { defaultValue: tabSegment });
      }

      return tabSegment?.charAt(0).toUpperCase() + tabSegment?.slice(1);
    }

    const lastSegment = path.split("/").filter(Boolean).at(-1);
    return lastSegment?.charAt(0).toUpperCase() + lastSegment?.slice(1);
  };

  const [tabs, setTabs] = useState([{ path: "/" }]);

  useEffect(() => {
    const path = location.pathname;

    if (path === "/") return;

    if (!visitedTabs.current.has(path)) {
      visitedTabs.current.add(path);
      setTabs((prev) => [...prev, { path }]);
    }
  }, [location.pathname]);

  // ✅ Separate effect for redirect from login page
  useEffect(() => {
    if (
      location.pathname === "/security/login" &&
      localStorage.getItem("access_token")
    ) {
      navigate("/home", { replace: true });
    }
  }, [location.pathname, navigate]);

  // Horizontal scroll with mouse wheel
  useEffect(() => {
    const el = scrollRef.current;
    const handleWheel = (e) => {
      if (e.deltaY !== 0) {
        e.preventDefault();
        el.scrollLeft += e.deltaY;
      }
    };
    el.addEventListener("wheel", handleWheel, { passive: false });
    return () => el.removeEventListener("wheel", handleWheel);
  }, []);

  const closeTab = (pathToClose) => {
    if (pathToClose === "/") return;

    setTabs((prev) => {
      const updated = prev.filter((t) => t.path !== pathToClose);
      if (location.pathname === pathToClose) {
        const fallback = updated.at(-1)?.path || "/";
        navigate(fallback);
      }
      return updated.length > 0 ? updated : [{ path: "/" }];
    });

    visitedTabs.current.delete(pathToClose);
  };

  return (
    <div
      ref={scrollRef}
      className="fixed top-[40px] sm:top-[44px] left-0 right-0 z-40
        flex items-center overflow-x-auto space-x-1.5 px-2 py-1
        bg-white dark:bg-gray-800 backdrop-blur shadow-sm
        border-b border-gray-200 dark:border-gray-700
        scrollbar-hide"
    >
      <AnimatePresence initial={false}>
        {tabs.map((tab) => {
          const isActive = tab.path === location.pathname;
          const isPermanent = tab.path === "/";

          return (
            <motion.div
              key={tab.path}
              layout
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className={`flex items-center space-x-1.5 px-2.5 py-0.5 rounded-md cursor-pointer
                ${
                  isActive
                    ? "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 shadow-[inset_0_-2px_0_0_#1976D2]"
                    : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600"
                }`}
              onClick={() => navigate(tab.path)}
            >
              <span className="text-xs font-normal">{labelFromPath(tab.path)}</span>
              {!isPermanent && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    closeTab(tab.path);
                  }}
                  className="text-gray-500 hover:text-red-500"
                >
                  <X size={12} />
                </button>
              )}
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}