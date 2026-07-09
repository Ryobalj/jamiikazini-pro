// src/app/syllabus/components/ActionsCard.jsx
import React, { useState } from "react";
import { 
  FileText, 
  Download, 
  AlertCircle, 
  Eye, 
  Save, 
  Clock,
  Users,
  Calendar,
  BookOpen
} from "lucide-react";
import { toast } from "react-toastify";
import api from "@/lib/axios";

const ActionsCard = ({ 
  selectedTimetable, 
  selectedSpecificActivity, 
  selectedLearningActivity, 
  t,
  formData = {}
}) => {
  const [loading, setLoading] = useState(false);
  const [loadingPdf, setLoadingPdf] = useState(false);
  const [generatedLessonPlan, setGeneratedLessonPlan] = useState(null);
  const [saveAsDraftLoading, setSaveAsDraftLoading] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);

  // Format date for display
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('sw-TZ', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // Calculate lesson duration
  const calculateDuration = (timestart, timefinish) => {
    if (!timestart || !timefinish) return "40 dakika";
    
    const start = new Date(`2000-01-01T${timestart}`);
    const end = new Date(`2000-01-01T${timefinish}`);
    const diffMinutes = (end - start) / (1000 * 60);
    
    return `${diffMinutes} dakika`;
  };

  // Save lesson plan as draft
  const saveAsDraft = async () => {
    if (!selectedTimetable || !selectedSpecificActivity) {
      toast.error(t("lesson_plan.alert_select_activity") || "Tafadhali chagua shughuli maalum ya kujifunza", {
        position: "bottom-right",
        autoClose: 3000,
      });
      return;
    }

    setSaveAsDraftLoading(true);
    
    try {
      const draftData = {
        id: Date.now().toString(),
        title: `Andalio: ${selectedTimetable.subject_name} - ${selectedSpecificActivity.name}`,
        timetable: selectedTimetable,
        specificActivity: selectedSpecificActivity,
        learningActivity: selectedLearningActivity,
        formData: formData,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        status: 'draft'
      };

      // Get existing drafts
      const existingDrafts = JSON.parse(localStorage.getItem('jamiikazini_lesson_drafts') || '[]');
      
      // Check max drafts (10)
      if (existingDrafts.length >= 10) {
        toast.warning(t("lesson_plan.max_drafts_reached", { max: 10 }) || `Umeifikia kikomo cha rasimu (10)`, {
          position: "bottom-right",
          autoClose: 4000,
        });
        return;
      }

      // Add new draft
      existingDrafts.unshift(draftData);
      localStorage.setItem('jamiikazini_lesson_drafts', JSON.stringify(existingDrafts));
      
      toast.success(t("lesson_plan.draft_saved") || "Rasimu imehifadhiwa", {
        position: "bottom-right",
        autoClose: 3000,
      });
      
    } catch (error) {
      console.error("❌ Error saving draft:", error);
      toast.error(t("lesson_plan.save_error") || "Hitilafu ya kuhifadhi", {
        position: "bottom-right",
        autoClose: 5000,
      });
    } finally {
      setSaveAsDraftLoading(false);
    }
  };

  // Generate lesson plan
  const submitLessonPlan = async (format = "json") => {
    if (!selectedTimetable || !selectedSpecificActivity) {
      toast.error(t("lesson_plan.alert_select_activity") || "Tafadhali chagua shughuli maalum ya kujifunza", {
        position: "bottom-right",
        autoClose: 3000,
      });
      return;
    }

    if (format === "json") {
      setLoading(true);
      setGeneratedLessonPlan(null);
    } else {
      setLoadingPdf(true);
    }

    try {
      // Prepare payload based on LessonPlanRequestSerializer
      const payload = {
        timetable: selectedTimetable.id,
        specific_activity: selectedSpecificActivity.id,
        date: formData?.date || new Date().toISOString().split('T')[0],
        period: formData?.period || selectedTimetable.period || 1,
        timestart: formData?.timestart || selectedTimetable.timestart || "08:00",
        timefinish: formData?.timefinish || selectedTimetable.timefinish || "08:40",
        boys_attended: formData?.boys_attended || selectedTimetable.registeredboys || 0,
        girls_attended: formData?.girls_attended || selectedTimetable.registeredgirls || 0,
        language: formData?.language || "sw",
        is_song: formData?.is_song || false,
        repeat_next: formData?.repeat_next || false,
        managed_count: formData?.managed_count || null
      };

      console.log("📤 Sending lesson plan payload:", payload);

      // Build URL
      let url = "/syllabus/lesson-plans/auto/";
      if (format === "pdf") {
        url += "?format=pdf";
      }

      // Make API request
      const config = format === "pdf" ? { 
        responseType: "blob",
        timeout: 60000 // 60 seconds timeout for PDF generation
      } : {};
      
      const res = await api.post(url, payload, config);

      if (format === "pdf") {
        // Handle PDF download
        const blob = new Blob([res.data], { type: "application/pdf" });
        const urlObject = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = urlObject;
        a.download = `Andalio_${selectedTimetable.subject_name}_${selectedTimetable.class_level_name}_${payload.date}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(urlObject);
        
        toast.success(t("lesson_plan.pdf_downloaded") || "PDF ya andalio imepakuliwa", {
          position: "bottom-right",
          autoClose: 3000,
        });
      } else {
        // Handle JSON response
        setGeneratedLessonPlan(res.data);
        console.log("✅ Lesson plan generated:", res.data);
        
        toast.success(t("lesson_plan.generated_success") || "Andalio la somo limeundwa kikamilifu!", {
          position: "bottom-right",
          autoClose: 3000,
        });
        
        // Auto-preview the generated lesson plan
        setPreviewMode(true);
      }
    } catch (error) {
      console.error(`❌ Error generating lesson plan (${format}):`, error);
      
      // Enhanced error handling with specific messages
      if (error.response) {
        const status = error.response.status;
        const errorData = error.response.data;
        
        let errorMessage = t("lesson_plan.error_generic") || "Hitilafu ilitokea wakati wa kutengeneza andalio la somo";
        
        switch (status) {
          case 400:
            if (errorData.detail) {
              errorMessage = errorData.detail;
            } else if (errorData.specific_activity) {
              errorMessage = errorData.specific_activity;
            } else if (typeof errorData === 'object') {
              const firstKey = Object.keys(errorData)[0];
              if (Array.isArray(errorData[firstKey])) {
                errorMessage = `${firstKey}: ${errorData[firstKey][0]}`;
              } else if (typeof errorData[firstKey] === 'string') {
                errorMessage = errorData[firstKey];
              }
            }
            break;
            
          case 401:
            errorMessage = t("errors.unauthorized") || "Una uhakika? Ingia tena";
            break;
            
          case 402:
            errorMessage = t("lesson_plan.pdf_error") || "PDF inahitaji usajili wa premium. Wasiliana na msimamizi.";
            break;
            
          case 404:
            errorMessage = t("errors.failed_to_load") || "Sehemu ya andalio haipatikani. Hakikisha URL ni sahihi.";
            break;
            
          case 429:
            errorMessage = t("errors.rate_limit") || "Umezingua idadi ya ombi. Subiri kidogo kisha jaribu tena.";
            break;
            
          case 500:
            errorMessage = t("errors.server_error") || "Hitilafu ya seva. Tafadhali jaribu tena baadaye.";
            break;
        }
        
        toast.error(errorMessage, {
          position: "bottom-right",
          autoClose: 5000,
        });
      } else if (error.request) {
        // Network error
        toast.error(t("errors.network_error") || "Hitilafu ya mtandao. Hakikisha umeunganishwa kwenye mtandao.", {
          position: "bottom-right",
          autoClose: 5000,
        });
      } else {
        toast.error(t("errors.generic") || "Hitilafu isiyojulikana imetokea.", {
          position: "bottom-right",
          autoClose: 5000,
        });
      }
    } finally {
      if (format === "json") {
        setLoading(false);
      } else {
        setLoadingPdf(false);
      }
    }
  };

  // Preview generated lesson plan
  const renderLessonPlanPreview = () => {
    if (!generatedLessonPlan || !previewMode) return null;

    const { meta, steps, assessment } = generatedLessonPlan;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          {/* Preview Header */}
          <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  {t("lesson_plan.preview") || "Hakiki ya Andalio la Somo"}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {meta?.subject} - {meta?.class_level} • {formatDate(meta?.date)}
                </p>
              </div>
              <button
                onClick={() => setPreviewMode(false)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Preview Content */}
          <div className="p-6">
            {/* Meta Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen size={16} className="text-blue-600" />
                  <span className="font-medium text-blue-800 dark:text-blue-300">Somo:</span>
                </div>
                <p className="text-blue-700 dark:text-blue-400">{meta?.subject}</p>
              </div>
              
              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Users size={16} className="text-green-600" />
                  <span className="font-medium text-green-800 dark:text-green-300">Darasa:</span>
                </div>
                <p className="text-green-700 dark:text-green-400">{meta?.class_level}</p>
              </div>
              
              <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Clock size={16} className="text-purple-600" />
                  <span className="font-medium text-purple-800 dark:text-purple-300">Muda:</span>
                </div>
                <p className="text-purple-700 dark:text-purple-400">{meta?.timestart} - {meta?.timefinish}</p>
              </div>
              
              <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Calendar size={16} className="text-amber-600" />
                  <span className="font-medium text-amber-800 dark:text-amber-300">Tarehe:</span>
                </div>
                <p className="text-amber-700 dark:text-amber-400">{formatDate(meta?.date)}</p>
              </div>
            </div>

            {/* Lesson Steps */}
            {steps && steps.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  {t("lesson_plan.lesson_steps") || "Hatua za Somo"}
                </h3>
                <div className="space-y-3">
                  {steps.map((step, index) => (
                    <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900 dark:text-white">{step.title}</h4>
                        {step.duration_minutes && (
                          <span className="text-sm text-gray-500 dark:text-gray-400">
                            {step.duration_minutes} {t("lesson_plan.minutes") || "dakika"}
                          </span>
                        )}
                      </div>
                      <p className="text-gray-600 dark:text-gray-300">{step.description}</p>
                      {step.activities && step.activities.length > 0 && (
                        <ul className="mt-2 space-y-1">
                          {step.activities.map((activity, idx) => (
                            <li key={idx} className="text-sm text-gray-500 dark:text-gray-400 flex items-start">
                              <span className="mr-2">•</span>
                              {activity}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Assessment */}
            {assessment && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  {t("lesson_plan.assessment_methods") || "Tathmini"}
                </h3>
                <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg">
                  <p className="text-gray-700 dark:text-gray-300">{assessment.criteria}</p>
                  {assessment.tools && (
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                      <span className="font-medium">Vifaa:</span> {assessment.tools}
                    </p>
                  )}
                  {assessment.remarks && (
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                      <span className="font-medium">Maelezo:</span> {assessment.remarks}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => submitLessonPlan("pdf")}
                disabled={loadingPdf}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {loadingPdf ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <Download size={16} />
                )}
                {t("lesson_plan.download_pdf") || "Pakua PDF"}
              </button>
              
              <button
                onClick={saveAsDraft}
                disabled={saveAsDraftLoading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {saveAsDraftLoading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <Save size={16} />
                )}
                {t("lesson_plan.save_draft") || "Hifadhi Rasimu"}
              </button>
              
              <button
                onClick={() => setPreviewMode(false)}
                className="flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
              >
                {t("common.close") || "Funga"}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t("lesson_plan.actions") || "Vitendo"}
        </h2>
        
        {/* Quick Stats */}
        {(selectedTimetable || selectedSpecificActivity) && (
          <div className="mb-6 grid grid-cols-2 gap-3">
            {selectedTimetable && (
              <>
                <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <BookOpen size={14} className="text-blue-600" />
                    <span className="text-xs font-medium text-blue-700 dark:text-blue-300">Somo</span>
                  </div>
                  <p className="text-sm font-semibold text-blue-800 dark:text-blue-400 truncate">
                    {selectedTimetable.subject_name}
                  </p>
                </div>
                
                <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <Users size={14} className="text-green-600" />
                    <span className="text-xs font-medium text-green-700 dark:text-green-300">Darasa</span>
                  </div>
                  <p className="text-sm font-semibold text-green-800 dark:text-green-400">
                    {selectedTimetable.class_level_name}
                  </p>
                </div>
              </>
            )}
            
            {selectedSpecificActivity && (
              <div className="col-span-2 bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Clock size={14} className="text-purple-600" />
                  <span className="text-xs font-medium text-purple-700 dark:text-purple-300">Shughuli</span>
                </div>
                <p className="text-sm font-semibold text-purple-800 dark:text-purple-400 truncate">
                  {selectedSpecificActivity.name}
                </p>
              </div>
            )}
          </div>
        )}
        
        {/* Action Buttons */}
        <div className="space-y-3">
          <button
            onClick={() => submitLessonPlan("json")}
            disabled={loading || !selectedTimetable || !selectedSpecificActivity}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                {t("lesson_plan.generating") || "Inatengeneza..."}
              </>
            ) : (
              <>
                <FileText size={18} />
                {t("lesson_plan.generate") || "Tengeneza Andalio la Somo"}
              </>
            )}
          </button>
          
          <button
            onClick={() => submitLessonPlan("pdf")}
            disabled={loadingPdf || !selectedTimetable || !selectedSpecificActivity}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loadingPdf ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                {t("common.loading") || "Inapakia..."}
              </>
            ) : (
              <>
                <Download size={18} />
                {t("lesson_plan.download_pdf") || "Pakua PDF"}
              </>
            )}
          </button>
          
          <button
            onClick={saveAsDraft}
            disabled={saveAsDraftLoading || !selectedTimetable || !selectedSpecificActivity}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saveAsDraftLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                {t("common.saving") || "Inahifadhi..."}
              </>
            ) : (
              <>
                <Save size={18} />
                {t("lesson_plan.save_draft") || "Hifadhi Rasimu"}
              </>
            )}
          </button>
        </div>
        
        {/* Requirements Status */}
        <div className="mt-6 space-y-2">
          <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t("lesson_plan.requirements") || "Mahitaji"}:
          </div>
          <div className={`flex items-center gap-2 text-sm ${selectedTimetable ? 'text-green-600' : 'text-gray-500'}`}>
            <div className={`w-2 h-2 rounded-full ${selectedTimetable ? 'bg-green-500' : 'bg-gray-400'}`}></div>
            {t("lesson_plan.requirement_subject") || "Somo limechaguliwa"}
          </div>
          <div className={`flex items-center gap-2 text-sm ${selectedLearningActivity ? 'text-green-600' : 'text-gray-500'}`}>
            <div className={`w-2 h-2 rounded-full ${selectedLearningActivity ? 'bg-green-500' : 'bg-gray-400'}`}></div>
            {t("lesson_plan.requirement_learning_activity") || "Shughuli ya Kujifunza Imeshaguliwa"}
          </div>
          <div className={`flex items-center gap-2 text-sm ${selectedSpecificActivity ? 'text-green-600' : 'text-gray-500'}`}>
            <div className={`w-2 h-2 rounded-full ${selectedSpecificActivity ? 'bg-green-500' : 'bg-gray-400'}`}></div>
            {t("lesson_plan.requirement_specific_activity") || "Shughuli Maalum Imeshaguliwa"}
          </div>
        </div>
        
        {/* Error/Warning Messages */}
        {!selectedTimetable && (
          <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertCircle size={16} className="text-yellow-600" />
              <span className="text-sm text-yellow-700 dark:text-yellow-300">
                {t("lesson_plan.alert_select_subject") || "Tafadhali chagua somo kwanza"}
              </span>
            </div>
          </div>
        )}
        
        {selectedTimetable && !selectedSpecificActivity && (
          <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertCircle size={16} className="text-yellow-600" />
              <span className="text-sm text-yellow-700 dark:text-yellow-300">
                {t("lesson_plan.alert_select_activity") || "Tafadhali chagua shughuli maalum ya kujifunza"}
              </span>
            </div>
          </div>
        )}

        {/* Additional Info */}
        {(selectedTimetable || formData.date) && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-center justify-between mb-1">
                <span>{t("lesson_plan.selected_date") || "Tarehe"}:</span>
                <span className="font-medium">
                  {formData.date ? formatDate(formData.date) : formatDate(new Date().toISOString().split('T')[0])}
                </span>
              </div>
              <div className="flex items-center justify-between mb-1">
                <span>{t("lesson_plan.duration") || "Muda"}:</span>
                <span className="font-medium">
                  {calculateDuration(formData.timestart || selectedTimetable?.timestart, formData.timefinish || selectedTimetable?.timefinish)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>{t("lesson_plan.total_students") || "Wanafunzi"}:</span>
                <span className="font-medium">
                  {(formData.boys_attended || 0) + (formData.girls_attended || 0)} {t("common.total") || "jumla"}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Lesson Plan Preview Modal */}
      {renderLessonPlanPreview()}
    </>
  );
};

export default ActionsCard;