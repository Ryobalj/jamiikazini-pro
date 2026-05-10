// src/app/syllabus/hooks/useLessonPlanSubmission.js
import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import Fuse from "fuse.js";
import api from "@/lib/axios";
import { toast } from "react-toastify";
import LessonPlanStorage from "@/services/lessonPlanStorage";

export const useLessonPlanSubmission = (selectedTimetable) => {
  const [learningActivities, setLearningActivities] = useState([]);
  const [specificActivities, setSpecificActivities] = useState([]);
  const [allSpecificActivities, setAllSpecificActivities] = useState([]);
  const [selectedLearningActivity, setSelectedLearningActivity] = useState(null);
  const [selectedSpecificActivity, setSelectedSpecificActivity] = useState(null);
  const [search, setSearch] = useState("");
  const [isLoadingActivities, setIsLoadingActivities] = useState(false);
  
  const abortControllers = useRef([]);

  // Filtered activities with fuzzy search
  const filteredActivities = useMemo(() => {
    if (!search) return specificActivities;
    
    const fuse = new Fuse(specificActivities, { 
      keys: ["name", "method"], 
      threshold: 0.4,
      includeScore: true 
    });
    
    return fuse.search(search).map((r) => r.item);
  }, [search, specificActivities]);

  // Load activities for selected timetable
  const loadActivitiesForTimetable = useCallback(async (timetableId) => {
    if (!selectedTimetable) return;

    const abortController = new AbortController();
    abortControllers.current.push(abortController);

    setIsLoadingActivities(true);
    setLearningActivities([]);
    setSpecificActivities([]);
    setAllSpecificActivities([]);
    setSelectedLearningActivity(null);
    setSelectedSpecificActivity(null);
    setSearch("");

    try {
      const cached = LessonPlanStorage.getCachedActivities(selectedTimetable.subject_version);
      
      if (cached) {
        setLearningActivities(cached.learningActivities);
        setAllSpecificActivities(cached.specificActivities);
        
        if (cached.learningActivities.length > 0) {
          const firstActivity = cached.learningActivities[0];
          setSelectedLearningActivity(firstActivity.id);
          
          const filteredSpecific = cached.specificActivities.filter(
            activity => activity.learning_activity === firstActivity.id
          );
          setSpecificActivities(filteredSpecific);
          
          if (filteredSpecific.length > 0) {
            setSelectedSpecificActivity(filteredSpecific[0].id);
          }
        }
      } else {
        const laRes = await api.get("/syllabus/learning-activities/", {
          params: { subject_version: selectedTimetable.subject_version },
          signal: abortController.signal
        });
        
        const activities = Array.isArray(laRes.data) ? laRes.data : [];
        setLearningActivities(activities);
        
        if (activities.length > 0) {
          const firstActivity = activities[0];
          setSelectedLearningActivity(firstActivity.id);
          
          const slaRes = await api.get("/syllabus/specific-learning-activities/", {
            params: { learning_activity: firstActivity.id },
            signal: abortController.signal
          });
          
          const specific = Array.isArray(slaRes.data) ? slaRes.data : [];
          setSpecificActivities(specific);
          setAllSpecificActivities(specific);
          
          if (specific.length > 0) {
            setSelectedSpecificActivity(specific[0].id);
          }
          
          LessonPlanStorage.cacheActivities(
            selectedTimetable.subject_version,
            activities,
            specific
          );
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') return;
      console.error("Failed to load activities:", error);
      toast.error("Failed to load activities", { position: "bottom-right" });
    } finally {
      setIsLoadingActivities(false);
      abortControllers.current = abortControllers.current.filter(ac => ac !== abortController);
    }
  }, [selectedTimetable]);

  // Load specific activities for selected learning activity
  const loadSpecificActivities = useCallback((learningActivityId) => {
    if (!learningActivityId || !allSpecificActivities.length) return;
    
    const filtered = allSpecificActivities.filter(activity => 
      activity.learning_activity === learningActivityId
    );
    setSpecificActivities(filtered);
    
    if (filtered.length > 0) {
      setSelectedSpecificActivity(filtered[0].id);
    } else {
      setSelectedSpecificActivity(null);
    }
  }, [allSpecificActivities]);

  // Load activities when timetable changes
  useEffect(() => {
    if (selectedTimetable) {
      loadActivitiesForTimetable(selectedTimetable.id);
    }
  }, [selectedTimetable, loadActivitiesForTimetable]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortControllers.current.forEach(controller => controller.abort());
      abortControllers.current = [];
    };
  }, []);

  return {
    learningActivities,
    specificActivities,
    selectedLearningActivity,
    selectedSpecificActivity,
    search,
    setSearch,
    filteredActivities,
    isLoadingActivities,
    setSelectedLearningActivity,
    setSelectedSpecificActivity,
    loadActivitiesForTimetable,
    loadSpecificActivities
  };
};