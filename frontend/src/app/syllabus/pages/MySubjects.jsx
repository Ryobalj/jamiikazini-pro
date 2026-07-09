// src/app/syllabus/pages/MySubjects.jsx

import React, { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { 
  Plus, 
  BookOpen, 
  Edit2, 
  Trash2, 
  AlertCircle, 
  RefreshCw, 
  CheckCircle, 
  FileText, 
  ClipboardList,
  Users,
  Calendar,
  FileCode,
  Eye,
  School,
  Download
} from "lucide-react";
import { toast } from "react-toastify";
import api from "@/lib/axios";

import WorkstationFormModal from "../components/WorkstationFormModal";
import TimetableFormModal from "../components/TimetableFormModal";
import WorkstationEditModal from "../components/WorkstationEditModal";

export default function MySubjects() {
  const { t } = useTranslation("syllabus");
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [initialLoading, setInitialLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const [subjects, setSubjects] = useState([]);
  const [timetables, setTimetables] = useState([]);
  const [workstation, setWorkstation] = useState(null);

  const [workstationModalOpen, setWorkstationModalOpen] = useState(false);
  const [workstationEditModalOpen, setWorkstationEditModalOpen] = useState(false);
  const [timetableModalOpen, setTimetableModalOpen] = useState(false);
  const [editingTimetable, setEditingTimetable] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  // ---------------------------
  // FETCH WORKSTATION
  // ---------------------------
  const fetchWorkstation = useCallback(async () => {
    try {
      const wsRes = await api.get("/syllabus/teacher-workstations/");
      const wsData = Array.isArray(wsRes.data) ? wsRes.data : wsRes.data?.results || [];
      
      console.log("Workstation data:", wsData);

      if (wsData.length === 0) {
        setWorkstationModalOpen(true);
        setWorkstation(null);
        return null;
      }

      const userWs = wsData[0];
      setWorkstation(userWs);
      return userWs;
    } catch (err) {
      console.error("Failed to fetch workstation:", err);
      setError(t("errors.failed_to_load"));
      return null;
    }
  }, [t]);

  // ---------------------------
  // FETCH TIMETABLES (REAL DATA FROM DATABASE)
  // ---------------------------
  const fetchTimetables = useCallback(async (ws) => {
    if (!ws) return;

    try {
      const timetableRes = await api.get("/syllabus/timetables/", {
        params: { 
          workstation: ws.id,
          ordering: "-created_at"
        }
      });
      
      const timetableData = Array.isArray(timetableRes.data) 
        ? timetableRes.data 
        : timetableRes.data?.results || [];
      
      console.log("Timetables fetched:", timetableData);
      setTimetables(timetableData);

      // Extract unique subjects from timetables with CORRECTED LOGIC
      const uniqueSubjects = [];
      const seenSubjects = new Set();
      
      // Object ya kukusanya periods per week per subject (KUTOKA SUBJECT MODEL)
      const periodsPerWeekPerSubject = {};
      // Object ya kukusanya class level data
      const classLevelData = {};
      
      timetableData.forEach(timetable => {
        const subjectName = timetable.subject_name;
        const subjectCode = timetable.subject_code;
        const allocatedPeriods = timetable.periods_per_week || 1;
        const classLevel = timetable.class_level_name || timetable.class_level_display;
        const syllabusYear = timetable.syllabus_year;
        const isEnglish = timetable.is_english || false;
        const isAwali = timetable.is_awali || false;
        const subjectVersionId = timetable.subject_version;
        
        // Data ya wavulana na wasichana kutoka timetable
        const registeredBoys = timetable.registeredboys || 0;
        const registeredGirls = timetable.registeredgirls || 0;

        if (subjectName && subjectVersionId) {
          const subjectKey = `${subjectVersionId}-${classLevel}`;
          
          // Store periods per week for this subject
          periodsPerWeekPerSubject[subjectKey] = allocatedPeriods;
          
          // Store class level data (students per class level)
          if (!classLevelData[classLevel]) {
            classLevelData[classLevel] = {
              boys: registeredBoys,
              girls: registeredGirls,
              total: registeredBoys + registeredGirls,
              subjects: new Set()
            };
          }
          classLevelData[classLevel].subjects.add(subjectKey);
          
          if (!seenSubjects.has(subjectKey)) {
            seenSubjects.add(subjectKey);
            
            const scheduledPeriods = timetableData.filter(t => 
              t.subject_version === subjectVersionId && 
              (t.class_level_name === classLevel || t.class_level_display === classLevel)
            ).length;
            
            uniqueSubjects.push({
              id: subjectVersionId,
              name: subjectName,
              code: subjectCode,
              class_level: classLevel,
              syllabus_year: syllabusYear,
              allocated_periods: allocatedPeriods,
              scheduled_periods: scheduledPeriods,
              is_english: isEnglish,
              is_awali: isAwali,
              timetable_id: timetable.id,
            });
          }
        }
      });

      // Add student data to each subject based on its class level
      const finalSubjects = uniqueSubjects.map(subject => {
        const classData = classLevelData[subject.class_level] || { boys: 0, girls: 0, total: 0 };
        
        return {
          ...subject,
          registered_boys: classData.boys,
          registered_girls: classData.girls,
          total_students: classData.total,
          current_timetable: {
            id: subject.timetable_id,
            registeredboys: classData.boys,
            registeredgirls: classData.girls,
            total_students: classData.total
          }
        };
      });

      console.log("Extracted subjects with corrected student counts:", finalSubjects);
      setSubjects(finalSubjects);

      // Show empty description ONLY if there are no timetables at all
      if (timetableData.length === 0) {
        toast.info(t("my_subjects.empty_description"), {
          position: "bottom-right",
          autoClose: 3000,
        });
      }

    } catch (err) {
      console.error("Failed to fetch timetables:", err);
      if (err.response?.status === 404) {
        setSubjects([]);
        setTimetables([]);
      } else {
        setError(t("errors.failed_to_load"));
        toast.error(t("errors.failed_to_load"), {
          position: "bottom-right",
          autoClose: 3000,
        });
      }
    }
  }, [t]);

  // ---------------------------
  // INITIAL DATA FETCH
  // ---------------------------
  const fetchInitialData = useCallback(async () => {
    setInitialLoading(true);
    setError(null);

    try {
      const ws = await fetchWorkstation();
      await fetchTimetables(ws);
    } catch (err) {
      console.error("Initial data fetch error:", err);
      setError(t("errors.failed_to_load"));
    } finally {
      setLoading(false);
      setInitialLoading(false);
    }
  }, [fetchWorkstation, fetchTimetables, t]);

  // ---------------------------
  // REFRESH DATA
  // ---------------------------
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchInitialData();
    setRefreshing(false);
    toast.success(t("common.refreshed"), {
      position: "bottom-right",
      autoClose: 2000,
    });
  };

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  // ---------------------------
  // WORKSTATION HANDLERS
  // ---------------------------
  const handleWorkstationSubmit = async (wsData) => {
    try {
      const response = await api.post("/syllabus/teacher-workstations/", wsData);
      const newWorkstation = response.data;
      
      setWorkstation(newWorkstation);
      setWorkstationModalOpen(false);
      
      toast.success(t("workstation.added_success"), {
        position: "bottom-right",
        autoClose: 3000,
      });
      
      await fetchTimetables(newWorkstation);
    } catch (err) {
      console.error("Failed to save workstation:", err);
      toast.error(err.response?.data?.detail || t("errors.failed_to_save"), {
        position: "bottom-right",
        autoClose: 3000,
      });
      throw err;
    }
  };

  const handleWorkstationUpdate = async (updatedWorkstation) => {
    setWorkstation(updatedWorkstation);
    setWorkstationEditModalOpen(false);
    
    toast.success(t("workstation.updated_success"), {
      position: "bottom-right",
      autoClose: 3000,
    });
    
    // Refresh data to get updated workstation info
    await fetchInitialData();
  };

  // ---------------------------
  // TIMETABLE HANDLERS
  // ---------------------------
  const handleTimetableSubmit = async (timetableData, isEdit = false) => {
    try {
      let response;
      
      // Prepare data - send null for optional fields
      const submitData = {
        workstation: timetableData.workstation,
        subject_version: timetableData.subject_version,
        registeredboys: timetableData.registeredboys || null,
        registeredgirls: timetableData.registeredgirls || null,
        status: Boolean(timetableData.status),
        period: null,
        timestart: null,
        timefinish: null
      };
      
      if (isEdit && editingTimetable) {
        response = await api.put(`/syllabus/timetables/${editingTimetable.id}/`, submitData);
        toast.success(t("common.update_success"), {
          position: "bottom-right",
          autoClose: 3000,
        });
      } else {
        response = await api.post("/syllabus/timetables/", submitData);
        toast.success(t("common.create_success"), {
          position: "bottom-right",
          autoClose: 3000,
        });
      }
  
      // Refresh data
      await fetchTimetables(workstation);
      
      // Close modal
      setTimetableModalOpen(false);
      setEditingTimetable(null);
      
      return response.data;
    } catch (err) {
      console.error("Failed to save timetable:", err);
      
      console.log("Full error:", err.response?.data);
      
      const errorMsg = err.response?.data?.detail || 
                      err.response?.data?.message || 
                      JSON.stringify(err.response?.data) || 
                      t("errors.failed_to_save");
      
      toast.error(errorMsg, {
        position: "bottom-right",
        autoClose: 5000,
      });
      
      throw err;
    }
  };

  // ---------------------------
  // DELETE TIMETABLE
  // ---------------------------
  const handleDeleteTimetable = async (timetableId) => {
    if (!window.confirm(t("common.confirm_delete"))) return;

    setDeletingId(timetableId);
    
    try {
      await api.delete(`/syllabus/timetables/${timetableId}/`);
      
      // Refresh data instead of manual calculation
      await fetchTimetables(workstation);
      
      toast.success(t("common.delete_success"), {
        position: "bottom-right",
        autoClose: 3000,
      });
    } catch (err) {
      console.error("Failed to delete timetable:", err);
      toast.error(t("errors.failed_to_delete"), {
        position: "bottom-right",
        autoClose: 3000,
      });
    } finally {
      setDeletingId(null);
    }
  };

  // ==========================================
  // UPDATED: HANDLE GENERATE SCHEME
  // ==========================================
  const handleGenerateScheme = (subject) => {
    // Store subject data for scheme page - USING CORRECT BACKEND FORMAT
    const schemeData = {
      subject_version_id: subject.id, // MUST match backend expectation
      subject_name: subject.name,
      subject_code: subject.code,
      class_level: subject.class_level,
      syllabus_year: subject.syllabus_year,
      is_english: subject.is_english,
      is_awali: subject.is_awali,
      periods_per_week: subject.allocated_periods || 1,
      registered_boys: subject.registered_boys || 0,
      registered_girls: subject.registered_girls || 0,
      total_students: subject.total_students || 0,
      workstation_id: workstation?.id,
      workstation_name: workstation?.school_name,
      teacher_name: workstation?.teacher_name || t("lesson_plan.teacher_name")
    };
    
    // Save to localStorage for the scheme page to use
    localStorage.setItem('schemeSubjectData', JSON.stringify(schemeData));
    
    // Navigate to scheme page
    navigate('/teaching/scheme', { 
      state: {
        subjectData: schemeData,
        workstation: workstation
      }
    });
  };

  // ==========================================
  // UPDATED: HANDLE GENERATE LESSON PLAN
  // ==========================================
  const handleGenerateLessonPlan = (subject) => {
    // Store subject data for lesson plan page
    const lessonPlanData = {
      subject_version_id: subject.id, // MUST match backend expectation
      subject_name: subject.name,
      subject_code: subject.code,
      class_level: subject.class_level,
      registered_boys: subject.registered_boys || 0,
      registered_girls: subject.registered_girls || 0,
      total_students: subject.total_students || 0,
      allocated_periods: subject.allocated_periods || 1,
      syllabus_year: subject.syllabus_year,
      is_english: subject.is_english,
      is_awali: subject.is_awali,
      workstation_id: workstation?.id,
      workstation_name: workstation?.school_name,
      teacher_name: workstation?.teacher_name || t("lesson_plan.teacher_name")
    };
    
    // Save to localStorage for the lesson plan page to use
    localStorage.setItem('lessonPlanSubjectData', JSON.stringify(lessonPlanData));
    
    // Navigate to lesson plan page
    navigate('/teaching/lesson-plan', { 
      state: { subjectData: lessonPlanData }
    });
  };

  // ---------------------------
  // MODAL HANDLERS
  // ---------------------------
  const openEditModal = (subject) => {
    // Find the corresponding timetable
    const timetable = timetables.find(t => 
      t.id === subject.timetable_id ||
      t.subject_version === subject.id
    );
    
    if (timetable) {
      setEditingTimetable(timetable);
      setTimetableModalOpen(true);
    } else {
      console.error("No matching timetable found for subject:", subject);
      toast.error(t("errors.timetable_not_found"), {
        position: "bottom-right",
        autoClose: 3000,
      });
    }
  };

  const closeTimetableModal = () => {
    setTimetableModalOpen(false);
    setEditingTimetable(null);
  };

  // ---------------------------
  // COMPUTED VALUES
  // ---------------------------
  const hasWorkstation = !!workstation;
  const hasTimetables = timetables.length > 0;
  const hasSubjects = subjects.length > 0;
  
  // Calculate total scheduled periods
  const totalScheduledPeriods = timetables.length;
  
  // Calculate total allocated periods
  const totalAllocatedPeriods = subjects.reduce((sum, subject) => {
    return sum + (subject.allocated_periods || 0);
  }, 0);
  
  // Calculate period balance
  const totalPeriodBalance = totalAllocatedPeriods - totalScheduledPeriods;
  
  // Calculate unique class levels
  const uniqueClassLevels = [...new Set(subjects.map(s => s.class_level))];
  
  // Calculate total students per class level
  const studentsPerClassLevel = {};
  subjects.forEach(subject => {
    const classLevel = subject.class_level;
    if (!studentsPerClassLevel[classLevel]) {
      studentsPerClassLevel[classLevel] = {
        boys: subject.registered_boys || 0,
        girls: subject.registered_girls || 0,
        total: subject.total_students || 0
      };
    }
  });
  
  // Calculate total students across all classes
  const totalStudentsAll = Object.values(studentsPerClassLevel).reduce((sum, classData) => {
    return sum + (classData.total || 0);
  }, 0);
  
  // Calculate total boys and girls across all classes
  const totalBoysAll = Object.values(studentsPerClassLevel).reduce((sum, classData) => {
    return sum + (classData.boys || 0);
  }, 0);
  
  const totalGirlsAll = Object.values(studentsPerClassLevel).reduce((sum, classData) => {
    return sum + (classData.girls || 0);
  }, 0);
  
  // Calculate period balance per subject
  const subjectsWithBalance = subjects.map(subject => ({
    ...subject,
    period_balance: (subject.allocated_periods || 0) - (subject.scheduled_periods || 0)
  }));
  
  // Format workstation info
  const getWorkstationDisplay = () => {
    if (!workstation) return "";
    
    const parts = [];
    if (workstation.district) parts.push(workstation.district);
    if (workstation.ward) parts.push(workstation.ward);
    if (workstation.school_name) parts.push(workstation.school_name);
    
    return parts.join(" • ");
  };

  // ==========================================
  // NEW: HANDLE SCHEME PREVIEW (FOR TESTING)
  // ==========================================
  const handlePreviewScheme = async (subject) => {
    try {
      toast.info(t("scheme.generating_preview"), {
        position: "bottom-right",
        autoClose: 2000,
      });
      
      // Navigate with subject data
      handleGenerateScheme(subject);
    } catch (err) {
      console.error("Failed to preview scheme:", err);
      toast.error(t("errors.failed_to_load"), {
        position: "bottom-right",
        autoClose: 3000,
      });
    }
  };

  // ==========================================
  // NEW: HANDLE DEBUG MODE (FOR DEVELOPERS)
  // ==========================================
  const handleDebugData = () => {
    console.log("🔍 DEBUG DATA:", {
      subjects,
      timetables,
      workstation,
      hasWorkstation,
      hasSubjects,
      totalAllocatedPeriods,
      totalScheduledPeriods,
      totalPeriodBalance
    });
    
    toast.info(t("my_subjects.debug_data"), {
      position: "bottom-right",
      autoClose: 3000,
    });
  };

  // ---------------------------
  // RENDER
  // ---------------------------
  return (
    <div className="space-y-6 p-4 md:p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <BookOpen size={24} className="text-blue-600" />
            {t("my_subjects.title")}
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {t("my_subjects.subtitle")}
          </p>
          
          {/* Workstation Info with Edit Button */}
          {workstation && (
            <div className="mt-2 flex items-center justify-between bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
              <div className="flex items-center gap-2 text-sm">
                <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                <span className="text-gray-600 dark:text-gray-400">
                  {t("my_subjects.workstation_label")}:
                </span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {getWorkstationDisplay()}
                </span>
              </div>
              <button
                onClick={() => setWorkstationEditModalOpen(true)}
                className="inline-flex items-center gap-1 px-3 py-1 text-sm rounded-lg border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
              >
                <Edit2 size={14} />
                {t("common.edit")}
              </button>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={handleDebugData}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            title={t("my_subjects.debug_data")}
          >
            <FileCode size={16} />
            {t("common.debug")}
          </button>
          
          <button
            onClick={handleRefresh}
            disabled={refreshing || loading}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50 transition-colors"
          >
            <RefreshCw size={16} className={refreshing ? "animate-spin" : ""} />
            {t("common.refresh")}
          </button>
          
          {hasWorkstation && (
            <button
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
              onClick={() => setTimetableModalOpen(true)}
              disabled={loading}
            >
              <Plus size={16} />
              {t("my_subjects.add_timetable")}
            </button>
          )}
        </div>
      </div>

      {/* Loading State */}
      {(loading || initialLoading) && (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">{t("common.loading")}...</p>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="text-red-600 dark:text-red-400" size={20} />
            <div>
              <p className="font-medium text-red-700 dark:text-red-400">{error}</p>
              <button
                onClick={fetchInitialData}
                className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline"
              >
                {t("common.retry")}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Empty State - No Workstation */}
      {!loading && !error && !hasWorkstation && (
        <div className="flex flex-col items-center justify-center py-16 text-center border border-dashed border-gray-300 dark:border-gray-700 rounded-xl">
          <BookOpen size={48} className="mb-4 text-gray-400 dark:text-gray-500" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {t("my_subjects.empty_title")}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 max-w-md">
            {t("my_subjects.empty_description")}
          </p>
          <button
            className="mt-6 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            onClick={() => setWorkstationModalOpen(true)}
          >
            {t("workstation.add_title")}
          </button>
        </div>
      )}

      {/* Empty State - Has Workstation but NO TIMETABLES */}
      {!loading && !error && hasWorkstation && !hasTimetables && (
        <div className="flex flex-col items-center justify-center py-16 text-center border border-dashed border-gray-300 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-900/50">
          <BookOpen size={48} className="mb-4 text-gray-400 dark:text-gray-500" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {t("my_subjects.empty_title")}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 max-w-md mb-6">
            {t("my_subjects.empty_description")}
          </p>
          <button
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            onClick={() => setTimetableModalOpen(true)}
          >
            <Plus size={16} />
            {t("my_subjects.add_timetable")}
          </button>
        </div>
      )}

      {/* Data Inconsistency Warning */}
      {!loading && !error && hasWorkstation && hasTimetables && !hasSubjects && (
        <div className="flex flex-col items-center justify-center py-16 text-center border border-dashed border-yellow-300 dark:border-yellow-700 rounded-xl bg-yellow-50 dark:bg-yellow-900/20">
          <AlertCircle size={48} className="mb-4 text-yellow-500" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {t("my_subjects.data_inconsistency_title")}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 max-w-md mb-6">
            {t("my_subjects.data_inconsistency_description", { count: timetables.length })}
          </p>
          <div className="flex gap-3">
            <button
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              onClick={handleRefresh}
            >
              {t("common.refresh")}
            </button>
            <button
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              onClick={handleDebugData}
            >
              {t("my_subjects.debug_data")}
            </button>
          </div>
        </div>
      )}

      {/* Subjects Grid - SHOW IKIWA KUNA TIMETABLES */}
      {!loading && !error && hasTimetables && (
        <div className="space-y-6">
          {/* Stats Summary */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
                <BookOpen size={14} />
                {t("my_subjects.total_subjects")}
              </div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {hasSubjects ? subjects.length : timetables.length}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {t("my_subjects.total_periods")}: {totalScheduledPeriods}
                <span className={`ml-2 ${totalPeriodBalance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ({totalPeriodBalance >= 0 ? '+' : ''}{totalPeriodBalance})
                </span>
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {t("my_subjects.allocated_periods")}: {totalAllocatedPeriods}
              </div>
            </div>
            
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
                <Users size={14} />
                {t("my_subjects.total_students")}
              </div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {totalStudentsAll}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {t("my_subjects.boys")}: {totalBoysAll} • {t("my_subjects.girls")}: {totalGirlsAll}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {t("my_subjects.class")}: {uniqueClassLevels.length}
              </div>
            </div>
            
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 relative">
              <div className="absolute top-3 right-3">
                <button
                  onClick={() => setWorkstationEditModalOpen(true)}
                  className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
                  title={t("common.edit")}
                >
                  <Edit2 size={14} />
                </button>
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
                <School size={14} />
                {t("my_subjects.workstation")}
              </div>
              <div className="text-lg font-semibold text-gray-900 dark:text-white mt-1 truncate">
                {getWorkstationDisplay() || t("common.not_available")}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {workstation?.district || "—"}
              </div>
            </div>
            
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
                <Calendar size={14} />
                {t("common.status")}
              </div>
              <div className="flex items-center gap-2 mt-1">
                <CheckCircle size={16} className="text-green-500" />
                <span className="font-medium text-gray-900 dark:text-white">
                  {t("common.active")}
                </span>
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {workstation?.is_active ? t("workstation.active") : t("workstation.inactive")}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {t("my_subjects.periods_per_week")}: {totalAllocatedPeriods}
              </div>
            </div>
          </div>

          {/* Subjects List */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <BookOpen size={20} />
                  {t("my_subjects.my_subjects")} {hasSubjects ? `(${subjects.length})` : `(${t("common.loading")}...)`}
                </h2>
                <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
                  <Users size={14} />
                  {t("my_subjects.class")}: {uniqueClassLevels.length}
                </div>
              </div>
            </div>
            
            {hasSubjects ? (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {subjectsWithBalance.map((subject) => (
                  <div
                    key={`${subject.id}-${subject.class_level}`}
                    className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900 dark:text-white">
                              {subject.name}
                            </h3>
                            <div className="flex items-center gap-3 mt-1">
                              {subject.code && (
                                <span className="text-sm text-gray-500 dark:text-gray-400">
                                  {t("my_subjects.code")}: <span className="font-medium">{subject.code}</span>
                                </span>
                              )}
                              {subject.class_level && (
                                <span className="text-sm text-gray-500 dark:text-gray-400">
                                  {t("my_subjects.class")}: <span className="font-medium">{subject.class_level}</span>
                                </span>
                              )}
                              {subject.syllabus_year && (
                                <span className="text-sm text-gray-500 dark:text-gray-400">
                                  {t("my_subjects.syllabus")}: <span className="font-medium">{subject.syllabus_year}</span>
                                </span>
                              )}
                            </div>
                            
                            {/* Student Statistics Display */}
                            <div className="flex flex-wrap items-center gap-4 mt-3">
                              <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                                <span className="text-sm text-gray-600 dark:text-gray-400">
                                  <span className="font-semibold">{subject.registered_boys || 0}</span> {t("my_subjects.boys")}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-pink-500"></div>
                                <span className="text-sm text-gray-600 dark:text-gray-400">
                                  <span className="font-semibold">{subject.registered_girls || 0}</span> {t("my_subjects.girls")}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                                <span className="text-sm text-gray-600 dark:text-gray-400">
                                  <span className="font-semibold">{subject.total_students || 0}</span> {t("my_subjects.total_students")}
                                  <span className="ml-1 text-xs text-gray-500">({t("my_subjects.class")}: {subject.class_level})</span>
                                </span>
                              </div>
                            </div>
                            
                            {/* Period Information */}
                            <div className="flex flex-wrap items-center gap-4 mt-3">
                              <div className="text-sm text-gray-600 dark:text-gray-400">
                                {t("my_subjects.allocated_periods")}: 
                                <span className="font-semibold ml-1">{subject.allocated_periods || 0}</span>
                              </div>
                              <div className="text-sm text-gray-600 dark:text-gray-400">
                                {t("my_subjects.scheduled_periods")}: 
                                <span className="font-semibold ml-1">{subject.scheduled_periods || 0}</span>
                              </div>
                              <div className="text-sm text-gray-600 dark:text-gray-400">
                                {t("my_subjects.period_balance")}: 
                                <span className={`font-semibold ml-1 ${subject.period_balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                  {subject.period_balance}
                                </span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm font-medium">
                              {subject.allocated_periods} {t("my_subjects.periods_per_week")}
                            </span>
                          </div>
                        </div>
                        
                        {/* Subject Tags */}
                        <div className="flex flex-wrap gap-2 mt-3">
                          {subject.is_english && (
                            <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-xs font-medium">
                              {t("my_subjects.english_medium")}
                            </span>
                          )}
                          {subject.is_awali && (
                            <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-xs font-medium">
                              {t("my_subjects.early_childhood")}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      {/* Actions - UPDATED WITH BETTER BUTTONS */}
                      <div className="flex items-center gap-2">
                        {/* Preview Button */}
                        <button
                          onClick={() => handlePreviewScheme(subject)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                          title={t("common.preview")}
                        >
                          <Eye size={14} />
                          <span className="sr-only sm:not-sr-only sm:inline">{t("common.preview")}</span>
                        </button>
                        
                        {/* Edit Button */}
                        <button
                          onClick={() => openEditModal(subject)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                          disabled={deletingId === subject.timetable_id}
                          title={t("common.edit")}
                        >
                          <Edit2 size={14} />
                          <span className="sr-only sm:not-sr-only sm:inline">{t("common.edit")}</span>
                        </button>
                        
                        {/* Lesson Plan Button */}
                        <button
                          onClick={() => handleGenerateLessonPlan(subject)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                          title={t("my_subjects.generate_lesson_plan")}
                        >
                          <ClipboardList size={14} />
                          <span className="sr-only sm:not-sr-only sm:inline">{t("my_subjects.lesson_plan")}</span>
                        </button>
                        
                        {/* Scheme of Work Button */}
                        <button
                          onClick={() => handleGenerateScheme(subject)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
                          title={t("my_subjects.generate_scheme")}
                        >
                          <FileText size={14} />
                          <span className="sr-only sm:not-sr-only sm:inline">{t("my_subjects.scheme")}</span>
                        </button>
                        
                        {/* Delete Button */}
                        <button
                          onClick={() => handleDeleteTimetable(subject.timetable_id)}
                          disabled={deletingId === subject.timetable_id}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                          title={t("common.delete")}
                        >
                          {deletingId === subject.timetable_id ? (
                            <>
                              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-red-700"></div>
                              <span className="sr-only sm:not-sr-only sm:inline">{t("common.deleting")}</span>
                            </>
                          ) : (
                            <>
                              <Trash2 size={14} />
                              <span className="sr-only sm:not-sr-only sm:inline">{t("common.delete")}</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              // Show timetable entries directly if subjects extraction failed
              <div className="p-6 text-center">
                <AlertCircle size={32} className="mx-auto mb-4 text-yellow-500" />
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {t("my_subjects.cannot_group_subjects")}
                </p>
                <div className="space-y-3">
                  {timetables.slice(0, 5).map((timetable) => (
                    <div key={timetable.id} className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                      <div className="flex flex-col space-y-2">
                        {timetable.subject_name && (
                          <div className="font-medium">
                            {t("my_subjects.subject")}: {timetable.subject_name}
                          </div>
                        )}
                        {/* Show student counts */}
                        <div className="flex items-center gap-4 text-sm">
                          <span className="text-blue-600 dark:text-blue-400">
                            {t("my_subjects.boys")}: {timetable.registeredboys || 0}
                          </span>
                          <span className="text-pink-600 dark:text-pink-400">
                            {t("my_subjects.girls")}: {timetable.registeredgirls || 0}
                          </span>
                          <span className="text-green-600 dark:text-green-400">
                            {t("my_subjects.total")}: {(timetable.registeredboys || 0) + (timetable.registeredgirls || 0)}
                          </span>
                        </div>
                        <div className="text-sm text-gray-500">
                          {t("my_subjects.timetable_id")}: {timetable.id}
                        </div>
                      </div>
                    </div>
                  ))}
                  {timetables.length > 5 && (
                    <div className="text-sm text-gray-500">
                      {t("my_subjects.more_entries", { count: timetables.length - 5 })}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modals */}
      <WorkstationFormModal
        open={workstationModalOpen}
        onClose={() => setWorkstationModalOpen(false)}
        onSubmit={handleWorkstationSubmit}
        initialData={workstation}
      />

      <TimetableFormModal
        open={timetableModalOpen}
        onClose={closeTimetableModal}
        onSubmit={handleTimetableSubmit}
        initialData={editingTimetable}
        workstations={workstation ? [workstation] : []}
        isEdit={!!editingTimetable}
      />

      <WorkstationEditModal
        open={workstationEditModalOpen}
        onClose={() => setWorkstationEditModalOpen(false)}
        workstation={workstation}
        onUpdate={handleWorkstationUpdate}
      />
    </div>
  );
}