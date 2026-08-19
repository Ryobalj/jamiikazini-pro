// src/app/syllabus/components/SyllabusWorkstationGuard.jsx
import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import WorkstationFormModal from "./WorkstationFormModal";

/**
 * Wraps a syllabus product page. If the teacher has no workstation set up
 * yet, shows the workstation setup form instead of mounting the page
 * (so the page's own data-fetching never runs against a missing workstation).
 *
 * When `requireTimetable` is true, a second gate applies after the
 * workstation check: the teacher must also have at least one timetable
 * entry (see TimeTable model) before the page mounts. This is used by
 * Scheme of Work and Lesson Plan, which are only meaningful for subjects
 * the teacher has actually put on their timetable - School/Class
 * Timetable and Exam Reports register subjects independently and don't
 * pass this prop.
 */
export default function SyllabusWorkstationGuard({ children, requireTimetable = false }) {
  const { t } = useTranslation("syllabus");
  const navigate = useNavigate();
  const [state, setState] = useState({ checking: true, hasWorkstation: false, hasTimetable: true });

  useEffect(() => {
    let cancelled = false;

    api
      .get("/syllabus/teacher-workstations/")
      .then((res) => {
        if (cancelled) return;
        const hasWorkstation = (res.data?.length || 0) > 0;

        if (!hasWorkstation || !requireTimetable) {
          setState({ checking: false, hasWorkstation, hasTimetable: true });
          return;
        }

        api
          .get("/syllabus/timetables/")
          .then((ttRes) => {
            if (cancelled) return;
            setState({
              checking: false,
              hasWorkstation: true,
              hasTimetable: (ttRes.data?.length || 0) > 0,
            });
          })
          .catch(() => {
            if (cancelled) return;
            setState({ checking: false, hasWorkstation: true, hasTimetable: false });
          });
      })
      .catch(() => {
        if (cancelled) return;
        setState({ checking: false, hasWorkstation: false, hasTimetable: true });
      });

    return () => {
      cancelled = true;
    };
  }, [requireTimetable]);

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
        onSubmit={() => setState((prev) => ({ ...prev, hasWorkstation: true }))}
      />
    );
  }

  if (requireTimetable && !state.hasTimetable) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-auto">
        <div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded-lg p-6 w-full max-w-md shadow-lg text-center">
          <h2 className="text-lg font-semibold mb-3">{t("timetable.timetable_required")}</h2>
          <p className="mb-5 text-sm text-gray-600 dark:text-gray-300">
            {t("timetable.timetable_required_message")}
          </p>
          <button
            type="button"
            onClick={() => navigate("/teaching/timetable")}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
          >
            {t("timetable.go_to_timetable")}
          </button>
        </div>
      </div>
    );
  }

  return children;
}
