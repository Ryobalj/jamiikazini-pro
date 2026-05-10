// src/components/RouteDebugger.jsx

import { useEffect } from "react";
import { useLocation } from "react-router-dom";

export default function RouteDebugger({ children }) {
  const location = useLocation();
  
  useEffect(() => {
    console.log("🔍 RouteDebugger - Current path:", location.pathname);
    console.log("🔍 RouteDebugger - Full URL:", window.location.href);
    console.log("🔍 RouteDebugger - State:", location.state);
  }, [location]);
  
  return children;
}