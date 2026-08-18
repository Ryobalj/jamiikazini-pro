// src/app/syllabus/components/SyllabusWorkstationGuard.jsx
import React, { useEffect, useState } from "react";
import api from "@/lib/axios";
import WorkstationFormModal from "./WorkstationFormModal";

/**
 * Wraps a syllabus product page. If the teacher has no workstation set up
 * yet, shows the workstation setup form instead of mounting the page
 * (so the page's own data-fetching never runs against a missing workstation).
 */
export default function SyllabusWorkstationGuard({ children }) {
  const [state, setState] = useState({ checking: true, hasWorkstation: false });

  useEffect(() => {
    let cancelled = false;

    api
      .get("/syllabus/teacher-workstations/")
      .then((res) => {
        if (cancelled) return;
        setState({ checking: false, hasWorkstation: (res.data?.length || 0) > 0 });
      })
      .catch(() => {
        if (cancelled) return;
        setState({ checking: false, hasWorkstation: false });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (state.checking) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!state.hasWorkstation) {
    return (
      <WorkstationFormModal
        open={true}
        onSubmit={() => setState({ checking: false, hasWorkstation: true })}
      />
    );
  }

  return children;
}
