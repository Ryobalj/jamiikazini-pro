// src/routes/modulePages.js

import Overview from "@/app/businesses/pages/Overview";
import Products from "@/app/businesses/pages/Products";
import Services from "@/app/businesses/pages/Services";
import Branches from "@/app/businesses/pages/Branches";
import Settings from "@/app/businesses/pages/Settings";

import KiiniDashboard from "@/app/kiini/pages/KiiniDashboard";
import InstitutionsListPage from "@/app/kiini/pages/InstitutionsListPage";
import DepartmentManagement from "@/app/kiini/pages/DepartmentManagement";
import StaffProfiles from "@/app/kiini/pages/StaffProfiles";
import InstitutionTiers from "@/app/kiini/pages/InstitutionTiers";
import InstitutionTypes from "@/app/kiini/pages/InstitutionTypes";

import ProfilePage from "@/app/accounts/pages/ProfilePage";
import SettingsPage from "@/app/accounts/pages/SettingsPage";
import WalletPage from "@/app/accounts/pages/WalletPage";
import EditProfilePage from "@/app/accounts/pages/EditProfilePage";

import AdminAuditPage from "@/app/payments/pages/admin/AdminAuditPage";
import TeachingHome from "@/app/syllabus/pages/TeachingHome";
import MySubjects from "@/app/syllabus/pages/MySubjects";
import MyTimetable from "@/app/syllabus/pages/MyTimetable";
import LessonPlanPage from "@/app/syllabus/pages/LessonPlanPage";
import SchemeOfWorkPage from "@/app/syllabus/pages/SchemeOfWorkPage";

export const modulePages = {
  businesses: {
    layout: "business",
    dynamic: true,
    path: "/businesses/dashboard/:id",
    pages: [
      { path: "overview", element: <Overview /> },
      { path: "products", element: <Products /> },
      { path: "services", element: <Services /> },
      { path: "branches", element: <Branches /> },
      { path: "settings", element: <Settings /> },
    ],
  },

  kiini: {
    layout: "main",
    dynamic: false,
    path: "/kiini/dashboard",
    pages: [
      { index: true, element: <KiiniDashboard /> },
      { path: "institutions", element: <InstitutionsListPage /> },
      { path: "departments", element: <DepartmentManagement /> },
      { path: "staff-profiles", element: <StaffProfiles /> },
      { path: "institution-tiers", element: <InstitutionTiers /> },
      { path: "institution-types", element: <InstitutionTypes /> },
    ],
  },

  accounts: {
    layout: "main",
    dynamic: false,
    path: "/accounts",
    pages: [
      { path: "profile", element: <ProfilePage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "wallet", element: <WalletPage /> },
      { path: "edit", element: <EditProfilePage /> },
    ],
  },

  paymentsAdmin: {
    layout: "main",
    dynamic: false,
    path: "/payments/audit-logs",
    allowedRoles: ["ADMIN", "SUPERUSER"],
    pages: [
      { path: "", element: <AdminAuditPage /> },
    ],
  },

  syllabus: {
    layout: "main",
    dynamic: false,
    path: "/teaching",
    pages: [
      { index: true, element: <TeachingHome /> },
      { path: "my-subjects", element: <MySubjects /> },
      { path: "timetable", element: <MyTimetable /> }, // ✅ Hapa
      { path: "lesson-plan", element: <LessonPlanPage /> }, // 🟢 Lesson Plan
      { path: "scheme", element: <SchemeOfWorkPage /> }, // 🟢 Scheme of Work
    ],
  },

};