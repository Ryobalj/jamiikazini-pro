import React from "react";
import { cn } from "@/lib/utils"; // utility ya class merging, angalia chini kama huna
import { AlertCircle } from "lucide-react";

export const Input = React.forwardRef(
  (
    {
      label,
      icon: Icon,
      helperText,
      error,
      className,
      type = "text",
      required = false,
      readOnly = false,
      disabled = false,
      ...props
    },
    ref
  ) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {label} {required && <span className="text-red-500">*</span>}
          </label>
        )}
        <div
          className={cn(
            "flex items-center px-3 py-2 border rounded-2xl shadow-sm transition bg-white",
            error
              ? "border-red-500 focus-within:ring-red-500"
              : "border-gray-300 focus-within:ring-2 focus-within:ring-primary/40",
            disabled && "bg-gray-100 cursor-not-allowed",
            className
          )}
        >
          {Icon && (
            <Icon className="text-gray-400 w-5 h-5 mr-2 shrink-0" />
          )}
          <input
            ref={ref}
            type={type}
            disabled={disabled}
            readOnly={readOnly}
            required={required}
            className="flex-1 border-none focus:ring-0 outline-none text-sm bg-transparent text-gray-900 placeholder-gray-400"
            {...props}
          />
        </div>
        {helperText && !error && (
          <p className="text-xs text-gray-500 mt-1">{helperText}</p>
        )}
        {error && (
          <div className="flex items-center mt-1 text-xs text-red-500 gap-1">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";