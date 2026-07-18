// src/context/AppContext.jsx

import { createContext, useContext, useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import api from "@/lib/axios";
import { logoutUser } from "@/lib/auth";
import { parseJwt, getTokenStage, isTokenExpiringSoon } from "@/lib/jwt";
import ConsentModal from "@/components/modals/ConsentModal";
import { useTranslation } from "react-i18next";

const AppContext = createContext();

export const AppContextProvider = ({ children }) => {
  const { t } = useTranslation("common"); // ✅ i18n support
  const navigate = useNavigate();
  const location = useLocation();

  const [user, setUser] = useState(null);
  const [userMenu, setUserMenu] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notifications, setNotifications] = useState([]);

  const [currentBusinessId, setCurrentBusinessId] = useState(null);
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [awaitingConsent, setAwaitingConsent] = useState(false);

  // 🔍 Detect businessId from URL
  useEffect(() => {
    const match = location.pathname.match(/\/dashboard\/([a-zA-Z0-9-]+)/);
    setCurrentBusinessId(match ? match[1] : null);
  }, [location]);

  // 📡 Fetch user & menu
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      setUser(null);
      setUserMenu([]);
      return;
    }

    async function fetchUserAndMenu() {
      try {
        const [userRes, menuRes] = await Promise.all([
          api.get("/auth/me/"),
          api.get("/kiini/user-menu/"),
        ]);

        const userData = userRes.data;
        if (!userData.full_name && userData.name) {
          userData.full_name = userData.name;
        }

        setUser(userData);
        setUserMenu(Array.isArray(menuRes.data) ? menuRes.data : []);
        setError(null);
      } catch (err) {
        console.error("⚠️ Failed to load user or menu:", err);
        setError(t("errors.fetch_user_or_menu"));
        setUser(null);
        setUserMenu([]);
      } finally {
        setLoading(false);
      }
    }

    fetchUserAndMenu();

    // ⏳ Session timeout handler
    const decoded = parseJwt(token);
    if (decoded?.exp) {
      const expiryTime = decoded.exp * 1000;
      const remainingTime = expiryTime - Date.now();

      if (remainingTime <= 0) {
        logoutUser();
        navigate("/security/login/");
        alert(t("session.expired_alert"));
      } else {
        const timeout = setTimeout(() => {
          logoutUser();
          alert(t("session.expired_alert"));
          navigate("/security/login/");
        }, remainingTime);

        return () => clearTimeout(timeout);
      }
    }
  }, [navigate]);

  // 🔔 Poll notifications every 30s while logged in
  useEffect(() => {
    if (!user) {
      setNotifications([]);
      return;
    }

    let cancelled = false;
    const fetchNotifications = () => {
      api
        .get("/kiini/notifications/")
        .then((res) => {
          if (!cancelled) {
            setNotifications(Array.isArray(res.data) ? res.data : res.data?.results || []);
          }
        })
        .catch(() => {});
    };

    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [user]);

  const markNotificationRead = (id) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    api.post(`/kiini/notifications/${id}/mark-read/`).catch(() => {});
  };

  const markAllNotificationsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    api.post("/kiini/notifications/mark-all-read/").catch(() => {});
  };

  // ⏱ Consent Modal trigger
  useEffect(() => {
    const interval = setInterval(() => {
      const token = localStorage.getItem("access_token");
      if (!token || awaitingConsent) return;

      setShowConsentModal(true);
      setAwaitingConsent(true);
    }, 5 * 60 * 1000); // every 5 minutes

    return () => clearInterval(interval);
  }, [awaitingConsent]);

  // ✅ Consent handlers
  const handleConsentConfirm = () => {
    setShowConsentModal(false);
    setAwaitingConsent(false);

    const token = localStorage.getItem("access_token");
    if (!token) return;

    const stage = getTokenStage(token);
    const isLast5Min = stage === 3;

    if (isLast5Min && isTokenExpiringSoon(token, 1)) {
      const refresh = localStorage.getItem("refresh_token");
      const refreshDecoded = parseJwt(refresh);
      const refreshTimeLeft = (refreshDecoded?.exp || 0) * 1000 - Date.now();

      if (refreshTimeLeft < 5 * 60 * 1000) {
        alert(t("session.expiring_soon"));
        return;
      }

      api
        .post("/security/token/refresh/", { refresh })
        .then((res) => {
          localStorage.setItem("access_token", res.data.access);
          if (res.data.refresh) {
            localStorage.setItem("refresh_token", res.data.refresh);
          }
        })
        .catch(() => {
          logoutUser();
          alert(t("session.expired_alert"));
          navigate("/security/login/");
        });
    }
  };

  const handleConsentCancel = () => {
    setShowConsentModal(false);
    setAwaitingConsent(false);
    logoutUser();
    alert(t("session.inactive_logout"));
    navigate("/security/login/");
  };

  return (
    <AppContext.Provider
      value={{
        user,
        setUser,
        userMenu,
        setUserMenu,
        currentBusinessId,
        setCurrentBusinessId,
        loading,
        error,
        notifications,
        unreadCount: notifications.filter((n) => !n.is_read).length,
        markNotificationRead,
        markAllNotificationsRead,
      }}
    >
      {children}
      <ConsentModal
        open={showConsentModal}
        onConfirm={handleConsentConfirm}
        onCancel={handleConsentCancel}
      />
    </AppContext.Provider>
  );
};

export const useAppContext = () => useContext(AppContext);