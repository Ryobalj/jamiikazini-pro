// src/routes/dynamicRoutes.jsx

import React from "react";
import { Route } from "react-router-dom";
import ProtectedRoute from "@/components/ProtectedRoute";
import LayoutWrapper from "@/layouts/LayoutWrapper";
import { modulePages } from "@/routes/modulePages";

export function generateDynamicRoutes() {
  console.log("🔥 modulePages received:", modulePages);

  return Object.entries(modulePages).map(([key, config]) => {
    console.log("➡️ processing module:", key, config);

    return (
      <Route
        key={key}
        path={config.path}
        element={
          <ProtectedRoute>
            <LayoutWrapper layout={config.layout} />
          </ProtectedRoute>
        }
      >
        {config.pages.map((p, i) => {
          if (p.index) {
            console.log("   🏠 index route:", p.element);
            return (
              <Route
                key={`index-${i}`}
                index
                element={p.element}
              />
            );
          }

          console.log("   📄 child route:", p.path, p.element);
          return (
            <Route
              key={p.path || i}
              path={p.path}
              element={p.element}
            />
          );
        })}
      </Route>
    );
  });
}