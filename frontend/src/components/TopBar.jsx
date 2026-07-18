// src/components/TopBar.jsx

import React, {
  useState,
  useRef,
  useEffect,
  forwardRef,
  useImperativeHandle,
  useCallback,
} from "react";
import {
  Search, Bell, ShoppingCart, Home,
  ArrowLeft, ArrowRight, User, Globe, Share2
} from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import ThemeSwitch from "./ThemeSwitch";
import { useAppContext } from "@/context/AppContext";
import { useCart } from "@/context/CartContext";
import CartMenu from "./topbar/CartMenu";
import UserDropMenu from "./topbar/UserDropMenu";
import NotificationMenu from "./topbar/NotificationMenu";
import SearchMenu from "./topbar/SearchMenu";
import LanguageSwitcher from "./LanguageSwitcher";
import CurrencyDropdown from "@/components/CurrencySelector"; // ✅ Umeongeza hii

const TopBar = forwardRef(function TopBar(
  {
    cartItems: cartItemsProp,
    onSearch,
    onLogoClick,
  },
  ref
) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, unreadCount } = useAppContext();
  const { items: cartContextItems } = useCart() || {};
  const cartItems = cartItemsProp ?? cartContextItems ?? [];
  const { t } = useTranslation();

  const [activeDropdown, setActiveDropdown] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  const containerRef = useRef(null);

  const closeAllDropdowns = useCallback(() => setActiveDropdown(null), []);
  useImperativeHandle(ref, () => ({ closeAllDropdowns }));

  useEffect(() => closeAllDropdowns(), [location.pathname]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (!containerRef.current?.contains(e.target)) {
        closeAllDropdowns();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [closeAllDropdowns]);

  const toggleDropdown = (type) => (e) => {
    e.stopPropagation();
    setActiveDropdown((prev) => (prev === type ? null : type));
  };

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
    onSearch?.(e.target.value);
  };

  return (
    <div
      ref={containerRef}
      className="fixed top-0 left-0 right-0 z-50 h-10 sm:h-11 bg-white dark:bg-gray-800 shadow flex items-center justify-between px-2 sm:px-3"
    >
      {/* Logo */}
      <div className="flex items-center">
        <button
          onClick={(e) => {
            e.stopPropagation();
            closeAllDropdowns();
            onLogoClick?.();
          }}
          className="focus:outline-none hover:scale-105 transition-transform"
        >
          <img
            src="/logo.png"
            alt="Jamiikazini"
            className="w-6 h-6 sm:w-7 sm:h-7 object-contain rounded-full animate-glowPulse"
          />
        </button>
      </div>

      {/* Action Icons */}
      <div className="flex items-center overflow-x-auto scrollbar-hide pr-1 max-w-full">
        <div className="flex items-center space-x-1 sm:space-x-1.5 min-w-max">
          <button onClick={() => window.history.back()} className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700" title={t("topbar.back")}>
            <ArrowLeft size={14} />
          </button>
          <button onClick={() => window.history.forward()} className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700" title={t("topbar.forward")}>
            <ArrowRight size={14} />
          </button>
          {user && (
            <>
              <button onClick={() => navigate("/home")} className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700" title={t("topbar.dashboard")}>
                <Home size={14} />
              </button>
              <button onClick={() => navigate("/invite")} className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700" title={t("topbar.invite")}>
                <Share2 size={14} />
              </button>
            </>
          )}
          <button onClick={toggleDropdown("search")} className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700" title={t("topbar.search")}>
            <Search size={14} />
          </button>
          <button onClick={toggleDropdown("notifications")} className="relative p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700" title={t("topbar.notifications")}>
            <Bell size={14} />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-3 h-3 text-[9px] flex items-center justify-center bg-red-500 text-white rounded-full">
                {unreadCount}
              </span>
            )}
          </button>
          <button onClick={toggleDropdown("cart")} className="relative p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700" title={t("topbar.cart")}>
            <ShoppingCart size={14} />
            {cartItems.length > 0 && (
              <span className="absolute -top-1 -right-1 w-3 h-3 text-[9px] flex items-center justify-center bg-orange-500 text-white rounded-full">
                {cartItems.length}
              </span>
            )}
          </button>
          <button onClick={toggleDropdown("user")} className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700" title={t("user.menu")}>
            <User size={14} />
          </button>
          <button onClick={toggleDropdown("language")} className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700" title={t("topbar.language")}>
            <Globe size={14} />
          </button>

          <CurrencyDropdown /> {/* ✅ Hii hapa */}
          <ThemeSwitch />
        </div>
      </div>

      {/* Dropdowns */}
      {activeDropdown === "search" && (
        <div className="absolute right-0 top-full mt-1 z-50">
          <SearchMenu
            searchQuery={searchQuery}
            onChange={handleSearchChange}
            onClose={closeAllDropdowns}
          />
        </div>
      )}
      {activeDropdown === "notifications" && (
        <div className="absolute right-0 top-full mt-1 z-50">
          <NotificationMenu onClose={closeAllDropdowns} />
        </div>
      )}
      {activeDropdown === "cart" && (
        <div className="absolute right-0 top-full mt-1 z-50">
          <CartMenu cartItems={cartItems} onClose={closeAllDropdowns} />
        </div>
      )}
      {activeDropdown === "user" && (
        <div className="absolute right-0 top-full mt-1 z-50">
          <UserDropMenu onClose={closeAllDropdowns} />
        </div>
      )}
      {activeDropdown === "language" && (
        <div className="absolute right-0 top-full mt-1 z-50">
          <LanguageSwitcher onClose={closeAllDropdowns} />
        </div>
      )}
    </div>
  );
});

export default TopBar;