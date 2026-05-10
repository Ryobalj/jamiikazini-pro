// src/pages/Home.jsx

import React, { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useLocation } from "react-router-dom";
import api from "@/lib/axios";
import { Loader2 } from "lucide-react";

const services = [
  {
    id: "teaching",
    icon: "📘",
    labelKey: "services.teaching",
    route: "/teaching",
  },
  {
    id: "business",
    icon: "💼",
    labelKey: "services.business",
  },
  {
    id: "health",
    icon: "🧑‍⚕️",
    labelKey: "services.health",
    route: "/health",
  },
  {
    id: "payments",
    icon: "💳",
    labelKey: "services.payments",
    route: "/payments/audit-logs",
  },
];

export default function Home() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [user, setUser] = useState(null);
  const [userBusinesses, setUserBusinesses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [authChecking, setAuthChecking] = useState(true);

  const fetchUserBusinesses = useCallback(async () => {
    try {
      setLoading(true);
      
      const response = await api.get("/businesses/");
      
      if (Array.isArray(response.data)) {
        setUserBusinesses(response.data);
      } else if (response.data.results) {
        setUserBusinesses(response.data.results);
      } else {
        setUserBusinesses([]);
      }
    } catch (err) {
      console.log("Could not fetch businesses:", err.response?.status);
      
      if (err.response?.status === 405) {
        try {
          const userResponse = await api.get("/auth/me/");
          if (userResponse.data.businesses) {
            setUserBusinesses(userResponse.data.businesses);
          } else {
            setUserBusinesses([]);
          }
        } catch (userErr) {
          setUserBusinesses([]);
        }
      } else {
        setUserBusinesses([]);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("access_token");
      
      if (!token) {
        navigate("/security/login", { replace: true });
        return;
      }

      try {
        const response = await api.get("/auth/me/");
        setUser(response.data);
        setAuthChecking(false);
      } catch (err) {
        console.error("Auth check failed:", err.response?.status);
        localStorage.clear();
        navigate("/security/login", { replace: true });
      }
    };

    checkAuth();
  }, [navigate]);

  useEffect(() => {
    if (authChecking) return;
    fetchUserBusinesses();
  }, [authChecking, fetchUserBusinesses]);

  // Listen for business created event
  useEffect(() => {
    const handleBusinessCreated = () => {
      fetchUserBusinesses();
    };

    window.addEventListener('businessCreated', handleBusinessCreated);
    return () => window.removeEventListener('businessCreated', handleBusinessCreated);
  }, [fetchUserBusinesses]);

  const handleBusinessClick = () => {
    if (loading) return;
    
    if (userBusinesses && userBusinesses.length > 0) {
      const firstBusiness = userBusinesses[0];
      navigate(`/businesses/dashboard/${firstBusiness.id}/overview`);
    } else {
      navigate("/businesses/register/", {
        state: {
          modal: true,
          backgroundLocation: location,
        },
      });
    }
  };

  const handleServiceClick = (service) => {
    if (service.id === "business") {
      handleBusinessClick();
    } else {
      navigate(service.route);
    }
  };

  if (authChecking) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="p-4 bg-gray-100 dark:bg-gray-900 min-h-screen">
      <h1 className="text-xl font-normal text-gray-900 dark:text-white mb-1">
        {t("user_home.welcome")}, {user.full_name || user.email}
      </h1>
      <p className="text-xs text-gray-600 dark:text-gray-400 mb-8">
        {t("user_home.description")}
      </p>

      <div className="grid grid-cols-4 gap-2">
        {services.map((service) => (
          <button
            key={service.id}
            onClick={() => handleServiceClick(service)}
            disabled={service.id === "business" && loading}
            className={`
              flex flex-col items-center
              py-3 px-1 rounded-xl
              active:bg-gray-300 dark:active:bg-gray-700
              transition-colors
              focus:outline-none
              group
              ${service.id === "business" && loading ? "opacity-50 cursor-not-allowed" : ""}
            `}
          >
            {service.id === "business" && loading ? (
              <Loader2 className="w-10 h-10 mb-1.5 animate-spin text-gray-400" />
            ) : (
              <span className="text-4xl mb-1.5 group-active:scale-95 transition-transform">
                {service.icon}
              </span>
            )}
            <span className="text-[10px] font-medium text-center text-gray-700 dark:text-gray-300 leading-tight">
              {t(service.labelKey)}
              {service.id === "business" && !loading && userBusinesses?.length > 0 && (
                <span className="block text-[8px] text-blue-500">
                  {userBusinesses.length} {userBusinesses.length === 1 ? 'business' : 'businesses'}
                </span>
              )}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
