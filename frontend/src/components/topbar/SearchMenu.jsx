// src/components/topbar/SearchMenu.jsx

import React, { useRef, useEffect } from "react";
import { Search } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function SearchMenu({ searchQuery, onChange, onClose }) {
  const { t } = useTranslation();
  const menuRef = useRef();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        onClose?.(); // Optional chaining in case onClose not passed
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onClose]);

  return (
    <div
      ref={menuRef}
      className="absolute right-0 mt-2 w-80 rounded-lg shadow-lg bg-white dark:bg-gray-800 ring-1 ring-gray-200 dark:ring-gray-700 p-3 space-y-3 animate-fade-in z-50"
    >
      <div className="relative">
        <input
          type="text"
          value={searchQuery}
          onChange={onChange}
          placeholder={t("search.placeholder")}
          className="w-full rounded pl-9 pr-3 py-2 border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
        />
        <Search
          className="absolute left-3 top-2.5 text-gray-400 dark:text-gray-300"
          size={16}
        />
      </div>
      <div className="text-sm text-gray-500 dark:text-gray-400">
        {t("search.empty")}
      </div>
    </div>
  );
}