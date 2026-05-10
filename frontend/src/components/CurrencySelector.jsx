// src/components/CurrencySelector.jsx
import React from "react";
import { useCurrency } from "@/context/CurrencyContext";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { ChevronDown, Check } from "lucide-react";

// Bendera kwa sarafu
const currencyFlags = {
  TZS: "🇹🇿",
  KES: "🇰🇪",
  UGX: "🇺🇬",
  RWF: "🇷🇼",
  BIF: "🇧🇮",
  USD: "🇺🇸",
};

export default function CurrencyDropdown() {
  const { currency, changeCurrency, supportedCurrencies } = useCurrency();

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          className="flex items-center space-x-1 px-1.5 py-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition text-xs sm:text-sm"
          title="Badili Sarafu"
        >
          <span className="text-sm">{currencyFlags[currency] || "🏳️"}</span>
          <span className="font-medium text-gray-800 dark:text-gray-100">{currency}</span>
          <ChevronDown className="w-3 h-3 text-gray-500 dark:text-gray-400" />
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded shadow-md w-44 z-50 py-1"
          sideOffset={8}
        >
          {supportedCurrencies.map((c) => (
            <DropdownMenu.Item
              key={c.code}
              onSelect={() => changeCurrency(c.code)}
              className={`flex items-center justify-between space-x-2 px-2 py-1.5 text-sm rounded cursor-pointer
                ${
                  currency === c.code
                    ? "font-semibold text-blue-600 dark:text-blue-300 bg-blue-50 dark:bg-blue-800"
                    : "text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800"
                }`}
            >
              <span className="flex items-center space-x-2">
                <span className="text-sm">{currencyFlags[c.code] || "🏳️"}</span>
                <span className="text-sm">{c.code}</span>
              </span>
              {currency === c.code && <Check className="w-3 h-3 text-blue-500" />}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}