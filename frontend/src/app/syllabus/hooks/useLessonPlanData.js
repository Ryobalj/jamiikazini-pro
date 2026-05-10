// src/app/syllabus/hooks/useLessonPlanData.js
import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import api from "@/lib/axios";
import { toast } from "react-toastify";
import LessonPlanStorage from "@/services/lessonPlanStorage";

export const useLessonPlanData = () => {
  const location = useLocation();
  
  // States
  const [workstations, setWorkstations] = useState([]);
  const [timetables, setTimetables] = useState([]);
  const [selectedTimetable, setSelectedTimetable] = useState(null);
  const [form, setForm] = useState({
    date: new Date().toISOString().split('T')[0],
    period: 1,
    timestart: "08:00",
    timefinish: "08:40",
    boys_attended: "",
    girls_attended: "",
    is_song: false,
    repeat_next: false,
    managed_count: "",
  });
  const [initialLoading, setInitialLoading] = useState(true);
  const [prefillData, setPrefillData] = useState(null);
  const [workstationModalOpen, setWorkstationModalOpen] = useState(false);
  const [timetableModalOpen, setTimetableModalOpen] = useState(false);
  const [error, setError] = useState(null);

  // Computed values
  const currentSubjectInfo = selectedTimetable ? {
    subject: selectedTimetable.subject_name,
    class: selectedTimetable.class_level_name,
    periods: selectedTimetable.periods_per_week,
    registeredBoys: selectedTimetable.registeredboys || 0,
    registeredGirls: selectedTimetable.registeredgirls || 0,
    totalStudents: (selectedTimetable.registeredboys || 0) + (selectedTimetable.registeredgirls || 0)
  } : null;

  const showWorkstationModal = !initialLoading && workstations.length === 0;
  const showTimetableModal = !initialLoading && workstations.length > 0 && timetables.length === 0;
  const canUsePage = workstations.length > 0 && timetables.length > 0;

  // Effects
  useEffect(() => {
    // Load prefill data
    const storedData = localStorage.getItem('lessonPlanSubjectData');
    if (storedData) {
      try {
        const data = JSON.parse(storedData);
        setPrefillData(data);
        LessonPlanStorage.saveAutoFilledData(data);
        localStorage.removeItem('lessonPlanSubjectData');
      } catch (err) {
        console.error("Failed to parse stored lesson plan data:", err);
      }
    }

    if (location.state?.subjectData) {
      setPrefillData(location.state.subjectData);
      LessonPlanStorage.saveAutoFilledData(location.state.subjectData);
    }
  }, [location]);

  useEffect(() => {
    const loadInitial = async () => {
      try {
        setInitialLoading(true);

        // Load workstations
        const wsRes = await api.get("/syllabus/teacher-workstations/");
        setWorkstations(Array.isArray(wsRes.data) ? wsRes.data : []);

        // Load timetables
        const ttRes = await api.get("/syllabus/timetables/");
        const ttData = Array.isArray(ttRes.data) ? ttRes.data : [];
        setTimetables(ttData);

        // Handle prefill data
        if (prefillData && ttData.length > 0) {
          const matchingTimetable = ttData.find(timetable => 
            timetable.subject_version === prefillData.subject_version ||
            (timetable.subject_name === prefillData.subject_name && timetable.class_level_name === prefillData.class_level)
          );
          
          if (matchingTimetable) {
            setSelectedTimetable(matchingTimetable);
            setForm(prev => ({
              ...prev,
              boys_attended: prefillData.registered_boys || "",
              girls_attended: prefillData.registered_girls || "",
            }));
            
            toast.success("Data prefilled successfully", {
              position: "bottom-right",
              autoClose: 3000,
            });
          }
        }
      } catch {
        setError("Failed to load data");
      } finally {
        setInitialLoading(false);
      }
    };

    loadInitial();
  }, [prefillData]);

  return {
    workstations,
    timetables,
    selectedTimetable,
    setSelectedTimetable,
    form,
    setForm,
    initialLoading,
    prefillData,
    currentSubjectInfo,
    canUsePage,
    showWorkstationModal,
    showTimetableModal,
    workstationModalOpen,
    setWorkstationModalOpen,
    timetableModalOpen,
    setTimetableModalOpen,
    error,
    setError
  };
};