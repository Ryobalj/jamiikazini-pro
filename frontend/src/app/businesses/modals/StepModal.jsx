// src/app/businesses/modals/StepModal.jsx

import React from "react";
import { Dialog } from "@headlessui/react";
import { X } from "lucide-react";
import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card";
import clsx from "clsx";

export default function StepModal({
  isOpen,
  onClose,
  title,
  subtitle,
  icon,
  children,
  footer,
  wide = false,
  hideClose = false,
}) {
  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onClose={onClose} className="fixed inset-0 z-50">
      <div className="flex items-center justify-center min-h-screen px-2 sm:px-4 bg-black bg-opacity-40">
        <Dialog.Panel
          className={clsx("relative w-full", {
            "max-w-2xl": !wide,
            "max-w-4xl": wide,
          })}
        >
          <Card
            shadowSize="medium"
            className="max-h-[90vh] sm:max-h-none overflow-hidden flex flex-col"
          >
            {!hideClose && (
              <button
                onClick={onClose}
                className="absolute top-4 right-4 text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            )}

            <CardHeader
              title={title}
              subtitle={subtitle}
              icon={icon}
              divider
            />

            <CardContent
              padding
              noPaddingTop
              className="overflow-y-auto px-4 sm:px-6 flex-1"
            >
              {children}
            </CardContent>

            {footer && (
              <CardFooter className="mt-4" align="right" divider>
                {footer}
              </CardFooter>
            )}
          </Card>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
}