// src/SubdomainStorefrontRouter.jsx
//
// Inaanzishwa na main.jsx pale hostname ni subdomain ya duka/taasisi
// (<domain>.jamiikazini.com), badala ya <App/> kamili. Inatafuta biashara au
// taasisi kwa domain hiyo, kisha inaonyesha njia ndogo tu (storefront, cart,
// checkout, login) zinazotumia components zilezile zilizopo tayari - hakuna
// kuiga upya, "*" yoyote isiyofahamika inaelekeza kwenye domain kuu.

import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Loader2, Frown } from "lucide-react";
import api from "@/lib/axios";

import MainLayout from "@/layouts/MainLayout";
import ProtectedRoute from "@/components/ProtectedRoute";
import Login from "@/pages/auth/Login";
import Register from "@/pages/auth/Register";
import CartPage from "@/app/cart/pages/CartPage";
import CheckoutPage from "@/app/cart/pages/CheckoutPage";
import BusinessStorefrontPage from "@/app/businesses/pages/BusinessStorefrontPage";
import InstitutionStorefrontPage from "@/app/kiini/pages/InstitutionStorefrontPage";

const CENTRAL_DOMAIN = import.meta.env.VITE_CENTRAL_DOMAIN || "jamiikazini.com";

function NotFoundVenue({ label }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 text-center bg-gray-50 dark:bg-gray-900">
      <Frown className="w-12 h-12 text-gray-400 mb-3" />
      <p className="text-gray-700 dark:text-gray-300 font-medium">
        Hakuna duka au taasisi kwa jina "{label}".
      </p>
      <a href={`https://${CENTRAL_DOMAIN}`} className="mt-4 text-sm text-purple-600 hover:underline">
        Rudi jamiikazini.com
      </a>
    </div>
  );
}

export default function SubdomainStorefrontRouter() {
  const [loading, setLoading] = useState(true);
  const [resolved, setResolved] = useState(null); // { type: "business" | "institution", id }

  useEffect(() => {
    const label = window.location.hostname.split(".")[0];

    api
      .get("/resolve-domain/", { params: { domain: label } })
      .then((res) => setResolved({ type: "business", id: res.data.id }))
      .catch(() =>
        api
          .get("/kiini/institutions/resolve-domain/", { params: { domain: label } })
          .then((res) => setResolved({ type: "institution", id: res.data.id }))
          .catch(() => setResolved({ type: "none" }))
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  if (!resolved || resolved.type === "none") {
    return <NotFoundVenue label={window.location.hostname.split(".")[0]} />;
  }

  const homeRedirect =
    resolved.type === "business" ? `/store/${resolved.id}` : `/institutions/${resolved.id}/public`;

  return (
    <Routes>
      <Route path="/" element={<Navigate to={homeRedirect} replace />} />
      <Route path="/store/:id" element={<MainLayout><BusinessStorefrontPage /></MainLayout>} />
      <Route path="/institutions/:id/public" element={<MainLayout><InstitutionStorefrontPage /></MainLayout>} />
      <Route path="/cart" element={<MainLayout><CartPage /></MainLayout>} />
      <Route path="/checkout" element={<ProtectedRoute><MainLayout><CheckoutPage /></MainLayout></ProtectedRoute>} />
      <Route path="/security/login" element={<Login />} />
      <Route path="/security/register" element={<Register />} />
      <Route path="*" element={<Navigate to={homeRedirect} replace />} />
    </Routes>
  );
}
