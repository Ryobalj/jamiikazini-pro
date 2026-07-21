// src/components/Sidebar.jsx

import React, { useState, useEffect, useRef } from "react";
import { ChevronRight, LogIn, UserPlus, X, BookOpen } from "lucide-react";
import * as LucideIcons from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAppContext } from "@/context/AppContext";
import { useTranslation } from "react-i18next";

export default function Sidebar({ isOpen = false, onClose }) {
  const { userMenu } = useAppContext();
  const [activeMenu, setActiveMenu] = useState(null);
  const sidebarRef = useRef();
  const panelRef = useRef();
  const navigate = useNavigate();
  const location = useLocation();

  const isGuest = !Array.isArray(userMenu) || userMenu.length === 0;
  const levelColors = ["#1976D2", "#F57C00", "#424242", "#2E7D32", "#8E24AA", "#C62828", "#00838F", "#6D4C41"];

  // 🧠 Load common namespaces only once (single hook call - React rules of hooks)
  const nsList = ["dashboard", "businesses", "kiini", "common"];
  const { t } = useTranslation(nsList);

  const translateLabel = (key, fallback) => {
    for (const ns of nsList) {
      const translated = t(key, { ns, defaultValue: undefined });
      if (translated && translated !== key) return translated;
    }
    return fallback || key;
  };

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        !sidebarRef.current?.contains(e.target) &&
        !panelRef.current?.contains(e.target)
      ) {
        setActiveMenu(null);
        onClose?.();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onClose]);

  const handleMainClick = (item) => {
    if (item.sub?.length) {
      setActiveMenu(item.app);
    } else if (item.url?.startsWith("/businesses/register")) {
      setActiveMenu(null);
      navigate(item.url, {
        state: {
          modal: true,
          backgroundLocation: location,
        },
      });
    } else {
      setActiveMenu(null);
      navigate(item.url);
    }
  };

  const renderMenuButton = (item, level = 0) => {
    const IconComponent = LucideIcons[item.icon] || 
                         LucideIcons[item.icon?.charAt(0).toUpperCase() + item.icon?.slice(1)] || 
                         LucideIcons.LayoutDashboard;
    const isActive = activeMenu === item.app;
    const color = levelColors[level % levelColors.length];
    const label = translateLabel(item.i18nKey || item.label, item.label);

    return (
      <button
        key={item.app}
        aria-label={label}
        title={label}
        onClick={() => handleMainClick(item)}
        className="flex items-center justify-center w-11 h-11 sm:w-12 sm:h-12 rounded-xl mx-auto transition-all duration-300 hover:scale-105 relative"
        style={{
          backgroundColor: isActive ? `${color}15` : "transparent",
          color: isActive ? color : "#6B7280",
        }}
      >
        {/* Left border indicator */}
        <div 
          className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full transition-all duration-300"
          style={{
            backgroundColor: isActive ? color : "transparent",
          }}
        />
        <IconComponent size={20} className="mx-auto" />
      </button>
    );
  };

  const renderSubMenu = (item) => (
    <nav className="space-y-0.5">
      {item.sub.map((sub, idx) => {
        const SubIcon = LucideIcons[sub.icon] || 
                       LucideIcons[sub.icon?.charAt(0).toUpperCase() + sub.icon?.slice(1)] || 
                       LucideIcons.Circle;
        const label = translateLabel(sub.i18nKey || sub.label, sub.label);
        const color = levelColors[idx % levelColors.length];

        return (
          <button
            key={sub.url}
            onClick={() => {
              setActiveMenu(null);
              navigate(sub.url);
            }}
            className="flex items-center space-x-3 px-3 py-2.5 rounded-lg w-full text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors relative group"
          >
            {/* Colored indicator bar */}
            <div 
              className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full transition-all duration-300 group-hover:h-8"
              style={{ backgroundColor: color }}
            />
            <SubIcon size={16} className="text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-200" />
            <span className="text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-200">{label}</span>
          </button>
        );
      })}
    </nav>
  );

  return (
    <>
      {/* Main Sidebar */}
      <aside
        ref={sidebarRef}
        className={`fixed top-[60px] left-0 h-[calc(100vh-60px)] w-12 sm:w-14 z-40 bg-white dark:bg-gray-800 shadow-lg
        flex flex-col justify-start overflow-y-auto transition-transform duration-300
        ${isOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        <nav className="flex flex-col space-y-2 p-2">
          {isGuest ? (
            <button
              aria-label={t("auth.login", { ns: "common", defaultValue: "Login" })}
              title={t("auth.login", { ns: "common", defaultValue: "Login" })}
              onClick={() => setActiveMenu("auth")}
              className="flex items-center justify-center w-11 h-11 sm:w-12 sm:h-12 rounded-xl mx-auto hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-300 text-gray-500 hover:text-blue-600"
            >
              <LogIn size={20} />
            </button>
          ) : (
            userMenu.map((item, idx) => renderMenuButton(item, idx))
          )}

          {/* Always visible, whether logged in or a guest */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-2 mt-1">
            <button
              aria-label={t("help.sidebar_label", { ns: "common", defaultValue: "User Manual" })}
              title={t("help.sidebar_label", { ns: "common", defaultValue: "User Manual" })}
              onClick={() => {
                setActiveMenu(null);
                navigate("/help");
              }}
              className="flex items-center justify-center w-11 h-11 sm:w-12 sm:h-12 rounded-xl mx-auto transition-all duration-300 hover:scale-105 relative"
              style={{
                backgroundColor: location.pathname === "/help" ? "#C08A2E15" : "transparent",
                color: location.pathname === "/help" ? "#C08A2E" : "#6B7280",
              }}
            >
              <div
                className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full transition-all duration-300"
                style={{ backgroundColor: location.pathname === "/help" ? "#C08A2E" : "transparent" }}
              />
              <BookOpen size={20} className="mx-auto" />
            </button>
          </div>
        </nav>
      </aside>

      {/* Submenu Panel */}
      <div
        ref={panelRef}
        className={`fixed top-[66px] left-12 sm:left-14 h-[calc(100vh-66px)] w-64 z-30
        bg-white dark:bg-gray-900 shadow-xl rounded-r-lg py-3 overflow-y-auto
        transition-all duration-300
        ${activeMenu ? "translate-x-0 opacity-100 pointer-events-auto" : "-translate-x-full opacity-0 pointer-events-none"}`}
      >
        <div className="flex justify-end px-3 mb-2 sm:hidden">
          <button onClick={onClose} className="text-gray-500 hover:text-red-500">
            <X size={16} />
          </button>
        </div>

        <div className="px-3">
          {activeMenu === "auth" && (
            <>
              <header className="mb-3 flex items-center space-x-2">
                <ChevronRight className="text-blue-500" size={16} />
                <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {t("auth.authenticate", { ns: "common", defaultValue: "Authenticate" })}
                </h2>
              </header>
              <nav className="space-y-0.5">
                {[
                  { label: "auth.login", icon: LogIn, path: "/security/login/", level: 0 },
                  { label: "auth.register", icon: UserPlus, path: "/auth/register/", level: 1 },
                ].map((item) => (
                  <button
                    key={item.label}
                    onClick={() => navigate(item.path)}
                    className="flex items-center space-x-3 px-3 py-2.5 rounded-lg w-full text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors relative group"
                  >
                    <div 
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full transition-all duration-300 group-hover:h-8"
                      style={{ backgroundColor: levelColors[item.level % levelColors.length] }}
                    />
                    <item.icon size={16} className="text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-200" />
                    <span className="text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-200">
                      {t(item.label, { ns: "common", defaultValue: item.label })}
                    </span>
                  </button>
                ))}
              </nav>
            </>
          )}

          {activeMenu && activeMenu !== "auth" && (
            <>
              <header className="mb-3 flex items-center space-x-2">
                <ChevronRight className="text-blue-500" size={16} />
                <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {translateLabel(
                    userMenu.find((m) => m.app === activeMenu)?.i18nKey ||
                      userMenu.find((m) => m.app === activeMenu)?.label,
                    userMenu.find((m) => m.app === activeMenu)?.label
                  )}
                </h2>
              </header>
              {renderSubMenu(userMenu.find((m) => m.app === activeMenu))}
            </>
          )}
        </div>
      </div>
    </>
  );
}