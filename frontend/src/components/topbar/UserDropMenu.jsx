// src/components/topbar/UserDropMenu.jsx

import React, { useRef, useEffect } from "react";
import { LogIn, LogOut, User, Settings, Wallet, Edit, Building2, Shield, HelpCircle } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAppContext } from "@/context/AppContext";
import { logoutUser } from "@/lib/auth";
import { useTranslation } from "react-i18next";

export default function UserDropMenu({ onClose }) {
  const { t } = useTranslation("common");
  const { user, setUser, setUserMenu } = useAppContext();
  const navigate = useNavigate();
  const menuRef = useRef();

  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        onClose?.();
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose]);

  const handleLogout = () => {
    logoutUser({ setUser, setUserMenu, navigate });
    onClose?.();
  };

  const handleNavigate = (path) => {
    navigate(path);
    onClose?.();
  };

  return (
    <div
      ref={menuRef}
      className="absolute right-0 mt-2 w-64 rounded-lg shadow-lg bg-white dark:bg-gray-800 ring-1 ring-gray-200 dark:ring-gray-700 p-3 space-y-3 animate-fade-in z-50"
    >
      {user ? (
        <>
          <div className="font-bold text-gray-900 dark:text-white">
            {user.full_name}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {user.email}
          </div>
          <hr className="border-gray-200 dark:border-gray-600" />

          <Link 
            to="/accounts/profile" 
            onClick={onClose} 
            className="flex items-center gap-3 rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
          >
            <User size={16} className="text-gray-500 dark:text-gray-400" />
            {t("user.profile")}
          </Link>

          <Link 
            to="/accounts/edit" 
            onClick={onClose} 
            className="flex items-center gap-3 rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
          >
            <Edit size={16} className="text-gray-500 dark:text-gray-400" />
            {t("user.edit_profile")}
          </Link>

          {/* ✅ Updated Wallet Link to JamiiWallet */}
          <Link 
            to="/jamiiwallet" 
            onClick={onClose} 
            className="flex items-center gap-3 rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
          >
            <Wallet size={16} className="text-gray-500 dark:text-gray-400" />
            {t("user.wallet")}
          </Link>

          <Link 
            to="/accounts/settings" 
            onClick={onClose} 
            className="flex items-center gap-3 rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
          >
            <Settings size={16} className="text-gray-500 dark:text-gray-400" />
            {t("user.settings")}
          </Link>

          <hr className="border-gray-200 dark:border-gray-600" />

          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full text-left rounded p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
          >
            <LogOut size={16} />
            {t("user.logout")}
          </button>
        </>
      ) : (
        <Link
          to="/security/login/"
          onClick={onClose}
          className="flex items-center gap-3 rounded p-2 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20"
        >
          <LogIn size={16} />
          {t("user.login")}
        </Link>
      )}
    </div>
  );
}