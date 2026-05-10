import React, { useState, useEffect } from "react";
import { Sun, Moon, Monitor } from "lucide-react";

export default function ThemeSwitch() {
  const getSystemPreference = () =>
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";

  const getInitialTheme = () => {
    const saved = localStorage.getItem("theme");
    return saved === "light" || saved === "dark" ? saved : "system";
  };

  const [theme, setTheme] = useState(getInitialTheme);

  // Listen to system theme change
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      if (theme === "system") {
        applyTheme("system");
      }
    };
    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [theme]);

  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const applyTheme = (theme) => {
    const root = document.documentElement;
    if (theme === "light") {
      root.classList.remove("dark");
    } else if (theme === "dark") {
      root.classList.add("dark");
    } else {
      const systemTheme = getSystemPreference();
      root.classList.toggle("dark", systemTheme === "dark");
    }
  };

  const icons = {
    light: <Sun size={18} />,
    dark: <Moon size={18} />,
    system: <Monitor size={18} />,
  };

  const nextTheme = {
    light: "dark",
    dark: "system",
    system: "light",
  };

  return (
    <button
      title={`Badilisha mandhari (sasa: ${theme})`}
      onClick={() => setTheme(nextTheme[theme])}
      className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center justify-center"
    >
      {icons[theme]}
    </button>
  );
}