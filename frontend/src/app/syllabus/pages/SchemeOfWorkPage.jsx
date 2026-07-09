// src/app/syllabus/pages/SchemeOfWorkPage.jsx

import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useLocation } from "react-router-dom";
import { 
  ArrowLeft, 
  BookOpen, 
  Calendar, 
  RefreshCw,
  AlertCircle,
  CheckCircle
} from "lucide-react";
import { toast } from "react-toastify";
import api from "@/lib/axios";

// Components
import SchemePreview from "../components/SchemePreview";
import SchemeSelection from "../components/SchemeSelection";
import SchemeActions from "../components/SchemeActions";

export default function SchemeOfWorkPage() {
  const { t } = useTranslation("syllabus");
  const navigate = useNavigate();
  const location = useLocation();
  
  /* ===================== STATES ===================== */
  const [workstation, setWorkstation] = useState(null);
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
  
  const [, setPreviewMode] = useState(false);
  const [error, setError] = useState(null);
  
  const [viewMode, setViewMode] = useState("table");

  /* ===================== DERIVED VALUES ===================== */
  const hasWorkstation = !!workstation;
  const hasSubjects = timetableSubjects.length > 0;
  const isFormValid = Boolean(selectedSubject && selectedCalendar);
  
  const selectedSubjectInfo = timetableSubjects.find(s => s.id === selectedSubject);
  const selectedCalendarInfo = calendars.find(c => c.id === selectedCalendar);

  /* ===================== FETCH WORKSTATION ===================== */
  const fetchWorkstation = useCallback(async () => {
    try {
      const response = await api.get("/syllabus/teacher-workstations/");
      const data = Array.isArray(response.data) 
        ? response.data 
        : response.data?.results || [];
      
      console.log("Workstation data:", data);
      
      if (data.length > 0) {
        const userWorkstation = data[0];
        setWorkstation(userWorkstation);
        return userWorkstation;
      } else {
        setWorkstation(null);
        return null;
      }
    } catch (err) {
      console.error("Failed to fetch workstation:", err);
      setWorkstation(null);
      return null;
    }
  }, []);

  /* ===================== FETCH TIMETABLES ===================== */
  const fetchTimetables = useCallback(async (ws) => {
    if (!ws) {
      setTimetableSubjects([]);
      return [];
    }

    try {
      const response = await api.get("/syllabus/timetables/", {
        params: { 
          workstation: ws.id,
          ordering: "-created_at"
        }
      });
      
      const data = Array.isArray(response.data) 
        ? response.data 
        : response.data?.results || [];
      
      console.log("Timetables fetched:", data.length);
      
      // Transform to scheme format
      const subjects = [];
      const seenSubjects = new Set();
      
      data.forEach(timetable => {
        const subjectKey = `${timetable.subject_version}-${timetable.class_level_name}`;
        
        if (!seenSubjects.has(subjectKey)) {
          seenSubjects.add(subjectKey);
          
          subjects.push({
            id: timetable.subject_version,
            name: timetable.subject_name,
            code: timetable.subject_code,
            className: timetable.class_level_name || timetable.class_level_display,
            periods_per_week: timetable.periods_per_week || 1,
            syllabus_year: timetable.syllabus_year,
            is_english: !!timetable.is_english,
            is_awali: !!timetable.is_awali,
            teacher_name: timetable.teacher_name || t("lesson_plan.teacher_name"),
            workstation_id: timetable.workstation
          });
        }
      });
      
      setTimetableSubjects(subjects);
      return subjects;
    } catch (err) {
      console.error("Failed to fetch timetables:", err);
      setTimetableSubjects([]);
      return [];
    }
  }, [t]);

  /* ===================== FETCH CALENDARS ===================== */
  const fetchCalendars = useCallback(async () => {
    try {
      const response = await api.get("/syllabus/annual-calendars/");
      const data = Array.isArray(response.data) 
        ? response.data 
        : response.data?.results || [];
      
      console.log("Calendars fetched:", data.length);
      setCalendars(data);
      return data;
    } catch (err) {
      console.error("Failed to fetch calendars:", err);
      setCalendars([]);
      return [];
    }
  }, []);

  /* ===================== INITIAL DATA FETCH ===================== */
  const fetchInitialData = useCallback(async () => {
    try {
      setInitialLoading(true);
      setError(null);
      
      // 1. Fetch workstation
      const ws = await fetchWorkstation();
      
      if (!ws) {
        toast.warning(t("workstation.required_message"), {
          position: "bottom-right",
          autoClose: 5000,
        });
      }
      
      // 2. Fetch timetables and calendars in parallel
      await Promise.all([
        fetchTimetables(ws),
        fetchCalendars()
      ]);
      
    } catch (err) {
      console.error("Error in initial data fetch:", err);
      setError(t("errors.failed_to_load"));
      toast.error(t("errors.failed_to_load"), {
        position: "bottom-right",
        autoClose: 3000,
      });
    } finally {
      setInitialLoading(false);
    }
  }, [fetchWorkstation, fetchTimetables, fetchCalendars, t]);

  /* ===================== PREFILL FROM MYSUBJECTS ===================== */
  useEffect(() => {
    // Check for prefill data from MySubjects page
    const storedData = localStorage.getItem('schemeSubjectData');
    
    if (storedData) {
      try {
        const parsed = JSON.parse(storedData);
        setPrefillData(parsed);
        console.log("Prefill data from localStorage:", parsed);
        
        // Auto-select subject if found
        if (parsed.subject_version_id) {
          setSelectedSubject(parsed.subject_version_id);
        }
        
        localStorage.removeItem('schemeSubjectData');
        toast.info(t("scheme.data_prefilled"));
      } catch (err) {
        console.error("Failed to parse stored data:", err);
      }
    }
    
    // Also check location state
    if (location.state?.subjectData) {
      setPrefillData(location.state.subjectData);
      console.log("Prefill data from location state:", location.state.subjectData);
      
      if (location.state.subjectData.subject_version_id) {
        setSelectedSubject(location.state.subjectData.subject_version_id);
      }
      toast.success(t("scheme.data_prefilled"));
    }
  }, [location, t]);

  /* ===================== AUTO-SELECT FROM PREFILL ===================== */
  useEffect(() => {
    if (prefillData && prefillData.subject_version_id && timetableSubjects.length > 0) {
      // Find matching subject
      const match = timetableSubjects.find(s => 
        s.id === prefillData.subject_version_id ||
        (s.name === prefillData.subject_name && s.className === prefillData.class_level)
      );
      
      if (match) {
        setSelectedSubject(match.id);
        console.log("Auto-selected subject from prefill:", match);
      }
      
      // Auto-select latest calendar
      if (calendars.length > 0 && !selectedCalendar) {
        const latestCalendar = calendars.reduce((a, b) => 
          (b.year > (a?.year || 0) ? b : a)
        );
        
        if (latestCalendar) {
          setSelectedCalendar(latestCalendar.id);
          console.log("Auto-selected calendar:", latestCalendar);
        }
      }
    }
  }, [prefillData, timetableSubjects, calendars, selectedCalendar]);

  /* ===================== API ERROR HANDLER ===================== */
  const handleApiError = useCallback((err) => {
    console.error("API Error:", err.response?.data || err);
    
    const errorMsg = err.response?.data?.detail ||
                    err.response?.data?.message ||
                    err.response?.data?.error ||
                    t("scheme.error_generic");
    
    setError(errorMsg);
    toast.error(errorMsg, {
      position: "bottom-right",
      autoClose: 5000,
    });
  }, [t]);

  /* ===================== GENERATE SCHEME ===================== */
  const handleFetchScheme = useCallback(async (language = "sw") => {
    if (!isFormValid) {
      toast.warning(t("scheme.select_subject_and_calendar"));
      return;
    }
    
    if (!hasWorkstation) {
      toast.error(t("workstation.required_message"));
      return;
    }
    
    setLoading(true);
    setSchemeData(null);
    setPreviewMode(false);
    setError(null);
    
    console.log("Generating scheme with:", {
      subject_version_id: selectedSubject,
      annual_calendar_id: selectedCalendar,
      language,
      workstation: workstation?.id
    });
    
    try {
      const response = await api.post("/syllabus/schemes/", {
        subject_version_id: selectedSubject, // STRING ID
        annual_calendar_id: selectedCalendar, // STRING ID
        language: language || "sw",
        balance_weekly: true
      });
      
      console.log("Scheme generated:", response.data);
      setSchemeData(response.data);
      toast.success(t("scheme.generated_success"));
    } catch (err) {
      // Try preview as fallback
      if (err.response?.status === 500) {
        try {
          const previewResponse = await api.post("/syllabus/schemes/preview/", {
            subject_version_id: selectedSubject,
            annual_calendar_id: selectedCalendar,
            language: language || "sw",
            balance_weekly: true
          });
          
          setSchemeData({
            ...previewResponse.data,
            _preview: { is_preview: false }
          });
          
          toast.success(t("scheme.generated_success"));
          return;
        } catch (previewErr) {
          handleApiError(previewErr);
        }
      } else {
        handleApiError(err);
      }
    } finally {
      setLoading(false);
    }
  }, [isFormValid, hasWorkstation, selectedSubject, selectedCalendar, workstation, handleApiError, t]);

  /* ===================== PREVIEW SCHEME ===================== */
  const handlePreviewScheme = useCallback(async (language = "sw") => {
    if (!isFormValid) {
      toast.warning(t("scheme.select_subject_and_calendar"));
      return;
    }
    
    if (!hasWorkstation) {
      toast.error(t("workstation.required_message"));
      return;
    }
    
    setPreviewLoading(true);
    setSchemeData(null);
    setError(null);
    
    console.log("Generating preview with:", {
      subject_version_id: selectedSubject,
      annual_calendar_id: selectedCalendar,
      language
    });
    
    try {
      const response = await api.post("/syllabus/schemes/preview/", {
        subject_version_id: selectedSubject,
        annual_calendar_id: selectedCalendar,
        language: language || "sw",
        balance_weekly: true
      });
      
      setSchemeData(response.data);
      setPreviewMode(true);
      toast.success(t("scheme.preview_generated") || "Preview generated");
    } catch (err) {
      handleApiError(err);
    } finally {
      setPreviewLoading(false);
    }
  }, [isFormValid, hasWorkstation, selectedSubject, selectedCalendar, handleApiError, t]);

  /* ===================== DOWNLOAD PDF ===================== */
  const handleDownloadPDF = useCallback(async (language = "sw") => {
    if (!schemeData) {
      toast.warning(t("scheme.generate_first"));
      return;
    }
    
    if (!hasWorkstation) {
      toast.error(t("workstation.required_message"));
      return;
    }
    
    setPdfLoading(true);
    setError(null);
    
    try {
      const response = await api.post(
        "/syllabus/schemes/pdf/",
        {
          subject_version_id: selectedSubject,
          annual_calendar_id: selectedCalendar,
          language: language || "sw",
          balance_weekly: true
        },
        { 
          responseType: "blob",
          timeout: 60000 
        }
      );
      
      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      
      const subjectName = selectedSubjectInfo?.name || "Scheme";
      const year = selectedCalendarInfo?.year || new Date().getFullYear();
      const filename = `Scheme_${subjectName}_${year}.pdf`;
      
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      URL.revokeObjectURL(url);
      toast.success(t("scheme.pdf_downloaded"));
    } catch (err) {
      handleApiError(err);
    } finally {
      setPdfLoading(false);
    }
  }, [schemeData, hasWorkstation, selectedSubject, selectedCalendar, selectedSubjectInfo, selectedCalendarInfo, handleApiError, t]);

  /* ===================== CLEAR SCHEME ===================== */
  const clearScheme = useCallback(() => {
    setSelectedSubject("");
    setSelectedCalendar("");
    setSchemeData(null);
    setPreviewMode(false);
    setError(null);
    toast.info(t("common.cleared"));
  }, [t]);

  /* ===================== EFFECTS ===================== */
  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  /* ===================== RENDER ===================== */
  if (initialLoading) {
    return (
      <div className="flex flex-col justify-center items-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
        <span className="text-gray-600 dark:text-gray-300">{t("common.loading")}...</span>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-4 md:p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          title={t("common.back")}
        >
          <ArrowLeft size={20} className="text-gray-600 dark:text-gray-400" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t("scheme.title")}
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {t("scheme.subtitle")}
          </p>
          
          {/* Workstation Status */}
          <div className="mt-2 flex items-center gap-2">
            {hasWorkstation ? (
              <div className="flex items-center gap-1 text-sm text-green-600">
                <CheckCircle size={14} />
                <span>
                  {workstation.school_name} • {workstation.district}
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-sm text-red-600">
                <AlertCircle size={14} />
                <span>{t("workstation.required_message")}</span>
              </div>
            )}
          </div>
        </div>
        
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={fetchInitialData}
            disabled={loading || pdfLoading || previewLoading}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title={t("common.refresh")}
          >
            <RefreshCw size={18} className={`text-gray-600 dark:text-gray-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 mb-6">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="font-semibold text-red-700 dark:text-red-400 mb-1">
                {t("common.error")}
              </h3>
              <p className="text-red-600 dark:text-red-300 text-sm">{error}</p>
            </div>
            <button 
              onClick={() => setError(null)} 
              className="text-red-500 hover:text-red-700"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="space-y-6">
        {/* Selection Section */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <SchemeSelection
            schemeData={{
              timetableSubjects,
              calendars,
              selectedSubject,
              setSelectedSubject,
              selectedCalendar,
              setSelectedCalendar,
              selectedSubjectInfo,
              selectedCalendarInfo,
              fetchInitialData,
              loading,
              pdfLoading,
              setSchemeData,
              setPreviewMode
            }}
          />
        </div>

        {/* Status Indicators */}
        <div className="flex flex-wrap gap-4">
          <div className={`flex items-center gap-2 text-sm ${hasWorkstation ? 'text-green-600' : 'text-red-600'}`}>
            <div className={`w-2 h-2 rounded-full ${hasWorkstation ? 'bg-green-500' : 'bg-red-500'}`}></div>
            {hasWorkstation ? (
              <>
                <CheckCircle size={14} />
                <span>{t("workstation.active")}</span>
              </>
            ) : (
              <>
                <AlertCircle size={14} />
                <span>{t("workstation.not_found")}</span>
              </>
            )}
          </div>
          
          <div className={`flex items-center gap-2 text-sm ${hasSubjects ? 'text-green-600' : 'text-yellow-600'}`}>
            <div className={`w-2 h-2 rounded-full ${hasSubjects ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
            {hasSubjects ? (
              <>
                <BookOpen size={14} />
                <span>{timetableSubjects.length} {t("my_subjects.subjects")}</span>
              </>
            ) : (
              <>
                <AlertCircle size={14} />
                <span>{t("my_subjects.no_subjects")}</span>
              </>
            )}
          </div>
          
          <div className={`flex items-center gap-2 text-sm ${selectedSubject ? 'text-green-600' : 'text-gray-500'}`}>
            <div className={`w-2 h-2 rounded-full ${selectedSubject ? 'bg-green-500' : 'bg-gray-400'}`}></div>
            {selectedSubject ? t("scheme.requirement_subject") : t("scheme.select_subject")}
          </div>
          
          <div className={`flex items-center gap-2 text-sm ${selectedCalendar ? 'text-green-600' : 'text-gray-500'}`}>
            <div className={`w-2 h-2 rounded-full ${selectedCalendar ? 'bg-green-500' : 'bg-gray-400'}`}></div>
            {selectedCalendar ? t("scheme.requirement_calendar") : t("scheme.select_calendar")}
          </div>
        </div>

        {/* Actions */}
        <SchemeActions
          schemeData={{
            isFormValid,
            loading,
            pdfLoading,
            previewLoading,
            schemeInfo: { schemeData },
            handleFetchScheme,
            handlePreviewScheme,
            handleDownloadPDF,
            clearScheme,
            fetchInitialData
          }}
          viewMode={viewMode}
          setViewMode={setViewMode}
        />

        {/* Loading State */}
        {(loading || pdfLoading || previewLoading) && (
          <div className="flex flex-col items-center justify-center py-12 bg-white dark:bg-gray-800 rounded-xl border">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">
              {pdfLoading ? t("common.saving") : 
               previewLoading ? t("scheme.generating_preview") : 
               t("scheme.generating_scheme")}
            </p>
          </div>
        )}

        {/* Preview/Results */}
        {schemeData && (
          <SchemePreview
            schemeData={schemeData}
            viewMode={viewMode}
            onDownloadPDF={handleDownloadPDF}
            pdfLoading={pdfLoading}
          />
        )}

        {/* Empty States */}
        {!hasWorkstation && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-6 text-center">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {t("workstation.workstation_required")}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {t("workstation.required_message")}
            </p>
            <button 
              onClick={() => navigate('/teaching/my-subjects')}
              className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
            >
              {t("workstation.add_title")}
            </button>
          </div>
        )}
        
        {hasWorkstation && !hasSubjects && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6 text-center">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {t("my_subjects.empty_title")}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {t("my_subjects.empty_description")}
            </p>
            <button 
              onClick={() => navigate('/teaching/my-subjects')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              {t("my_subjects.add_timetable")}
            </button>
          </div>
        )}
        
        {!schemeData && hasWorkstation && hasSubjects && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-dashed border-gray-300 dark:border-gray-700 p-12 text-center">
            <h3 className="text-xl font-medium text-gray-900 dark:text-white mb-3">
              {t("scheme.no_scheme_generated")}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
              {t("scheme.select_subject_and_calendar_to_generate")}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}