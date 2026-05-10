// src/components/AppLayout.jsx

import React from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import TabBar from "./TabBar";
import { useAppContext } from "@/context/AppContext";
import { useNavigate } from "react-router-dom";

export default function AppLayout({ children }) {
  const { user } = useAppContext();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    navigate("/");         // 🔹 Rudi kwenye tab ya "Jamiikazini"
    window.location.reload();  // 🔄 Safisha context na UI yote
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white flex flex-col">
      {/* TopBar juu kabisa */}
      <TopBar user={user} onLogout={handleLogout} />

      {/* Chini ya TopBar: Sidebar kushoto + Main content kulia */}
      <div className="flex flex-1 h-[calc(100vh-4rem)]">
        <Sidebar />

        {/* Kulia: TabBar juu, Main content chini */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <TabBar />
          <main className="flex-1 p-4 overflow-y-auto">{children}</main>
        </div>
      </div>
    </div>
  );
}