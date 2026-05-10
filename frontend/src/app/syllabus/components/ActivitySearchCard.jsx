// src/app/syllabus/components/ActivitySearchCard.jsx
import React, { useEffect, useState, useMemo, useCallback, useRef } from "react";
import { Search, RefreshCw, ChevronDown, AlertCircle, Database, ShieldAlert, Filter } from "lucide-react";
import Fuse from "fuse.js";
import api from "@/lib/axios";
import { toast } from "react-toastify";
import LessonPlanStorage from "@/services/lessonPlanStorage";

const ActivitySearchCard = ({
  selectedTimetable,
  onLearningActivitySelect,
  onSpecificActivitySelect,
  t
}) => {
  const [learningActivities, setLearningActivities] = useState([]);
  const [specificActivities, setSpecificActivities] = useState([]);
  const [selectedLearningActivity, setSelectedLearningActivity] = useState(null);
  const [selectedSpecificActivity, setSelectedSpecificActivity] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingSpecific, setLoadingSpecific] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [rateLimitWarning, setRateLimitWarning] = useState(false);
  const [searchStats, setSearchStats] = useState({ time: 0, quality: "good" });
  const [searchOptions, setSearchOptions] = useState({
    searchInMethods: true,
    searchInDescriptions: true,
    searchInNames: true,
    caseSensitive: false,
    exactMatch: false,
    searchDepth: "normal"
  });
  
  const hasLoadedRef = useRef(new Set());
  const searchTimerRef = useRef(null);

  // 🔄 Load Learning Activities - ONE TIME ONLY per subject
  useEffect(() => {
    if (!selectedTimetable || !selectedTimetable.subject_version) {
      resetState();
      return;
    }

    const subjectVersionId = selectedTimetable.subject_version;
    
    // Don't reload if we already have data for this subject
    if (hasLoadedRef.current.has(subjectVersionId) && learningActivities.length > 0) {
      console.log("📦 Using cached activities for this subject");
      return;
    }

    loadLearningActivities(subjectVersionId);
  }, [selectedTimetable]);

  const resetState = () => {
    setLearningActivities([]);
    setSpecificActivities([]);
    setSelectedLearningActivity(null);
    setSelectedSpecificActivity(null);
    setSearchQuery("");
    setShowDropdown(false);
  };

  const loadLearningActivities = async (subjectVersionId) => {
    if (rateLimitWarning) {
      toast.warning(t("errors.rate_limit_activities") || "Tafadhali subiri kidogo kabla ya kufanya ombi zaidi", {
        position: "bottom-right",
        autoClose: 3000,
      });
      return;
    }

    setLoading(true);
    try {
      console.log("🎯 Loading learning activities for subject version:", subjectVersionId);
      
      // Check local storage cache first
      const cached = LessonPlanStorage.getCachedActivities(subjectVersionId);
      if (cached && new Date() - new Date(cached.cachedAt) < 600000) { // 10 minutes cache
        console.log("📦 Using local storage cache");
        setLearningActivities(cached.learningActivities);
        
        if (cached.learningActivities.length > 0) {
          const firstActivity = cached.learningActivities[0];
          setSelectedLearningActivity(firstActivity);
          onLearningActivitySelect?.(firstActivity);
          
          // Check if we have cached specific activities for this learning activity
          if (cached.specificActivities?.[firstActivity.id]) {
            const cachedSpecific = cached.specificActivities[firstActivity.id];
            setSpecificActivities(cachedSpecific);
            if (cachedSpecific.length > 0) {
              const firstSpecific = cachedSpecific[0];
              setSelectedSpecificActivity(firstSpecific);
              onSpecificActivitySelect?.(firstSpecific);
              setSearchQuery(firstSpecific.name || "");
            }
          } else {
            // Load specific activities
            await loadSpecificActivities(firstActivity.id, subjectVersionId, true);
          }
        }
        
        hasLoadedRef.current.add(subjectVersionId);
        
        toast.success(t("lesson_plan.data_cached") || "Data imehifadhiwa kwa matumizi ya baadaye", {
          position: "bottom-right",
          autoClose: 2000,
        });
        return;
      }

      // API call with retry logic
      const response = await api.get("/syllabus/learning-activities/", {
        params: { 
          subject_version: subjectVersionId 
        }
      });
      
      const activities = Array.isArray(response.data) ? response.data : [];
      console.log("✅ Loaded", activities.length, "learning activities");
      
      setLearningActivities(activities);
      
      if (activities.length > 0) {
        const firstActivity = activities[0];
        setSelectedLearningActivity(firstActivity);
        onLearningActivitySelect?.(firstActivity);
        
        // Load specific activities with delay to avoid rate limiting
        setTimeout(() => {
          loadSpecificActivities(firstActivity.id, subjectVersionId, false);
        }, 1000);
        
        // Cache in local storage
        LessonPlanStorage.cacheActivities(subjectVersionId, activities, {});
      }
      
      hasLoadedRef.current.add(subjectVersionId);
      setRateLimitWarning(false);
      
      toast.success(t("lesson_plan.all_activities_loaded")?.replace("{{count}}", activities.length) || `Shughuli ${activities.length} zimepakuliwa`, {
        position: "bottom-right",
        autoClose: 3000,
      });
      
    } catch (error) {
      console.error("❌ Failed to load learning activities:", error);
      
      if (error.response?.status === 429) {
        setRateLimitWarning(true);
        toast.error(t("errors.rate_limit_activities") || "Kikomo cha ombi kimefikwa. Tafadhali subiri...", {
          position: "bottom-right",
          autoClose: 5000,
        });
        
        // Auto-retry after 30 seconds
        setTimeout(() => {
          setRateLimitWarning(false);
          toast.info(t("common.retry") || "Inajaribu tena...", { 
            position: "bottom-right", 
            autoClose: 2000 
          });
          loadLearningActivities(subjectVersionId);
        }, 30000);
      } else {
        toast.error(t("errors.failed_to_load_activities") || "Imeshindwa kupakia shughuli. Tafadhali jaribu tena.", {
          position: "bottom-right",
          autoClose: 3000,
        });
      }
    } finally {
      setLoading(false);
    }
  };

  // 🔄 Load Specific Activities with exponential backoff
  const loadSpecificActivities = useCallback(async (learningActivityId, subjectVersionId, fromCache = false) => {
    if (!learningActivityId || rateLimitWarning) return;

    setLoadingSpecific(true);
    try {
      console.log("🎯 Loading specific activities for learning activity:", learningActivityId);
      
      // Check local cache first
      const cached = LessonPlanStorage.getCachedActivities(subjectVersionId);
      if (cached?.specificActivities?.[learningActivityId] && fromCache) {
        const cachedSpecific = cached.specificActivities[learningActivityId];
        setSpecificActivities(cachedSpecific);
        
        if (cachedSpecific.length > 0) {
          const firstSpecific = cachedSpecific[0];
          setSelectedSpecificActivity(firstSpecific);
          onSpecificActivitySelect?.(firstSpecific);
          setSearchQuery(firstSpecific.name || "");
        }
        return;
      }

      // API call with delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const response = await api.get("/syllabus/specific-learning-activities/", {
        params: { 
          learning_activity: learningActivityId 
        }
      });
      
      const specific = Array.isArray(response.data) ? response.data : [];
      console.log("✅ Loaded", specific.length, "specific activities");
      
      setSpecificActivities(specific);
      
      if (specific.length > 0) {
        const firstSpecific = specific[0];
        setSelectedSpecificActivity(firstSpecific);
        onSpecificActivitySelect?.(firstSpecific);
        setSearchQuery(firstSpecific.name || "");
        
        // Update cache
        if (subjectVersionId) {
          LessonPlanStorage.updateSpecificActivitiesCache(
            subjectVersionId, 
            learningActivityId, 
            specific
          );
        }
      }
      
      setRateLimitWarning(false);
      
    } catch (error) {
      console.error("❌ Failed to load specific activities:", error);
      
      if (error.response?.status === 429) {
        setRateLimitWarning(true);
        toast.error(t("errors.rate_limit_activities") || "Kikomo cha ombi kimefikwa. Tafadhali subiri...", {
          position: "bottom-right",
          autoClose: 5000,
        });
        
        // Exponential backoff retry
        const retryDelay = 10000;
        setTimeout(() => {
          setRateLimitWarning(false);
          loadSpecificActivities(learningActivityId, subjectVersionId, false);
        }, retryDelay);
      }
    } finally {
      setLoadingSpecific(false);
    }
  }, [rateLimitWarning, onSpecificActivitySelect, t]);

  // 🔍 Advanced Fuzzy Search for Specific Activities
  const filteredSpecificActivities = useMemo(() => {
    if (!searchQuery.trim()) return specificActivities;
    
    const startTime = Date.now();
    
    // Configure Fuse.js based on search options
    const fuseOptions = {
      keys: [],
      threshold: searchOptions.searchDepth === "deep" ? 0.3 : 
                searchOptions.searchDepth === "shallow" ? 0.5 : 0.4,
      includeScore: true,
      ignoreLocation: true,
      shouldSort: true,
      minMatchCharLength: searchOptions.exactMatch ? searchQuery.length : 1,
      findAllMatches: true,
      useExtendedSearch: true,
      isCaseSensitive: searchOptions.caseSensitive,
    };
    
    // Add keys based on search options
    if (searchOptions.searchInNames) fuseOptions.keys.push("name");
    if (searchOptions.searchInMethods) fuseOptions.keys.push("method");
    if (searchOptions.searchInDescriptions) fuseOptions.keys.push("description");
    
    const fuse = new Fuse(specificActivities, fuseOptions);
    
    let results;
    if (searchOptions.exactMatch) {
      // Exact match search
      const searchPattern = `^${searchQuery}$`;
      results = fuse.search(searchPattern);
    } else {
      // Fuzzy search
      results = fuse.search(searchQuery);
    }
    
    const searchTime = Date.now() - startTime;
    
    // Determine search quality
    let quality = "excellent";
    if (searchTime > 100) quality = "good";
    if (searchTime > 500) quality = "fair";
    if (searchTime > 1000) quality = "poor";
    
    setSearchStats({
      time: searchTime,
      quality,
      count: results.length,
      total: specificActivities.length
    });
    
    return results.map(result => result.item);
  }, [searchQuery, specificActivities, searchOptions]);

  // Handle Learning Activity Selection
  const handleLearningActivityChange = (e) => {
    const activityId = e.target.value;
    const selected = learningActivities.find(activity => activity.id === activityId);
    
    if (!selected) return;
    
    console.log("🎯 Selected Learning Activity:", selected);
    setSelectedLearningActivity(selected);
    setSelectedSpecificActivity(null);
    setSearchQuery("");
    setShowDropdown(false);
    onLearningActivitySelect?.(selected);
    
    // Check cache first
    const subjectVersionId = selectedTimetable?.subject_version;
    const cached = LessonPlanStorage.getCachedActivities(subjectVersionId);
    
    if (cached?.specificActivities?.[selected.id]) {
      console.log("📦 Using cached specific activities");
      const cachedSpecific = cached.specificActivities[selected.id];
      setSpecificActivities(cachedSpecific);
      
      if (cachedSpecific.length > 0) {
        const firstSpecific = cachedSpecific[0];
        setSelectedSpecificActivity(firstSpecific);
        onSpecificActivitySelect?.(firstSpecific);
        setSearchQuery(firstSpecific.name || "");
      }
    } else {
      // Load from API with delay
      setTimeout(() => {
        loadSpecificActivities(selected.id, subjectVersionId, false);
      }, 800);
    }
  };

  // Handle Specific Activity Selection from Dropdown
  const handleSpecificActivitySelect = (activity) => {
    console.log("🎯 Selected Specific Activity:", activity);
    setSelectedSpecificActivity(activity);
    setSearchQuery(activity.name);
    setShowDropdown(false);
    onSpecificActivitySelect?.(activity);
  };

  // Handle Search Input Change with Debounce
  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchQuery(value);
    
    // Clear previous timer
    if (searchTimerRef.current) {
      clearTimeout(searchTimerRef.current);
    }
    
    // If user clears search, clear selection
    if (!value.trim() && selectedSpecificActivity) {
      setSelectedSpecificActivity(null);
      onSpecificActivitySelect?.(null);
    }
    
    // Show dropdown when typing (with debounce)
    if (value.trim() && specificActivities.length > 0) {
      searchTimerRef.current = setTimeout(() => {
        setShowDropdown(true);
      }, 300);
    }
  };

  // Clear Search
  const clearSearch = () => {
    setSearchQuery("");
    setSelectedSpecificActivity(null);
    setShowDropdown(false);
    onSpecificActivitySelect?.(null);
    
    if (searchTimerRef.current) {
      clearTimeout(searchTimerRef.current);
    }
  };

  // Toggle Advanced Search Options
  const toggleAdvancedSearch = () => {
    // You can implement a modal or expandable section for advanced search
    toast.info(t("lesson_plan.advanced_search") || "Chaguzi za utafutaji wa juu zitakuja hivi karibuni", {
      position: "bottom-right",
      autoClose: 3000,
    });
  };

  // Clear Search History
  const clearSearchHistory = () => {
    LessonPlanStorage.clearSearchHistory();
    toast.success(t("lesson_plan.search_history_cleared") || "Historia ya utafutaji imefutwa", {
      position: "bottom-right",
      autoClose: 3000,
    });
  };

  // Get quality color
  const getQualityColor = (quality) => {
    switch (quality) {
      case "excellent": return "text-green-600";
      case "good": return "text-blue-600";
      case "fair": return "text-yellow-600";
      case "poor": return "text-red-600";
      default: return "text-gray-600";
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {t ? t('lesson_plan.select_activities') : "Chagua Shughuli"}
      </h2>

      {/* Rate Limit Warning */}
      {rateLimitWarning && (
        <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <div className="flex items-center gap-2">
            <ShieldAlert size={16} className="text-amber-600 animate-pulse" />
            <div className="flex-1">
              <div className="font-medium text-amber-800 dark:text-amber-300">
                {t ? t('lesson_plan.warning') : "Onyo la Kikomo cha Omb"}
              </div>
              <div className="text-sm text-amber-700 dark:text-amber-400 mt-1">
                {t ? t('errors.rate_limit_activities') : "Umezingua idadi ya ombi. Tafadhali subiri kidogo..."}
              </div>
            </div>
            <RefreshCw size={14} className="animate-spin text-amber-600" />
          </div>
        </div>
      )}

      {/* Cache Status */}
      <div className="mb-4 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-gray-500">
          <Database size={12} />
          <span>
            {t ? t('lesson_plan.data_cached') : "Hifadhi"}: {
              hasLoadedRef.current.has(selectedTimetable?.subject_version) ? 
              t ? t('common.active') : 'Inatumika' : 
              t ? t('common.loading') : 'Inapakia...'
            }
          </span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={clearSearchHistory}
            className="text-xs text-gray-400 hover:text-gray-600"
            title={t ? t('lesson_plan.clear_history') : "Futa historia ya utafutaji"}
          >
            {t ? t('lesson_plan.clear_history') : "Futa Historia"}
          </button>
          <button
            onClick={() => {
              LessonPlanStorage.clearSession();
              hasLoadedRef.current.clear();
              toast.info(t ? t('lesson_plan.session_cleared') : "Hifadhi imefutwa", { 
                position: "bottom-right" 
              });
            }}
            className="text-xs text-gray-400 hover:text-gray-600"
          >
            {t ? t('common.clear') : "Futa Hifadhi"}
          </button>
        </div>
      </div>

      {/* Learning Activity Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {t ? t('lesson_plan.select_learning_activity') : "Chagua Shughuli ya Kujifunza"} *
        </label>
        <div className="relative">
          <select
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-3 dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
            onChange={handleLearningActivityChange}
            value={selectedLearningActivity?.id || ""}
            disabled={loading || !selectedTimetable || rateLimitWarning}
          >
            <option value="">
              {loading ? 
                (t ? t('common.loading') + "..." : "Inapakia...") : 
                (t ? t('lesson_plan.select_learning_activity') : "Chagua shughuli ya kujifunza")
              }
            </option>
            {learningActivities.map((activity) => (
              <option key={activity.id} value={activity.id}>
                {activity.name}
              </option>
            ))}
          </select>
          {loading && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <RefreshCw size={18} className="animate-spin text-gray-400" />
            </div>
          )}
        </div>
        
        {learningActivities.length > 0 && (
          <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            {t ? t('lesson_plan.found_learning_activities', { count: learningActivities.length }) : 
                `Shughuli ${learningActivities.length} za kujifunza zimepatikana`}
          </div>
        )}
      </div>

      {/* Specific Activity Search with Dropdown */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {t ? t('lesson_plan.specific_activity') : "Shughuli Maalum ya Kujifunza"} *
        </label>
        
        <div className="relative">
          {/* Search Input with Advanced Options */}
          <div className="relative mb-2">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              placeholder={t ? t('lesson_plan.search_placeholder') : "Tafuta shughuli..."}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg pl-10 pr-20 py-3 dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
              value={searchQuery}
              onChange={handleSearchChange}
              onFocus={() => specificActivities.length > 0 && setShowDropdown(true)}
              disabled={!selectedLearningActivity || loadingSpecific || rateLimitWarning}
            />
            
            {/* Advanced Search Button */}
            <button
              onClick={toggleAdvancedSearch}
              className="absolute right-10 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              type="button"
              title={t ? t('lesson_plan.advanced_search') : "Utafutaji wa Juu"}
            >
              <Filter size={16} />
            </button>
            
            {/* Clear Button */}
            {searchQuery && (
              <button
                onClick={clearSearch}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                type="button"
                title={t ? t('common.clear') : "Futa"}
              >
                ✕
              </button>
            )}
          </div>

          {/* Search Stats */}
          {searchQuery && filteredSpecificActivities.length > 0 && (
            <div className="mb-2 text-xs text-gray-500 dark:text-gray-400">
              <div className="flex items-center justify-between">
                <span>
                  {t ? t('lesson_plan.showing_results', { 
                    count: filteredSpecificActivities.length, 
                    total: specificActivities.length 
                  }) : 
                  `Inaonyesha ${filteredSpecificActivities.length} kati ya ${specificActivities.length}`}
                </span>
                <span className={`${getQualityColor(searchStats.quality)}`}>
                  {t ? t(`lesson_plan.${searchStats.quality}`) : searchStats.quality} • {searchStats.time}ms
                </span>
              </div>
            </div>
          )}

          {/* Loading Indicator */}
          {loadingSpecific && (
            <div className="mt-2 flex items-center gap-2 text-sm text-blue-600">
              <RefreshCw size={14} className="animate-spin" />
              {t ? t('lesson_plan.loading') : "Inapakia"}...
            </div>
          )}

          {/* Dropdown with Search Results */}
          {showDropdown && selectedLearningActivity && specificActivities.length > 0 && (
            <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-64 overflow-y-auto">
              <div className="p-2 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {searchQuery ? (
                    t ? t('lesson_plan.search_results') : `Matokeo ya utafutaji: ${filteredSpecificActivities.length}`
                  ) : (
                    t ? t('lesson_plan.all_specific_activities', { count: specificActivities.length }) : 
                        `Shughuli zote maalum (${specificActivities.length})`
                  )}
                </div>
              </div>
              
              {filteredSpecificActivities.length > 0 ? (
                filteredSpecificActivities.map((activity) => (
                  <div
                    key={activity.id}
                    className={`p-3 cursor-pointer border-b border-gray-100 dark:border-gray-800 last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                      selectedSpecificActivity?.id === activity.id ? "bg-blue-50 dark:bg-blue-900/30" : ""
                    }`}
                    onClick={() => handleSpecificActivitySelect(activity)}
                  >
                    <div className="font-medium text-gray-900 dark:text-white">{activity.name}</div>
                    {activity.method && (
                      <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        <span className="font-medium">{t ? t('lesson_plan.method') : "Njia"}:</span> {activity.method}
                      </div>
                    )}
                    {activity.periods && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {t ? t('lesson_plan.duration') : "Muda"}: {activity.periods} {t ? t('lesson_plan.minutes') : "dakika"}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                  {t ? t('lesson_plan.no_results_for_search', { search: searchQuery }) : 
                      `Hakuna matokeo kwa utafutaji "${searchQuery}"`}
                  <div className="mt-2 text-xs">
                    {t ? t('lesson_plan.try_different_search') : "Jaribu utafutaji tofauti"}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Selected Activity Info */}
        {selectedSpecificActivity && (
          <div className="mt-3 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="font-medium text-gray-900 dark:text-white">
                  ✓ {t ? t('lesson_plan.specific_activity') : "Shughuli Maalum Imeshaguliwa"}: {selectedSpecificActivity.name}
                </div>
                {selectedSpecificActivity.method && (
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    <span className="font-medium">{t ? t('lesson_plan.method') : "Njia"}:</span> {selectedSpecificActivity.method}
                  </div>
                )}
              </div>
              <button
                onClick={clearSearch}
                className="ml-2 text-sm text-red-600 hover:text-red-800 whitespace-nowrap"
                type="button"
              >
                {t ? t('common.clear') : "Futa"}
              </button>
            </div>
          </div>
        )}
        
        {/* No Activities Message */}
        {selectedLearningActivity && specificActivities.length === 0 && !loadingSpecific && (
          <div className="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertCircle size={16} className="text-yellow-600" />
              <span className="text-sm text-yellow-700 dark:text-yellow-300">
                {t ? t('lesson_plan.no_activities_found') : "Hakuna shughuli maalum zilizopatikana kwa shughuli hii ya kujifunza"}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Search Tips */}
      {specificActivities.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">
            {t ? t('lesson_plan.search_tips') : "Vidokezo vya Utafutaji"}:
          </div>
          <ul className="text-xs text-blue-700 dark:text-blue-400 space-y-1">
            <li>• {t ? t('lesson_plan.search_tip_1') : "Tumia maneno muhimu yanayohusiana na somo"}</li>
            <li>• {t ? t('lesson_plan.search_tip_2') : "Jaribu kutafuta kwa njia au mbinu"}</li>
            <li>• {t ? t('lesson_plan.search_tip_3') : "Tumia maneno machache kwa matokeo bora"}</li>
          </ul>
        </div>
      )}

      {/* Status Summary */}
      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-900 rounded">
            <div className="font-medium text-gray-700 dark:text-gray-300">
              {t ? t('lesson_plan.learning_activity') : "Shughuli za Kujifunza"}
            </div>
            <div className="text-2xl font-bold text-blue-600">{learningActivities.length}</div>
          </div>
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-900 rounded">
            <div className="font-medium text-gray-700 dark:text-gray-300">
              {t ? t('lesson_plan.specific_activities') : "Shughuli Maalum"}
            </div>
            <div className="text-2xl font-bold text-green-600">{specificActivities.length}</div>
          </div>
        </div>
        
        {/* Requirements Status */}
        <div className="mt-4 space-y-2">
          <div className={`flex items-center gap-2 text-sm ${selectedTimetable ? 'text-green-600' : 'text-gray-500'}`}>
            <div className={`w-2 h-2 rounded-full ${selectedTimetable ? 'bg-green-500' : 'bg-gray-400'}`}></div>
            {t ? t('lesson_plan.requirement_subject') : "Somo limechaguliwa"}
          </div>
          <div className={`flex items-center gap-2 text-sm ${selectedLearningActivity ? 'text-green-600' : 'text-gray-500'}`}>
            <div className={`w-2 h-2 rounded-full ${selectedLearningActivity ? 'bg-green-500' : 'bg-gray-400'}`}></div>
            {t ? t('lesson_plan.requirement_learning_activity') : "Shughuli ya Kujifunza Imeshaguliwa"}
          </div>
          <div className={`flex items-center gap-2 text-sm ${selectedSpecificActivity ? 'text-green-600' : 'text-gray-500'}`}>
            <div className={`w-2 h-2 rounded-full ${selectedSpecificActivity ? 'bg-green-500' : 'bg-gray-400'}`}></div>
            {t ? t('lesson_plan.requirement_specific_activity') : "Shughuli Maalum Imeshaguliwa"}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ActivitySearchCard;