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
import VerifyIdentityPage from "@/app/accounts/pages/VerifyIdentityPage";
import DriverVerificationPage from "@/app/logistics/pages/DriverVerificationPage";

// Institution Pages
import InstitutionProfile from "@/app/kiini/pages/InstitutionProfile";
import InstitutionFormPage from "@/app/kiini/pages/InstitutionFormPage";
import PublicHomePage from "@/app/homepage/pages/PublicHomePage";
import HomepageManagerPage from "@/app/homepage/pages/HomepageManagerPage";
import InstitutionSettingsPage from "@/app/kiini/pages/InstitutionSettingsPage";
import InstitutionStorefrontPage from "@/app/kiini/pages/InstitutionStorefrontPage";

// Payments admin pages
import InvoicesPage from "@/app/payments/pages/InvoicesPage";
import PaymentMethodsPage from "@/app/payments/pages/PaymentMethodsPage";
import PaymentReportsPage from "@/app/payments/pages/PaymentReportsPage";

// Business Pages
import BusinessRegistrationPage from "@/app/businesses/pages/BusinessRegistrationPage";
import NearbyBusinessesPage from "@/app/businesses/pages/NearbyBusinessesPage";
import BusinessStorefrontPage from "@/app/businesses/pages/BusinessStorefrontPage";
import CreditAccountPage from "@/app/businesses/pages/CreditAccountPage";

// Cart / Checkout Pages
import CartPage from "@/app/cart/pages/CartPage";
import CheckoutPage from "@/app/cart/pages/CheckoutPage";

// Item Request Pages
import RequestItemPage from "@/app/itemrequests/pages/RequestItemPage";
import WaitingForClaimPage from "@/app/itemrequests/pages/WaitingForClaimPage";
import ClaimedConfirmationPage from "@/app/itemrequests/pages/ClaimedConfirmationPage";

// Order Tracking Pages
import OrderDetailPage from "@/app/orders/pages/OrderDetailPage";
import OrdersListPage from "@/app/orders/pages/OrdersListPage";
import MyOffersPage from "@/app/businesses/pages/MyOffersPage";
import RequestImportPage from "@/app/businesses/pages/RequestImportPage";

// Logistics (Driver) Pages
import AvailableDeliveryJobsPage from "@/app/logistics/pages/AvailableDeliveryJobsPage";
import RequestServicePage from "@/app/logistics/pages/RequestServicePage";
import MyDeliveriesPage from "@/app/logistics/pages/MyDeliveriesPage";

// Chat Pages
import ConversationsListPage from "@/app/jamiichat/pages/ConversationsListPage";
import ChatDetailPage from "@/app/jamiichat/pages/ChatDetailPage";

