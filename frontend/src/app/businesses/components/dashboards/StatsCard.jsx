// src/app/businesses/components/dashboards/StatsCard.jsx

import React from "react";
import { Circle } from "lucide-react"; // Fallback icon

const StatsCard = ({ title, value, icon: Icon, color = "blue", extra = null }) => {
  const bgColor = {
    blue: "bg-blue-100 text-blue-700",
    green: "bg-green-100 text-green-700",
    orange: "bg-orange-100 text-orange-700",
    red: "bg-red-100 text-red-700",
    gray: "bg-gray-100 text-gray-700",
  }[color] || "bg-gray-100 text-gray-700";

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-xl p-4 flex items-center gap-4 w-full">
      <div className={`p-3 rounded-full ${bgColor}`}>
        {Icon ? <Icon className="w-6 h-6" /> : <Circle className="w-6 h-6" />}
      </div>
      <div className="flex flex-col">
        <span className="text-sm text-gray-500 dark:text-gray-400">{title}</span>
        <span className="text-xl font-bold text-gray-900 dark:text-white">{value}</span>
        {extra && <span className="text-xs text-gray-400 dark:text-gray-500">{extra}</span>}
      </div>
    </div>
  );
};

export default StatsCard;