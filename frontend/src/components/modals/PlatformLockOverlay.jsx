// src/components/modals/PlatformLockOverlay.jsx

import { Dialog } from "@headlessui/react";
import { useLocation, useNavigate } from "react-router-dom";
import { Lock, GraduationCap, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTranslation } from "react-i18next";
import { logoutUser } from "@/lib/auth";

// Njia zinazoendelea kufanya kazi hata jukwaa likiwa limefungwa: JamiiShule
// (module pekee inayoachwa wazi) na kuingia/kujisajili (bila hizi mtumiaji
// hawezi hata kuthibitisha kama amefunguliwa au kuomba akaunti ya ADMIN).
const EXEMPT_PREFIXES = ["/teaching", "/security/login", "/auth/register", "/auth/verify-email"];

export default function PlatformLockOverlay({ locked, message }) {
  const { t } = useTranslation("common");
  const location = useLocation();
  const navigate = useNavigate();

  const isExemptRoute = EXEMPT_PREFIXES.some((prefix) => location.pathname.startsWith(prefix));

  if (!locked || isExemptRoute) return null;

  return (
    <Dialog open onClose={() => {}} className="relative z-[100]">
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="w-full max-w-md rounded-2xl bg-white dark:bg-neutral-900 p-6 shadow-xl space-y-4 text-center">
          <div className="mx-auto w-14 h-14 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
            <Lock className="w-7 h-7 text-amber-600 dark:text-amber-400" />
          </div>
          <Dialog.Title className="text-lg font-semibold text-gray-800 dark:text-white">
            {t("platform_lock.title")}
          </Dialog.Title>
          <Dialog.Description className="text-sm text-gray-600 dark:text-gray-300">
            {message || t("platform_lock.default_message")}
          </Dialog.Description>
          <div className="flex flex-col gap-2 pt-2">
            <Button
              onClick={() => navigate("/teaching")}
              className="bg-purple-600 hover:bg-purple-700"
            >
              <GraduationCap className="w-4 h-4 mr-2" />
              {t("platform_lock.go_to_jamiishule")}
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                logoutUser();
                navigate("/security/login/");
              }}
            >
              <LogOut className="w-4 h-4 mr-2" />
              {t("platform_lock.logout")}
            </Button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
}
