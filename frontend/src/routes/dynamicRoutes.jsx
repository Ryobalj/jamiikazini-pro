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

    // Auth is applied per-page, not once for the whole module: a page
    // needs `public: true` set explicitly to skip the login requirement
    // (e.g. the /teaching menu itself), everything else stays protected
    // exactly as before - this is additive/opt-in, so no existing page
    // changes behavior unless it's marked public.
    return (
      <Route
        key={key}
        path={config.path}
        element={<LayoutWrapper layout={config.layout} />}
      >
        {config.pages.map((p, i) => {
          const element = p.public ? p.element : <ProtectedRoute>{p.element}</ProtectedRoute>;

          if (p.index) {
            console.log("   🏠 index route:", p.element);
            return (
              <Route
                key={`index-${i}`}
                index
                element={element}
              />
            );
          }

          console.log("   📄 child route:", p.path, p.element);
          return (
            <Route
              key={p.path || i}
              path={p.path}
              element={element}
            />
          );
        })}
      </Route>
    );
  });
}