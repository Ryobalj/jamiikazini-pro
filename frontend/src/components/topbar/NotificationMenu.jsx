// src/components/topbar/NotificationMenu.jsx

import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Package, MessageCircle, Wallet, Inbox, Bell, CheckCheck } from "lucide-react";
import { useAppContext } from "@/context/AppContext";

const ICONS = {
  ORDER: Package,
  CHAT: MessageCircle,
  PAYMENT: Wallet,
  REQUEST: Inbox,
  SYSTEM: Bell,
};

function timeAgo(isoString, t) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(isoString).getTime()) / 1000));
  if (seconds < 60) return t("notifications.just_now", "Sasa hivi");
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return t("notifications.minutes_ago", "{{count}} dk zilizopita", { count: minutes });
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return t("notifications.hours_ago", "{{count}} saa zilizopita", { count: hours });
  const days = Math.floor(hours / 24);
  return t("notifications.days_ago", "{{count}} siku zilizopita", { count: days });
}

export default function NotificationMenu({ onClose }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { notifications, markNotificationRead, markAllNotificationsRead } = useAppContext();

  const handleClick = (n) => {
    if (!n.is_read) markNotificationRead(n.id);
    if (n.link) {
      navigate(n.link);
      onClose?.();
    }
  };

  return (
    <div className="absolute right-0 mt-2 w-80 rounded-lg shadow-lg bg-white dark:bg-gray-800 ring-1 ring-gray-200 dark:ring-gray-700 p-3 space-y-2 animate-fade-in z-50">
      <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 pb-2">
        <span className="font-medium text-sm text-gray-900 dark:text-white">
          {t("notifications.title", "Arifa")}
        </span>
        {notifications.length > 0 && (
          <button
            onClick={markAllNotificationsRead}
            className="flex items-center gap-1 text-xs text-blue-500 hover:underline"
          >
            <CheckCheck className="w-3.5 h-3.5" /> {t("notifications.mark_all_read", "Zote Zimesomwa")}
          </button>
        )}
      </div>

      <div className="max-h-80 overflow-y-auto space-y-1">
        {notifications.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-6">
            {t("notifications.empty", "Hakuna arifa bado.")}
          </p>
        ) : (
          notifications.map((n) => {
            const Icon = ICONS[n.notification_type] || Bell;
            return (
              <button
                key={n.id}
                onClick={() => handleClick(n)}
                className={`w-full flex items-start gap-2 text-left p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 ${
                  n.is_read ? "" : "bg-blue-50 dark:bg-blue-900/20"
                }`}
              >
                <Icon className="w-4 h-4 mt-0.5 shrink-0 text-gray-500 dark:text-gray-400" />
                <div className="min-w-0">
                  <p className="text-sm text-gray-800 dark:text-gray-200 line-clamp-2">{n.message}</p>
                  <p className="text-[11px] text-gray-400 dark:text-gray-500">{timeAgo(n.created_at, t)}</p>
                </div>
                {!n.is_read && <span className="w-2 h-2 rounded-full bg-blue-500 mt-1.5 shrink-0" />}
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
