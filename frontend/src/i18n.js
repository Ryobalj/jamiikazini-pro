import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

// Scan both src/locales/ and src/app/**/locales/
const loadLocales = () => {
  const resources = {};
  const context = import.meta.glob([
    "./locales/*.json",                     // global: src/locales/sw.json
    "./app/**/locales/*.json"              // modular: src/app/businesses/locales/sw.json
  ], { eager: true });

  for (const path in context) {
    const pathParts = path.split(/\/|\\/); // cross-platform safe
    const langCode = pathParts.at(-1).replace(".json", ""); // sw or en

    // Determine namespace: if from src/locales -> use "common", else use app folder name
    let namespace = "common";
    if (path.includes("/app/")) {
      const appIndex = pathParts.indexOf("app");
      namespace = pathParts[appIndex + 1]; // e.g., "businesses", "health", etc.
    }

    // Initialize language entry if needed
    if (!resources[langCode]) {
      resources[langCode] = {};
    }

    // Assign namespace content
    resources[langCode][namespace] = context[path];
  }

  return resources;
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: "sw",
    debug: false,
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ["localStorage", "navigator", "htmlTag"],
      caches: ["localStorage"],
    },
    resources: loadLocales(),
    defaultNS: "common", // fallback to common if no namespace
  });

export default i18n;