// Jamiiwallet pages
import JamiiWalletPage from "@/app/jamiiwallet/pages/JamiiWalletPage";
import SendMoneyPage from "@/app/jamiiwallet/pages/SendMoneyPage";
import CashOutPage from "@/app/jamiiwallet/pages/CashOutPage";
import BillPayPage from "@/app/billpay/pages/BillPayPage";
import PropertyListPage from "@/app/realestate/pages/PropertyListPage";
import PropertyDetailPage from "@/app/realestate/pages/PropertyDetailPage";
import MyPropertiesPage from "@/app/realestate/pages/MyPropertiesPage";
import MyInquiriesPage from "@/app/realestate/pages/MyInquiriesPage";
import RequestHarvestPage from "@/app/agriculture/pages/RequestHarvestPage";
import RequestProjectPage from "@/app/construction/pages/RequestProjectPage";
import SavingsGroupsPage from "@/app/savings/pages/SavingsGroupsPage";
import SavingsGroupDetailPage from "@/app/savings/pages/SavingsGroupDetailPage";
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
        <Route path="/homepage/:ownerType/:ownerId" element={<PublicHomePage />} />
        <Route path="/homepage/manage/:ownerType/:ownerId" element={<ProtectedRoute><MainLayout><HomepageManagerPage /></MainLayout></ProtectedRoute>} />

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
        <Route path="/institutions/:id/public" element={<MainLayout><InstitutionStorefrontPage /></MainLayout>} />
        {/* /kiini/dashboard* zinashughulikiwa na generateDynamicRoutes() (modulePages.kiini)
            chini - ziliondolewa hapa ili zisigongane na routes hizo hizo. */}

        {/* Business Routes */}
        <Route path="/businesses/register/" element={<ProtectedRoute><MainLayout><BusinessRegistrationPage /></MainLayout></ProtectedRoute>} />
        <Route path="/store/:id" element={<MainLayout><BusinessStorefrontPage /></MainLayout>} />
        <Route path="/realestate" element={<MainLayout><PropertyListPage /></MainLayout>} />
        <Route path="/realestate/mine" element={<ProtectedRoute><MainLayout><MyPropertiesPage /></MainLayout></ProtectedRoute>} />
        <Route path="/realestate/inquiries/mine" element={<ProtectedRoute><MainLayout><MyInquiriesPage /></MainLayout></ProtectedRoute>} />
        <Route path="/realestate/:id" element={<MainLayout><PropertyDetailPage /></MainLayout>} />
        <Route path="/request-harvest" element={<ProtectedRoute><MainLayout><RequestHarvestPage /></MainLayout></ProtectedRoute>} />
        <Route path="/request-project" element={<ProtectedRoute><MainLayout><RequestProjectPage /></MainLayout></ProtectedRoute>} />

        {/* Cart / Checkout Routes */}
        <Route path="/cart" element={<MainLayout><CartPage /></MainLayout>} />
        <Route path="/checkout" element={<ProtectedRoute><MainLayout><CheckoutPage /></MainLayout></ProtectedRoute>} />

        {/* Item Request Routes */}
        <Route path="/request-item" element={<ProtectedRoute><MainLayout><RequestItemPage /></MainLayout></ProtectedRoute>} />
        <Route path="/request-import" element={<ProtectedRoute><MainLayout><RequestImportPage /></MainLayout></ProtectedRoute>} />
        <Route path="/request-item/:id/waiting" element={<ProtectedRoute><MainLayout><WaitingForClaimPage /></MainLayout></ProtectedRoute>} />
        <Route path="/request-item/:id/claimed" element={<ProtectedRoute><MainLayout><ClaimedConfirmationPage /></MainLayout></ProtectedRoute>} />

        {/* Order Tracking Routes */}
        <Route path="/orders" element={<ProtectedRoute><MainLayout><OrdersListPage /></MainLayout></ProtectedRoute>} />
        <Route path="/offers/mine" element={<ProtectedRoute><MainLayout><MyOffersPage /></MainLayout></ProtectedRoute>} />
        <Route path="/orders/:id" element={<ProtectedRoute><MainLayout><OrderDetailPage /></MainLayout></ProtectedRoute>} />

        {/* Logistics (Driver) Routes */}
        <Route path="/logistics/jobs" element={<ProtectedRoute><MainLayout><AvailableDeliveryJobsPage /></MainLayout></ProtectedRoute>} />
        <Route path="/logistics/request" element={<ProtectedRoute><MainLayout><RequestServicePage /></MainLayout></ProtectedRoute>} />
        <Route path="/logistics/deliveries" element={<ProtectedRoute><MainLayout><MyDeliveriesPage /></MainLayout></ProtectedRoute>} />
        <Route path="/logistics/verify" element={<ProtectedRoute><MainLayout><DriverVerificationPage /></MainLayout></ProtectedRoute>} />

        {/* Identity Verification */}
        <Route path="/verify-identity" element={<ProtectedRoute><MainLayout><VerifyIdentityPage /></MainLayout></ProtectedRoute>} />

        {/* Payments Routes */}
        <Route path="/payments/audit-logs/" element={<ProtectedRoute><MainLayout><div>Audit Logs</div></MainLayout></ProtectedRoute>} />
        <Route path="/payments/invoices/" element={<ProtectedRoute><MainLayout><InvoicesPage /></MainLayout></ProtectedRoute>} />
        <Route path="/businesses/credit-account" element={<ProtectedRoute><MainLayout><CreditAccountPage /></MainLayout></ProtectedRoute>} />
        <Route path="/payments/payment-methods/" element={<ProtectedRoute><MainLayout><PaymentMethodsPage /></MainLayout></ProtectedRoute>} />
        <Route path="/payments/payment-reports/" element={<ProtectedRoute><MainLayout><PaymentReportsPage /></MainLayout></ProtectedRoute>} />

        {/* Chat Routes */}
        <Route path="/jamiichat" element={<ProtectedRoute><MainLayout><ConversationsListPage /></MainLayout></ProtectedRoute>} />
        <Route path="/jamiichat/:id" element={<ProtectedRoute><MainLayout><ChatDetailPage /></MainLayout></ProtectedRoute>} />

        {/* Security Routes */}
        <Route path="/security/2fa/setup" element={<ProtectedRoute><MainLayout><Setup2FAPage /></MainLayout></ProtectedRoute>} />


        {/* Jamiiwallet Routes */}
        <Route path="/jamiiwallet" element={<ProtectedRoute><MainLayout><JamiiWalletPage /></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/send" element={<ProtectedRoute><MainLayout><SendMoneyPage /></MainLayout></ProtectedRoute>} />
        <Route path="/jamiiwallet/cash-out" element={<ProtectedRoute><MainLayout><CashOutPage /></MainLayout></ProtectedRoute>} />
        <Route path="/billpay" element={<ProtectedRoute><MainLayout><BillPayPage /></MainLayout></ProtectedRoute>} />
        <Route path="/savings" element={<ProtectedRoute><MainLayout><SavingsGroupsPage /></MainLayout></ProtectedRoute>} />
        <Route path="/savings/:id" element={<ProtectedRoute><MainLayout><SavingsGroupDetailPage /></MainLayout></ProtectedRoute>} />
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