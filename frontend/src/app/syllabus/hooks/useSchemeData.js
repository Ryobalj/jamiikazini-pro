// src/app/syllabus/hooks/useSchemeData.js
import { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useLocation } from "react-router-dom";
import { toast } from "react-toastify";
import api from "@/lib/axios";

export default function useSchemeData() {
  const { t } = useTranslation("syllabus");
  const location = useLocation();

  /* ===================== STATES ===================== */
  const [timetableSubjects, setTimetableSubjects] = useState([]);
  const [calendars, setCalendars] = useState([]);

  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedCalendar, setSelectedCalendar] = useState("");

  const [schemeData, setSchemeData] = useState(null);
  const [prefillData, setPrefillData] = useState(null);

  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  const [previewMode, setPreviewMode] = useState(false);
  const [error, setError] = useState(null);

  /* ===================== DERIVED ===================== */
  const hasSubjects = timetableSubjects.length > 0;
  const isFormValid = Boolean(selectedSubject && selectedCalendar);

  const selectedSubjectInfo = useMemo(
    () => timetableSubjects.find(s => s.id === selectedSubject),
    [timetableSubjects, selectedSubject]
  );

  const selectedCalendarInfo = useMemo(
    () => calendars.find(c => c.id === selectedCalendar),
    [calendars, selectedCalendar]
  );

  /* ===================== TRANSFORM ===================== */
  const transformTimetableData = useCallback(
    (data = []) =>
      data.map(subject => ({
        id: subject.subject_version,
        name: subject.subject_name,
        code: subject.subject_code,
        className:
          subject.class_level_name || subject.class_level_display,
        periods_per_week: subject.periods_per_week || 1,
        syllabus_year: subject.syllabus_year,
        is_english: !!subject.is_english,
        is_awali: !!subject.is_awali,
        teacher_name:
          subject.teacher_name || t("lesson_plan.teacher_name")
      })),
    [t]
  );

  /* ===================== PREFILL ===================== */
  useEffect(() => {
    const stored = localStorage.getItem("schemeSubjectData");

    if (stored) {
      try {
        setPrefillData(JSON.parse(stored));
        localStorage.removeItem("schemeSubjectData");
        toast.info(t("scheme.data_prefilled"));
      } catch {}
    }

    if (location.state?.subjectData) {
      setPrefillData(location.state.subjectData);
      toast.success(t("scheme.data_prefilled"));
    }
  }, [location, t]);

  /* ===================== AUTO SELECT ===================== */
  const autoSelectData = useCallback(
    (subjects, calendarList) => {
      if (!prefillData) return;

      const match = subjects.find(
        s =>
          s.id === prefillData.subject_version_id ||
          (
            s.name === prefillData.subject_name &&
            s.className === prefillData.class_level
          )
      );

      if (match) {
        setSelectedSubject(match.id);

        const latestCalendar = calendarList.reduce(
          (a, b) => (b.year > (a?.year || 0) ? b : a),
          null
        );

        if (latestCalendar) {
          setSelectedCalendar(latestCalendar.id);
        }
      }
    },
    [prefillData]
  );

  /* ===================== INITIAL FETCH ===================== */
  const fetchInitialData = useCallback(async () => {
    try {
      setInitialLoading(true);
      setError(null);

      const [tt, cal] = await Promise.all([
        api.get("/syllabus/timetables/"),
        api.get("/syllabus/annual-calendars/")
      ]);

      const transformedSubjects = transformTimetableData(tt.data || []);

      setTimetableSubjects(transformedSubjects);
      setCalendars(cal.data || []);

      autoSelectData(transformedSubjects, cal.data || []);
    } catch {
      const msg = t("errors.failed_to_load");
      setError(msg);
      toast.error(msg);
    } finally {
      setInitialLoading(false);
    }
  }, [autoSelectData, transformTimetableData, t]);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  /* ===================== ERROR HANDLER ===================== */
  const handleApiError = useCallback(
    err => {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        t("scheme.error_generic");

      setError(msg);
      toast.error(msg);
    },
    [t]
  );

  /* ===================== PREVIEW ===================== */
  const handlePreviewScheme = useCallback(
    async (language = "sw") => {
      if (!isFormValid) {
        toast.warning(t("scheme.select_subject_and_calendar"));
        return;
      }

      setPreviewLoading(true);
      setSchemeData(null);
      setError(null);

      try {
        const res = await api.post("/syllabus/schemes/preview/", {
          subject_version_id: Number(selectedSubject),
          annual_calendar_id: Number(selectedCalendar),
          language,
          balance_weekly: true
        });

        setSchemeData(res.data);
        setPreviewMode(true);
        toast.success(t("scheme.preview_generated"));
      } catch (err) {
        handleApiError(err);
      } finally {
        setPreviewLoading(false);
      }
    },
    [isFormValid, selectedSubject, selectedCalendar, handleApiError, t]
  );

  /* ===================== FULL SCHEME ===================== */
  const handleFetchScheme = useCallback(
    async (language = "sw") => {
      if (!isFormValid) {
        toast.warning(t("scheme.select_subject_and_calendar"));
        return;
      }

      setLoading(true);
      setSchemeData(null);
      setPreviewMode(false);
      setError(null);

      try {
        const res = await api.post("/syllabus/schemes/", {
          subject_version_id: Number(selectedSubject),
          annual_calendar_id: Number(selectedCalendar),
          language,
          balance_weekly: true
        });

        setSchemeData(res.data);
        toast.success(t("scheme.generated_success"));
      } catch (err) {
        if (err.response?.status === 500) {
          try {
            const fallback = await api.post("/syllabus/schemes/preview/", {
              subject_version_id: Number(selectedSubject),
              annual_calendar_id: Number(selectedCalendar),
              language,
              balance_weekly: true
            });

            setSchemeData({
              ...fallback.data,
              _preview: { is_preview: false }
            });

            toast.success(t("scheme.generated_success"));
            return;
          } catch {}
        }

        handleApiError(err);
      } finally {
        setLoading(false);
      }
    },
    [isFormValid, selectedSubject, selectedCalendar, handleApiError, t]
  );

  /* ===================== PDF ===================== */
  const handleDownloadPDF = useCallback(
    async (language = "sw") => {
      if (!schemeData) {
        toast.warning(t("scheme.generate_first"));
        return;
      }

      setPdfLoading(true);

      try {
        const res = await api.post(
          "/syllabus/schemes/pdf/",
          {
            subject_version_id: Number(selectedSubject),
            annual_calendar_id: Number(selectedCalendar),
            language,
            balance_weekly: true
          },
          { responseType: "blob", timeout: 60000 }
        );

        const blob = new Blob([res.data], { type: "application/pdf" });
        const url = URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = `Scheme_${selectedSubjectInfo?.name}_${selectedCalendarInfo?.year}.pdf`;
        a.click();

        URL.revokeObjectURL(url);
        toast.success(t("scheme.pdf_downloaded"));
      } catch (err) {
        handleApiError(err);
      } finally {
        setPdfLoading(false);
      }
    },
    [
      schemeData,
      selectedSubject,
      selectedCalendar,
      selectedSubjectInfo,
      selectedCalendarInfo,
      handleApiError,
      t
    ]
  );

  /* ===================== CLEAR ===================== */
  const clearScheme = useCallback(() => {
    setSelectedSubject("");
    setSelectedCalendar("");
    setSchemeData(null);
    setPreviewMode(false);
    setError(null);
    toast.info(t("common.cleared"));
  }, [t]);

  /* ===================== RETURN ===================== */
  return {
    timetableSubjects,
    calendars,

    selectedSubject,
    setSelectedSubject,
    selectedCalendar,
    setSelectedCalendar,

    schemeData,
    loading,
    previewLoading,
    pdfLoading,
    initialLoading,
    error,
    previewMode,

    hasSubjects,
    isFormValid,
    selectedSubjectInfo,
    selectedCalendarInfo,

    fetchInitialData,
    handlePreviewScheme,
    handleFetchScheme,
    handleDownloadPDF,
    clearScheme
  };
}