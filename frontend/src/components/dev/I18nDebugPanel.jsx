// src/components/dev/I18nDebugPanel.jsx
import React, { useState, useRef, useEffect } from "react";
import i18n from "@/i18n";
import { GripVertical, X } from "lucide-react";

export function I18nDebugPanel({ lang = i18n.language || "sw" }) {
  const [activeTab, setActiveTab] = useState("missing");
  const panelRef = useRef(null);
  const [position, setPosition] = useState({ x: 20, y: 20 });
  const [dragging, setDragging] = useState(false);
  const offset = useRef({ x: 0, y: 0 });

  const namespaces = Object.keys(i18n.options.resources?.[lang] || {});
  const missingKeys = [];

  namespaces.forEach((ns) => {
    const keys = Object.keys(i18n.options.resources[lang][ns]);
    keys.forEach((key) => {
      const value = i18n.t(`${ns}:${key}`);
      if (value === `${ns}:${key}`) {
        missingKeys.push(`${ns}:${key}`);
      }
    });
  });

  // === Drag logic ===
  const startDrag = (e) => {
    setDragging(true);
    offset.current = {
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    };
  };

  const doDrag = (e) => {
    if (!dragging) return;
    setPosition({
      x: e.clientX - offset.current.x,
      y: e.clientY - offset.current.y,
    });
  };

  const stopDrag = () => setDragging(false);

  useEffect(() => {
    window.addEventListener("mousemove", doDrag);
    window.addEventListener("mouseup", stopDrag);
    return () => {
      window.removeEventListener("mousemove", doDrag);
      window.removeEventListener("mouseup", stopDrag);
    };
  }, [dragging]);

  return (
    <div
      ref={panelRef}
      className="fixed z-50 text-xs rounded shadow-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 w-[300px] max-h-[60vh] flex flex-col"
      style={{ left: position.x, top: position.y }}
    >
      {/* Header */}
      <div
        onMouseDown={startDrag}
        className="cursor-move flex items-center justify-between px-3 py-2 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700"
      >
        <div className="flex items-center space-x-2 text-[0.75rem] font-bold text-red-600 dark:text-red-400">
          <GripVertical size={12} />
          <span>I18n Debug Panel</span>
        </div>
        <button
          onClick={() => panelRef.current?.remove()}
          className="text-gray-500 hover:text-red-500"
        >
          <X size={12} />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 text-[0.7rem]">
        {["missing", "lang", "namespaces"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-1 px-2 border-r last:border-r-0 border-gray-300 dark:border-gray-700 ${
              activeTab === tab
                ? "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 font-semibold"
                : "hover:bg-gray-100 dark:hover:bg-gray-800"
            }`}
          >
            {tab === "missing" && `🧪 ${missingKeys.length} MIA`}
            {tab === "lang" && "🌐 Lugha"}
            {tab === "namespaces" && "📦 Namespaces"}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-2 overflow-y-auto flex-1">
        {activeTab === "missing" && (
          <>
            {missingKeys.length === 0 ? (
              <p className="text-green-600">✔️ Hakuna tafsiri inayokosekana.</p>
            ) : (
              <ul className="list-disc list-inside space-y-1 text-red-500">
                {missingKeys.map((key) => (
                  <li key={key}>{key}</li>
                ))}
              </ul>
            )}
          </>
        )}

        {activeTab === "lang" && (
          <div className="space-y-1">
            <p><strong>Current:</strong> {i18n.language}</p>
            <p><strong>Fallback:</strong> {i18n.options.fallbackLng}</p>
            <p><strong>Detected:</strong> {i18n.services?.languageDetector?.detect()}</p>
          </div>
        )}

        {activeTab === "namespaces" && (
          <ul className="list-disc list-inside space-y-1">
            {namespaces.map((ns) => (
              <li key={ns}>{ns}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}