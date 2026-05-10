// src/app/syllabus/hooks/useBackgroundLoading.js
import { useState, useCallback, useRef } from "react";
import api from "@/lib/axios";
import { toast } from "react-toastify";
import LessonPlanStorage from "@/services/lessonPlanStorage";

export const useBackgroundLoading = (timetables) => {
  const [backgroundLoading, setBackgroundLoading] = useState({
    loading: false,
    progress: 0,
    total: 0,
    completed: 0,
    errors: [],
    status: 'idle'
  });

  const abortControllers = useRef([]);

  const startSmartBackgroundLoading = useCallback(async (timetables) => {
    if (backgroundLoading.loading || timetables.length > 5) return;
    
    setBackgroundLoading(prev => ({
      ...prev,
      loading: true,
      progress: 0,
      total: timetables.length,
      completed: 0,
      errors: [],
      status: 'loading'
    }));

    const abortController = new AbortController();
    abortControllers.current.push(abortController);

    try {
      const batchSize = 2;
      const batches = [];
      
      for (let i = 0; i < timetables.length; i += batchSize) {
        batches.push(timetables.slice(i, i + batchSize));
      }

      for (const [batchIndex, batch] of batches.entries()) {
        if (abortController.signal.aborted) break;

        const batchPromises = batch.map(async (timetable) => {
          try {
            const cached = LessonPlanStorage.getCachedActivities(timetable.subject_version);
            if (cached && new Date() - new Date(cached.cachedAt) < 3600000) {
              return { success: true, timetableId: timetable.id, cached: true };
            }

            const laRes = await api.get("/syllabus/learning-activities/", {
              params: { subject_version: timetable.subject_version },
              signal: abortController.signal
            });
            
            const learningActivities = Array.isArray(laRes.data) ? laRes.data : [];
            
            const allSpecificActivities = [];
            const activitiesToLoad = learningActivities.slice(0, 3);
            
            for (const activity of activitiesToLoad) {
              try {
                const slaRes = await api.get("/syllabus/specific-learning-activities/", {
                  params: { learning_activity: activity.id },
                  signal: abortController.signal
                });
                
                if (Array.isArray(slaRes.data)) {
                  allSpecificActivities.push(...slaRes.data.slice(0, 5));
                }
              } catch (err) {
                console.warn(`Failed to load specific activities:`, err);
              }
            }

            LessonPlanStorage.cacheActivities(
              timetable.subject_version,
              learningActivities,
              allSpecificActivities
            );

            return { success: true, timetableId: timetable.id, cached: false };
          } catch (error) {
            return { success: false, timetableId: timetable.id, error: error.message };
          }
        });

        const results = await Promise.allSettled(batchPromises);
        
        const completed = (batchIndex + 1) * batchSize;
        setBackgroundLoading(prev => ({
          ...prev,
          progress: Math.min((completed / timetables.length) * 100, 100),
          completed: Math.min(completed, timetables.length),
          errors: [
            ...prev.errors,
            ...results
              .filter(r => r.status === 'fulfilled' && !r.value.success)
              .map(r => r.value)
          ]
        }));

        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      setBackgroundLoading(prev => ({
        ...prev,
        loading: false,
        status: 'completed'
      }));

      toast.success("Background loading completed", {
        position: "bottom-right",
        autoClose: 3000,
      });
    } catch (error) {
      setBackgroundLoading(prev => ({
        ...prev,
        loading: false,
        status: 'error',
        errors: [...prev.errors, { error: error.message }]
      }));
    } finally {
      abortControllers.current = abortControllers.current.filter(ac => ac !== abortController);
    }
  }, [backgroundLoading.loading]);

  const cancelBackgroundLoading = useCallback(() => {
    abortControllers.current.forEach(controller => controller.abort());
    abortControllers.current = [];
    
    setBackgroundLoading({
      loading: false,
      progress: 0,
      total: 0,
      completed: 0,
      errors: [],
      status: 'idle'
    });
    
    toast.info("Background loading cancelled", {
      position: "bottom-right",
      autoClose: 3000,
    });
  }, []);

  // Start loading when timetables change
  useState(() => {
    if (timetables.length > 0 && timetables.length <= 5) {
      startSmartBackgroundLoading(timetables);
    } else if (timetables.length > 5) {
      toast.info(`You have ${timetables.length} subjects. Activities will load when you select a subject.`, {
        position: "bottom-right",
        autoClose: 5000,
      });
    }
  });

  return {
    backgroundLoading,
    cancelBackgroundLoading
  };
};