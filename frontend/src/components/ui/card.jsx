// src/components/ui/card.jsx

import React from "react";
import clsx from "clsx";
import PropTypes from "prop-types";

export function Card({ 
  children, 
  className = "", 
  hoverEffect = false,
  bordered = false,
  shadowSize = "soft",
  ...props 
}) {
  return (
    <div
      className={clsx(
        "bg-white dark:bg-gray-800 rounded-2xl p-6 transition-all duration-300",
        {
          "shadow-soft": shadowSize === "soft",
          "shadow-medium": shadowSize === "medium",
          "shadow-hard": shadowSize === "hard",
          "border border-gray-200 dark:border-gray-700": bordered,
          "hover:shadow-lg hover:-translate-y-1": hoverEffect,
        },
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

Card.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  hoverEffect: PropTypes.bool,
  bordered: PropTypes.bool,
  shadowSize: PropTypes.oneOf(["soft", "medium", "hard"]),
};

export function CardHeader({ 
  title, 
  subtitle,
  icon, 
  actions,
  className = "",
  align = "left",
  divider = true
}) {
  return (
    <div
      className={clsx(
        "flex flex-col gap-2 mb-4",
        {
          "border-b border-gray-200 dark:border-gray-700 pb-3": divider,
          "items-start": align === "left",
          "items-center": align === "center",
          "items-end": align === "right",
        },
        className
      )}
    >
      <div className="flex items-center w-full gap-3">
        {icon && <div className="text-blue-600 dark:text-blue-400">{icon}</div>}
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
            {title}
          </h3>
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {subtitle}
            </p>
          )}
        </div>
        {actions && <div className="flex-shrink-0">{actions}</div>}
      </div>
    </div>
  );
}

CardHeader.propTypes = {
  title: PropTypes.string.isRequired,
  subtitle: PropTypes.string,
  icon: PropTypes.node,
  actions: PropTypes.node,
  className: PropTypes.string,
  align: PropTypes.oneOf(["left", "center", "right"]),
  divider: PropTypes.bool,
};

export function CardContent({ 
  children, 
  className = "",
  padding = true,
  noPaddingTop = false
}) {
  return (
    <div
      className={clsx(
        "text-sm text-gray-700 dark:text-gray-300",
        {
          "px-6": padding,
          "pb-6": padding,
          "pt-0": noPaddingTop,
          "pt-6": padding && !noPaddingTop,
        },
        className
      )}
    >
      {children}
    </div>
  );
}

CardContent.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  padding: PropTypes.bool,
  noPaddingTop: PropTypes.bool,
};

export function CardFooter({ 
  children, 
  className = "",
  align = "right",
  divider = true
}) {
  return (
    <div
      className={clsx(
        "flex gap-3",
        {
          "justify-start": align === "left",
          "justify-center": align === "center",
          "justify-end": align === "right",
          "border-t border-gray-200 dark:border-gray-700 pt-4": divider,
        },
        className
      )}
    >
      {children}
    </div>
  );
}

CardFooter.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  align: PropTypes.oneOf(["left", "center", "right"]),
  divider: PropTypes.bool,
};