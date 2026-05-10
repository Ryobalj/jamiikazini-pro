// src/App.jsx

import "@/i18n";
import React from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import { generateDynamicRoutes } from "@/routes/dynamicRoutes";
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Login from "@/pages/auth/Login";
import Register from "@/pages/auth/Register";
import VerifyEmail from "@/pages/auth/VerifyEmail";
import Home from "@/pages/Home";
import HomePage from "@/pages/HomePage";
import InviteFriends from "@/pages/InviteFriends";

// Account Pages
import ProfilePage from "@/app/accounts/pages/ProfilePage";
import EditProfilePage from "@/app/accounts/pages/EditProfilePage";
import SettingsPage from "@/app/accounts/pages/SettingsPage";
import WalletPage from "@/app/accounts/pages/WalletPage";

// Institution Pages
import InstitutionProfile from "@/app/kiini/pages/InstitutionProfile";

// Business Pages
import BusinessRegistrationPage from "@/app/businesses/pages/BusinessRegistrationPage";
import NearbyBusinessesPage from "@/app/businesses/pages/NearbyBusinessesPage";

// Chat Pages
import JamiichatPage from "@/app/jamiichat/pages/JamiichatPage";

// Jamiiwallet pages
import JamiiWalletPage from "@/app/jamiiwallet/pages/JamiiWalletPage";

import MainLayout from "@/layouts/MainLayout";
import ProtectedRoute from "@/components/ProtectedRoute";

export default function App() {
  const location = useLocation();
  const backgroundLocation = location.state?.backgroundLocation;

  return (
    <>
      <Routes location={backgroundLocation || location}>
        {/* Public Routes */}
        <Route path="/" element={<MainLayout><HomePage /></MainLayout>} />
        <Route path="/security/login/" element={<MainLayout hideSidebar><Login /></MainLayout>} />
        <Route path="/auth/register/" element={<MainLayout hideSidebar><Register /></MainLayout>} />
        <Route path="/auth/verify-email/:user_id/:token/" element={<MainLayout hideSidebar><VerifyEmail /></MainLayout>} />

        {/* Protected Routes */}
        <Route path="/home" element={<ProtectedRoute><MainLayout><Home /></MainLayout></ProtectedRoute>} />
        <Route path="/invite" element={<ProtectedRoute><MainLayout><InviteFriends /></MainLayout></ProtectedRoute>} />

        {/* Nearby Route - First in sidebar */}
        <Route path="/nearby" element={<ProtectedRoute><MainLayout><NearbyBusinessesPage /></MainLayout></ProtectedRoute>} />

        {/* Account Routes */}
        <Route path="/accounts/profile" element={<ProtectedRoute><MainLayout><ProfilePage /></MainLayout></ProtectedRoute>} />
        <Route path="/accounts/edit" element={<ProtectedRoute><MainLayout><EditProfilePage /></MainLayout></ProtectedRoute>} />
        <Route path="/accounts/settings" element={<ProtectedRoute><MainLayout><SettingsPage /></MainLayout></ProtectedRoute>} />
        <Route path="/accounts/wallet" element={<ProtectedRoute><MainLayout><WalletPage /></MainLayout></ProtectedRoute>} />
        <Route path="/accounts/change-password" element={<ProtectedRoute><MainLayout><div>Change Password</div></MainLayout></ProtectedRoute>} />

        {/* Institution Routes */}
        <Route path="/institutions/create" element={<ProtectedRoute><MainLayout><div>Create Institution</div></MainLayout></ProtectedRoute>} />
        <Route path="/kiini/institutions/:id" element={<ProtectedRoute><MainLayout><InstitutionProfile /></MainLayout></ProtectedRoute>} />
        <Route path="/kiini/institutions/:id/settings" element={<ProtectedRoute><MainLayout><div>Institution Settings</div></MainLayout></ProtectedRoute>} />
        <Route path="/kiini/institutions/:id/edit" element={<ProtectedRoute><MainLayout><div>Edit Institution</div></MainLayout></ProtectedRoute>} />
        <Route path="/kiini/dashboard" element={<ProtectedRoute><MainLayout><div>Kiini Dashboard</div></MainLayout></ProtectedRoute>} />
        <Route path="/kiini/dashboard/institutions" element={<ProtectedRoute><MainLayout><div>Institutions</div></MainLayout></ProtectedRoute>} />
        <Route path="/kiini/dashboard/departments" element={<ProtectedRoute><MainLayout><div>Departments</div></MainLayout></ProtectedRoute>} />
        <Route path="/kiini/dashboard/staff-profiles" element={<ProtectedRoute><MainLayout><div>Staff Profiles</div></MainLayout></ProtectedRoute>} />
        <Route path="/kiini/dashboard/institution-tiers" element={<ProtectedRoute><MainLayout><div>Institution Tiers</div></MainLayout></ProtectedRoute>} />
        <Route path="/kiini/dashboard/institution-types" element={<ProtectedRoute><MainLayout><div>Institution Types</div></MainLayout></ProtectedRoute>} />

        {/* Business Routes */}
        <Route path="/businesses/register/" element={<ProtectedRoute><MainLayout><BusinessRegistrationPage /></MainLayout></ProtectedRoute>} />

        {/* Payments Routes */}
        <Route path="/payments/audit-logs/" element={<ProtectedRoute><MainLayout><div>Audit Logs</div></MainLayout></ProtectedRoute>} />
        <Route path="/payments/invoices/" element={<ProtectedRoute><MainLayout><div>Invoices</div></MainLayout></ProtectedRoute>} />
        <Route path="/payments/payment-methods/" element={<ProtectedRoute><MainLayout><div>Payment Methods</div></MainLayout></ProtectedRoute>} />
        <Route path="/payments/payment-reports/" element={<ProtectedRoute><MainLayout><div>Payment Reports</div></MainLayout></ProtectedRoute>} />

        {/* Chat Routes */}
        <Route path="/jamiichat" element={<ProtectedRoute><MainLayout><JamiichatPage /></MainLayout></ProtectedRoute>} />
        <Route path="/jamiichat/:id" element={<ProtectedRoute><MainLayout><JamiichatPage /></MainLayout></ProtectedRoute>} />

        {/* Security Routes */}
        <Route path="/security/2fa/setup" element={<ProtectedRoute><MainLayout><div>2FA Setup</div></MainLayout></ProtectedRoute>} />


        {/* Jamiiwallet Routes */}
        <Route path="/jamiiwallet" element={<ProtectedRoute><MainLayout><JamiiWalletPage /></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/send" element={<ProtectedRoute><MainLayout><div>Send Money</div></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/request" element={<ProtectedRoute><MainLayout><div>Request Money</div></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/transactions" element={<ProtectedRoute><MainLayout><div>All Transactions</div></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/transactions/:id" element={<ProtectedRoute><MainLayout><div>Transaction Details</div></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/add-card" element={<ProtectedRoute><MainLayout><div>Add Card</div></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/add-beneficiary" element={<ProtectedRoute><MainLayout><div>Add Beneficiary</div></MainLayout></ProtectedRoute>} />

        {/* Dynamic module routes (includes business dashboard) */}
        {generateDynamicRoutes()}
      </Routes>

      <ToastContainer
        position="bottom-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="colored"
      />

      {/* Modal Version */}
      {location.state?.modal && location.pathname === "/businesses/register/" && (
        <ProtectedRoute>
          <BusinessRegistrationPage />
        </ProtectedRoute>
      )}
    </>
  );
}