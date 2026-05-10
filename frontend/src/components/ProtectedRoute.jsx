// src/components/ProtectedRoute.jsx

import React, { useState, useEffect } from "react";
import { Navigate, useLocation } from "react-router-dom";
import api from "@/lib/axios";

export default function ProtectedRoute({ children }) {
  const [state, setState] = useState({
    isVerifying: true,
    isValid: false
  });
  const location = useLocation();
  
  useEffect(() => {
    const checkAuth = async () => {
      const accessToken = localStorage.getItem("access_token");
      
      console.log("ProtectedRoute - checking auth for:", location.pathname);
      console.log("Token exists:", !!accessToken);
      
      if (!accessToken) {
        console.log("No token, redirecting to login");
        setState({ isVerifying: false, isValid: false });
        return;
      }

      try {
        console.log("Verifying token...");
        const response = await api.get("/auth/me/");
        console.log("Token valid for:", response.data.email);
        setState({ isVerifying: false, isValid: true });
      } catch (error) {
        console.error("Token verification failed:", error.response?.status);
        
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        
        setState({ isVerifying: false, isValid: false });
      }
    };

    checkAuth();
  }, [location.pathname]);

  if (state.isVerifying) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Verifying session...</p>
        </div>
      </div>
    );
  }

  if (!state.isValid) {
    console.log("Redirecting to login");
    const redirectState = {
      from: location,
      ...(location.state?.modal ? { 
        modal: true, 
        backgroundLocation: location.state.backgroundLocation || "/" 
      } : {})
    };
    
    return <Navigate to="/security/login" state={redirectState} replace />;
  }

  return children;
}