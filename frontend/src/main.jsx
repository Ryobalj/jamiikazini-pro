// src/main.jsx

import "./styles/globals.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { AppContextProvider } from "./context/AppContext";
import { CurrencyProvider } from "./context/CurrencyContext";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <AppContextProvider>
        <CurrencyProvider>
          <App />
        </CurrencyProvider>
      </AppContextProvider>
    </BrowserRouter>
  </StrictMode>
);