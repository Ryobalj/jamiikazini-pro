// src/services/lessonPlanStorage.js

const LessonPlanStorage = {
  // Cache key prefix
  PREFIX: 'jamiikazini_lesson_plan_',
  
  // Generate cache key
  _getKey(subjectVersionId) {
    return `${this.PREFIX}subject_${subjectVersionId}`;
  },
  
  // Get cached activities for a subject
  getCachedActivities(subjectVersionId) {
    try {
      const key = this._getKey(subjectVersionId);
      const cached = localStorage.getItem(key);
      return cached ? JSON.parse(cached) : null;
    } catch (error) {
      console.error('❌ Failed to get cached activities:', error);
      return null;
    }
  },
  
  // Cache activities for a subject
  cacheActivities(subjectVersionId, learningActivities, specificActivities = {}) {
    try {
      const key = this._getKey(subjectVersionId);
      const cacheData = {
        learningActivities,
        specificActivities,
        cachedAt: new Date().toISOString()
      };
      localStorage.setItem(key, JSON.stringify(cacheData));
      console.log(`📦 Cached ${learningActivities.length} learning activities for subject ${subjectVersionId}`);
    } catch (error) {
      console.error('❌ Failed to cache activities:', error);
    }
  },
  
  // Update specific activities cache
  updateSpecificActivitiesCache(subjectVersionId, learningActivityId, specificActivities) {
    try {
      const key = this._getKey(subjectVersionId);
      const existingCache = this.getCachedActivities(subjectVersionId);
      
      if (existingCache) {
        existingCache.specificActivities = existingCache.specificActivities || {};
        existingCache.specificActivities[learningActivityId] = specificActivities;
        existingCache.cachedAt = new Date().toISOString();
        
        localStorage.setItem(key, JSON.stringify(existingCache));
        console.log(`📦 Updated cache with ${specificActivities.length} specific activities for LA ${learningActivityId}`);
      } else {
        // Create new cache if doesn't exist
        this.cacheActivities(subjectVersionId, [], { [learningActivityId]: specificActivities });
      }
    } catch (error) {
      console.error('❌ Failed to update specific activities cache:', error);
    }
  },
  
  // ✅ ADD THIS METHOD: Save auto-filled data
  saveAutoFilledData(timetable, formData) {
    try {
      const key = `${this.PREFIX}auto_fill_${timetable?.id || 'default'}`;
      const autoFillData = {
        timetableId: timetable?.id,
        subjectVersionId: timetable?.subject_version,
        subjectName: timetable?.subject_name,
        classLevel: timetable?.class_level_name,
        formData: formData,
        savedAt: new Date().toISOString()
      };
      
      localStorage.setItem(key, JSON.stringify(autoFillData));
      console.log(`📦 Saved auto-fill data for timetable ${timetable?.id}`);
      
      // Also save to recent timetables
      this.addToRecentTimetables(timetable);
      
      return true;
    } catch (error) {
      console.error('❌ Failed to save auto-fill data:', error);
      return false;
    }
  },
  
  // ✅ ADD THIS METHOD: Get auto-filled data
  getAutoFilledData(timetableId) {
    try {
      const key = `${this.PREFIX}auto_fill_${timetableId || 'default'}`;
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('❌ Failed to get auto-fill data:', error);
      return null;
    }
  },
  
  // ✅ ADD THIS METHOD: Add to recent timetables
  addToRecentTimetables(timetable) {
    try {
      const key = `${this.PREFIX}recent_timetables`;
      const recent = JSON.parse(localStorage.getItem(key)) || [];
      
      // Remove if already exists
      const filtered = recent.filter(item => item.id !== timetable.id);
      
      // Add to beginning (max 5 items)
      filtered.unshift({
        id: timetable.id,
        subjectName: timetable.subject_name,
        classLevel: timetable.class_level_name,
        accessedAt: new Date().toISOString()
      });
      
      if (filtered.length > 5) {
        filtered.length = 5;
      }
      
      localStorage.setItem(key, JSON.stringify(filtered));
    } catch (error) {
      console.error('❌ Failed to add to recent timetables:', error);
    }
  },
  
  // ✅ ADD THIS METHOD: Get recent timetables
  getRecentTimetables() {
    try {
      const key = `${this.PREFIX}recent_timetables`;
      return JSON.parse(localStorage.getItem(key)) || [];
    } catch (error) {
      console.error('❌ Failed to get recent timetables:', error);
      return [];
    }
  },
  
  // Clear all session data
  clearSession() {
    try {
      // Remove all lesson plan cache
      const keysToRemove = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith(this.PREFIX)) {
          keysToRemove.push(key);
        }
      }
      
      keysToRemove.forEach(key => localStorage.removeItem(key));
      console.log(`🧹 Cleared ${keysToRemove.length} cached items`);
      
      return true;
    } catch (error) {
      console.error('❌ Failed to clear session:', error);
      return false;
    }
  },
  
  // Clear search history
  clearSearchHistory() {
    try {
      localStorage.removeItem(`${this.PREFIX}search_history`);
      return true;
    } catch (error) {
      console.error('❌ Failed to clear search history:', error);
      return false;
    }
  },
  
  // Add search to history
  addToSearchHistory(searchTerm, activityId) {
    try {
      const key = `${this.PREFIX}search_history`;
      const history = JSON.parse(localStorage.getItem(key)) || [];
      
      // Add new search (max 20 items)
      history.unshift({
        term: searchTerm,
        activityId: activityId,
        timestamp: new Date().toISOString()
      });
      
      // Keep only last 20 searches
      if (history.length > 20) {
        history.length = 20;
      }
      
      localStorage.setItem(key, JSON.stringify(history));
    } catch (error) {
      console.error('❌ Failed to add to search history:', error);
    }
  },
  
  // Get search history
  getSearchHistory() {
    try {
      const key = `${this.PREFIX}search_history`;
      return JSON.parse(localStorage.getItem(key)) || [];
    } catch (error) {
      console.error('❌ Failed to get search history:', error);
      return [];
    }
  },
  
  // ✅ ADD THIS METHOD: Save lesson plan draft
  saveLessonPlanDraft(draftData) {
    try {
      const key = `${this.PREFIX}draft_${draftData.id}`;
      localStorage.setItem(key, JSON.stringify(draftData));
      console.log(`📦 Saved draft: ${draftData.title}`);
      return true;
    } catch (error) {
      console.error('❌ Failed to save draft:', error);
      return false;
    }
  },
  
  // ✅ ADD THIS METHOD: Get all drafts
  getAllDrafts() {
    try {
      const drafts = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith(`${this.PREFIX}draft_`)) {
          const draft = JSON.parse(localStorage.getItem(key));
          drafts.push(draft);
        }
      }
      return drafts.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    } catch (error) {
      console.error('❌ Failed to get drafts:', error);
      return [];
    }
  },
  
  // ✅ ADD THIS METHOD: Delete draft
  deleteDraft(draftId) {
    try {
      localStorage.removeItem(`${this.PREFIX}draft_${draftId}`);
      console.log(`🗑️ Deleted draft: ${draftId}`);
      return true;
    } catch (error) {
      console.error('❌ Failed to delete draft:', error);
      return false;
    }
  }
};

export default LessonPlanStorage;