// src/components/LanguageSwitcher.jsx

import React, { useEffect, useState } from "react";
import { Menu } from "@headlessui/react";
import { Globe } from "lucide-react";
import { useTranslation } from "react-i18next";

const languages = [
  { code: "sw", name: "Kiswahili", flag: "🇹🇿" },
  { code: "en", name: "English", flag: "🇬🇧" },
  { code: "fr", name: "Français", flag: "🇫🇷" },
  { code: "rw", name: "Kinyarwanda", flag: "🇷🇼" },
  { code: "lg", name: "Luganda", flag: "🇺🇬" },
  { code: "ha", name: "Hausa", flag: "🇳🇬" },
  { code: "af", name: "Afrikaans", flag: "🇿🇦" },
  { code: "zh", name: "中文", flag: "🇨🇳" },
  { code: "ar", name: "العربية", flag: "🇸🇦" },
  { code: "hi", name: "हिन्दी", flag: "🇮🇳" },
  { code: "ru", name: "Русский", flag: "🇷🇺" },
  { code: "ko", name: "한국어", flag: "🇰🇷" },
  { code: "ja", name: "日本語", flag: "🇯🇵" },
  { code: "es", name: "Español", flag: "🇪🇸" },
  { code: "pt", name: "Português", flag: "🇧🇷" },
];

export default function LanguageSwitcher({ onClose }) {
  const { i18n } = useTranslation();
  const [selectedLang, setSelectedLang] = useState(
    languages.find((lang) => lang.code === i18n.language) || languages[0]
  );

  useEffect(() => {
    const currentLang = languages.find((lang) => lang.code === i18n.language);
    if (currentLang) {
      setSelectedLang(currentLang);
    }
  }, [i18n.language]);

  const handleChangeLanguage = (lang) => {
    i18n.changeLanguage(lang.code);
    onClose?.(); // Funika dropdown baada ya kuchagua
  };

  return (
    <div className="w-48 origin-top-right divide-y divide-gray-200 dark:divide-gray-700 rounded-md bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none py-1 max-h-80 overflow-y-auto">
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => handleChangeLanguage(lang)}
          className="flex items-center w-full px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <span className="mr-2">{lang.flag}</span>
          {lang.name}
        </button>
      ))}
    </div>
  );
}