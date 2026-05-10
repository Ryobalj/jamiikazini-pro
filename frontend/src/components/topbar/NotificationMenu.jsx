// src/components/topbar/NotificationMenu.jsx

import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

export default function NotificationMenu({
  notifications = { requests: [], chats: [] },
  onAcceptRequest,
  onDeclineRequest,
  onClose,
}) {
  const [activeTab, setActiveTab] = useState("requests");
  const { t } = useTranslation();

  const totalRequests = notifications.requests.length;
  const totalChats = notifications.chats.length;

  return (
    <div className="absolute right-0 mt-2 w-80 rounded-lg shadow-lg bg-white dark:bg-gray-800 ring-1 ring-gray-200 dark:ring-gray-700 p-3 space-y-2 animate-fade-in z-50">
      {/* Tabs */}
      <div className="flex justify-around border-b border-gray-300 dark:border-gray-600">
        <div
          onClick={() => setActiveTab("requests")}
          className={`cursor-pointer flex-1 text-center p-2 rounded-t ${
            activeTab === "requests" ? "bg-gray-100 dark:bg-gray-700" : ""
          }`}
        >
          {t("notifications.requests")} ({totalRequests})
        </div>
        <div
          onClick={() => setActiveTab("chats")}
          className={`cursor-pointer flex-1 text-center p-2 rounded-t ${
            activeTab === "chats" ? "bg-gray-100 dark:bg-gray-700" : ""
          }`}
        >
          {t("notifications.chats")} ({totalChats})
        </div>
      </div>

      {/* Content */}
      <div className="max-h-64 overflow-y-auto space-y-2 mt-2">
        {activeTab === "requests" &&
          notifications.requests.map((req) => (
            <div
              key={req.id}
              className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <div className="font-medium">{req.title}</div>
              <div className="flex space-x-2 mt-1">
                <button
                  onClick={() => onAcceptRequest?.(req.id)}
                  className="text-xs text-blue-500 hover:underline"
                >
                  {t("notifications.accept")}
                </button>
                <button
                  onClick={() => onDeclineRequest?.(req.id)}
                  className="text-xs text-gray-500 hover:underline"
                >
                  {t("notifications.decline")}
                </button>
                <Link
                  to={`/request/${req.id}`}
                  onClick={onClose}
                  className="text-xs text-green-500 hover:underline"
                >
                  {t("notifications.view")}
                </Link>
              </div>
            </div>
          ))}

        {activeTab === "chats" &&
          notifications.chats.map((chat) => (
            <div
              key={chat.id}
              className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <div className="font-medium">{chat.title}</div>
              <div className="flex space-x-2 mt-1">
                <Link
                  to={`/chat/${chat.id}`}
                  onClick={onClose}
                  className="text-xs text-green-500 hover:underline"
                >
                  {t("notifications.open_chat")}
                </Link>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}