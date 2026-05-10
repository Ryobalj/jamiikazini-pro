// src/components/modals/ConsentModal.jsx

import { useEffect } from "react";
import { Dialog } from "@headlessui/react";
import { Button } from "@/components/ui/button";
import { useTranslation } from "react-i18next";

const ConsentModal = ({ open, onConfirm, onCancel }) => {
  const { t } = useTranslation();

  useEffect(() => {
    if (open) {
      const timeout = setTimeout(() => {
        onCancel();
      }, 30000);
      return () => clearTimeout(timeout);
    }
  }, [open, onCancel]);

  return (
    <Dialog open={open} onClose={onCancel} className="relative z-50">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="w-full max-w-md rounded-2xl bg-white dark:bg-neutral-900 p-6 shadow-xl space-y-4">
          <Dialog.Title className="text-lg font-semibold text-gray-800 dark:text-white">
            {t("consent.title")}
          </Dialog.Title>
          <Dialog.Description className="text-sm text-gray-600 dark:text-gray-300">
            {t("consent.description")}
          </Dialog.Description>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="ghost" onClick={onCancel}>
              {t("consent.cancel")}
            </Button>
            <Button onClick={onConfirm} className="bg-blue-600 text-white hover:bg-blue-700">
              {t("consent.confirm")}
            </Button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};

export default ConsentModal;