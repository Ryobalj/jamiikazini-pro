// src/main.jsx

import "./styles/globals.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import SubdomainStorefrontRouter from "./SubdomainStorefrontRouter.jsx";
import { AppContextProvider } from "./context/AppContext";
import { CurrencyProvider } from "./context/CurrencyContext";
import { CartProvider } from "./context/CartContext";

const CENTRAL_DOMAIN = import.meta.env.VITE_CENTRAL_DOMAIN || "jamiikazini.com";

// Kama hostname ni <domain>.jamiikazini.com (siyo www/api/app, siyo domain
// kuu yenyewe, siyo localhost/onrender.com preview), mtumiaji amefika kupitia
// subdomain ya duka/taasisi maalum - onyesha router ndogo ya storefront
// badala ya <App/> nzima yenye dashboard/menus zote.
function isVenueSubdomain(hostname) {
  if (hostname === CENTRAL_DOMAIN || hostname === `www.${CENTRAL_DOMAIN}`) return false;
  if (!hostname.endsWith(`.${CENTRAL_DOMAIN}`)) return false;
  const label = hostname.split(".")[0];
  return !["www", "api", "app"].includes(label);
}

const RootApp = isVenueSubdomain(window.location.hostname) ? SubdomainStorefrontRouter : App;

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <AppContextProvider>
        <CurrencyProvider>
          <CartProvider>
            <RootApp />
          </CartProvider>
        </CurrencyProvider>
      </AppContextProvider>
    </BrowserRouter>
  </StrictMode>
);