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
import InstitutionFormPage from "@/app/kiini/pages/InstitutionFormPage";
import InstitutionSettingsPage from "@/app/kiini/pages/InstitutionSettingsPage";

// Payments admin pages
import InvoicesPage from "@/app/payments/pages/InvoicesPage";
import PaymentMethodsPage from "@/app/payments/pages/PaymentMethodsPage";
import PaymentReportsPage from "@/app/payments/pages/PaymentReportsPage";

// Business Pages
import BusinessRegistrationPage from "@/app/businesses/pages/BusinessRegistrationPage";
import NearbyBusinessesPage from "@/app/businesses/pages/NearbyBusinessesPage";

// Chat Pages
import JamiichatPage from "@/app/jamiichat/pages/JamiichatPage";

// Jamiiwallet pages
import JamiiWalletPage from "@/app/jamiiwallet/pages/JamiiWalletPage";
import SendMoneyPage from "@/app/jamiiwallet/pages/SendMoneyPage";
import RequestMoneyPage from "@/app/jamiiwallet/pages/RequestMoneyPage";
import TransactionsListPage from "@/app/jamiiwallet/pages/TransactionsListPage";
import TransactionDetailPage from "@/app/jamiiwallet/pages/TransactionDetailPage";
import AccountsPage from "@/app/jamiiwallet/pages/AccountsPage";
import AddCardPage from "@/app/jamiiwallet/pages/AddCardPage";
import AddBeneficiaryPage from "@/app/jamiiwallet/pages/AddBeneficiaryPage";
import Setup2FAPage from "@/app/security/pages/Setup2FAPage";

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
        <Route path="/institutions/create" element={<ProtectedRoute><MainLayout><InstitutionFormPage /></MainLayout></ProtectedRoute>} />
        <Route path="/kiini/institutions/:id" element={<ProtectedRoute><MainLayout><InstitutionProfile /></MainLayout></ProtectedRoute>} />
        <Route path="/kiini/institutions/:id/settings" element={<ProtectedRoute><MainLayout><InstitutionSettingsPage /></MainLayout></ProtectedRoute>} />
        <Route path="/kiini/institutions/:id/edit" element={<ProtectedRoute><MainLayout><InstitutionFormPage /></MainLayout></ProtectedRoute>} />
        {/* /kiini/dashboard* zinashughulikiwa na generateDynamicRoutes() (modulePages.kiini)
            chini - ziliondolewa hapa ili zisigongane na routes hizo hizo. */}

        {/* Business Routes */}
        <Route path="/businesses/register/" element={<ProtectedRoute><MainLayout><BusinessRegistrationPage /></MainLayout></ProtectedRoute>} />

        {/* Payments Routes */}
        <Route path="/payments/audit-logs/" element={<ProtectedRoute><MainLayout><div>Audit Logs</div></MainLayout></ProtectedRoute>} />
        <Route path="/payments/invoices/" element={<ProtectedRoute><MainLayout><InvoicesPage /></MainLayout></ProtectedRoute>} />
        <Route path="/payments/payment-methods/" element={<ProtectedRoute><MainLayout><PaymentMethodsPage /></MainLayout></ProtectedRoute>} />
        <Route path="/payments/payment-reports/" element={<ProtectedRoute><MainLayout><PaymentReportsPage /></MainLayout></ProtectedRoute>} />

        {/* Chat Routes */}
        <Route path="/jamiichat" element={<ProtectedRoute><MainLayout><JamiichatPage /></MainLayout></ProtectedRoute>} />
        <Route path="/jamiichat/:id" element={<ProtectedRoute><MainLayout><JamiichatPage /></MainLayout></ProtectedRoute>} />

        {/* Security Routes */}
        <Route path="/security/2fa/setup" element={<ProtectedRoute><MainLayout><Setup2FAPage /></MainLayout></ProtectedRoute>} />


        {/* Jamiiwallet Routes */}
        <Route path="/jamiiwallet" element={<ProtectedRoute><MainLayout><JamiiWalletPage /></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/send" element={<ProtectedRoute><MainLayout><SendMoneyPage /></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/request" element={<ProtectedRoute><MainLayout><RequestMoneyPage /></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/accounts" element={<ProtectedRoute><MainLayout><AccountsPage /></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/transactions" element={<ProtectedRoute><MainLayout><TransactionsListPage /></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/transactions/:id" element={<ProtectedRoute><MainLayout><TransactionDetailPage /></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/add-card" element={<ProtectedRoute><MainLayout><AddCardPage /></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/add-beneficiary" element={<ProtectedRoute><MainLayout><AddBeneficiaryPage /></MainLayout></ProtectedRoute>} />

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