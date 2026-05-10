// src/components/ui/button.jsx

import clsx from "clsx";
import { Loader2 } from "lucide-react";

export function Button({
  children,
  variant = "primary", // primary | secondary | danger
  size = "md",          // sm | md | lg
  loading = false,
  disabled = false,
  className = "",
  ...props
}) {
  const baseStyles = "inline-flex items-center justify-center font-medium rounded-2xl transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2";

  const sizeStyles = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-base",
    lg: "px-5 py-3 text-lg",
  };

  const variantStyles = {
    primary: "bg-[#1976D2] text-white hover:bg-[#125aaa] focus:ring-[#1976D2]",
    secondary: "bg-[#F57C00] text-white hover:bg-[#e56700] focus:ring-[#F57C00]",
    danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
  };

  const isDisabled = disabled || loading;

  return (
    <button
      className={clsx(
        baseStyles,
        sizeStyles[size],
        variantStyles[variant],
        isDisabled && "opacity-50 cursor-not-allowed",
        className
      )}
      disabled={isDisabled}
      {...props}
    >
      {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
}