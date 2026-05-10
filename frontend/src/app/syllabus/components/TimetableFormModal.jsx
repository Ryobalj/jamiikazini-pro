// src/app/syllabus/components/TimetableFormModal.jsx
import React, { useEffect, useState, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "../../../lib/axios.js";

export default function TimetableFormModal({
  open,
  onClose,
  onSubmit,
  initialData,
  workstations = [],
}) {
  const { t } = useTranslation(["syllabus", "common"]);
  const firstInputRef = useRef(null);
  const navigate = useNavigate();
  const suggestionsRef = useRef(null);

  const inputClass =
    "w-full rounded-lg border px-3 py-2 " +
    "border-gray-300 dark:border-gray-600 " +
    "bg-white dark:bg-gray-700 " +
    "text-gray-900 dark:text-white " +
    "placeholder-gray-400 dark:placeholder-gray-400 " +
    "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 " +
    "disabled:bg-gray-100 disabled:cursor-not-allowed dark:disabled:bg-gray-800 " +
    "transition-colors duration-200";

  const [form, setForm] = useState({
    workstation: "",
    subject_version: "",
    subject_name: "",
    class_level: "",
    syllabus_year: "",
    registeredboys: "",
    registeredgirls: "",
    status: false,
  });

  const [subjectQuery, setSubjectQuery] = useState("");
  const [subjectOptions, setSubjectOptions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);
  const [formErrors, setFormErrors] = useState({});

  /* ---------------- RESET FORM ---------------- */
  useEffect(() => {
    if (!open) return;

    if (initialData) {
      setForm({
        ...initialData,
        subject_name: initialData.subject_display || initialData.subject_version?.subject?.name || "",
        class_level: initialData.class_level_display || initialData.subject_version?.class_level?.name || "",
        syllabus_year: initialData.subject_version?.syllabus_version?.year || "",
        registeredboys: initialData.registeredboys || "",
        registeredgirls: initialData.registeredgirls || "",
      });
    } else {
      setForm({
        workstation: workstations[0]?.id || "",
        subject_version: "",
        subject_name: "",
        class_level: "",
        syllabus_year: "",
        registeredboys: "",
        registeredgirls: "",
        status: false,
      });
    }

    setSubjectQuery("");
    setSubjectOptions([]);
    setShowSuggestions(false);
    setLoading(false);
    setSearching(false);
    setError(null);
    setFormErrors({});

    setTimeout(() => firstInputRef.current?.focus(), 100);
  }, [open, initialData, workstations]);

  /* ---------------- CLICK OUTSIDE SUGGESTIONS ---------------- */
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  /* ---------------- SUBJECT SEARCH - FIXED ---------------- */
  const fetchSubjects = useCallback(async (query) => {
    if (!query || query.trim().length < 2) {
      setSubjectOptions([]);
      setShowSuggestions(false);
      return;
    }

    const controller = new AbortController();
    setSearching(true);
    setError(null);

    try {
      const res = await api.get("/syllabus/subject-versions-readonly/", {
        params: { 
          search: query.trim(),
          limit: 20 
        },
        signal: controller.signal,
      });

      let data = [];
      
      if (Array.isArray(res.data)) {
        data = res.data;
      } else if (res.data?.results && Array.isArray(res.data.results)) {
        data = res.data.results;
      } else if (res.data?.data && Array.isArray(res.data.data)) {
        data = res.data.data;
      }

      const options = data.map((item, index) => {
        const subjectData = {
          id: item.id || item.pk || index,
          name: "",
          class_level: "",
          year: "",
          code: ""
        };

        // Get subject name
        if (item.subject) {
          if (typeof item.subject === 'object') {
            subjectData.name = item.subject.name || item.subject.subject_name || "";
            subjectData.code = item.subject.code || "";
          } else if (typeof item.subject === 'string') {
            subjectData.name = item.subject;
          }
        }
        if (!subjectData.name && item.name) subjectData.name = item.name;
        if (!subjectData.name && item.subject_name) subjectData.name = item.subject_name;
        if (!subjectData.name && item.subject_display) subjectData.name = item.subject_display;

        // Get class level
        if (item.class_level) {
          if (typeof item.class_level === 'object') {
            subjectData.class_level = item.class_level.name || item.class_level.class_level_name || "";
          } else {
            subjectData.class_level = item.class_level;
          }
        }
        if (!subjectData.class_level && item.class_level_name) subjectData.class_level = item.class_level_name;
        if (!subjectData.class_level && item.class_level_display) subjectData.class_level = item.class_level_display;

        // Get year
        if (item.syllabus_version) {
          if (typeof item.syllabus_version === 'object') {
            subjectData.year = item.syllabus_version.year || "";
          } else {
            subjectData.year = item.syllabus_version;
          }
        }
        if (!subjectData.year && item.year) subjectData.year = item.year;
        if (!subjectData.year && item.syllabus_year) subjectData.year = item.syllabus_year;

        // Get code
        if (!subjectData.code && item.code) subjectData.code = item.code;

        return subjectData;
      });

      const validOptions = options.filter(opt => opt.name && opt.name.trim() !== "");
      setSubjectOptions(validOptions);
      setShowSuggestions(validOptions.length > 0);
      
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(`Imeshindwa kupakia masomo: ${err.message}`);
      }
      setSubjectOptions([]);
      setShowSuggestions(false);
    } finally {
      setSearching(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (subjectQuery.trim().length >= 2) {
        fetchSubjects(subjectQuery);
      } else {
        setSubjectOptions([]);
        setShowSuggestions(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [subjectQuery, fetchSubjects]);

  /* ---------------- HANDLERS ---------------- */
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    if (formErrors[name]) {
      setFormErrors(prev => ({ ...prev, [name]: "" }));
    }
    if (error) setError(null);

    if (name === "subject_name") {
      setForm((prev) => ({
        ...prev,
        subject_name: value,
        ...(value !== prev.subject_name ? {
          subject_version: "",
          class_level: "",
          syllabus_year: "",
        } : {})
      }));
      setSubjectQuery(value);
    } else if (name === "registeredboys" || name === "registeredgirls") {
      if (value === "" || /^\d*$/.test(value)) {
        const numValue = value === "" ? "" : parseInt(value);
        if (numValue === "" || (numValue >= 0 && numValue <= 200)) {
          setForm((prev) => ({
            ...prev,
            [name]: value
          }));
        }
      }
    } else {
      setForm((prev) => ({
        ...prev,
        [name]: type === "checkbox" ? checked : value,
      }));
    }
  };

  const handleSelectSubject = (subject) => {
    setForm((prev) => ({
      ...prev,
      subject_version: subject.id,
      subject_name: subject.name,
      class_level: subject.class_level || "",
      syllabus_year: subject.year || "",
    }));
    setSubjectOptions([]);
    setSubjectQuery(subject.name);
    setShowSuggestions(false);
  };

  const validateForm = () => {
    const errors = {};

    if (!form.workstation) {
      errors.workstation = "Chagua kituo cha kazi";
    }

    if (!form.subject_version) {
      errors.subject_version = "Chagua somo kutoka kwenye orodha";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    setError(null);
    setFormErrors({});

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const submitData = {
        workstation: form.workstation,
        subject_version: form.subject_version,
        registeredboys: form.registeredboys ? parseInt(form.registeredboys) : null,
        registeredgirls: form.registeredgirls ? parseInt(form.registeredgirls) : null,
        status: Boolean(form.status),
      };
      
      await onSubmit(submitData);
      onClose?.();
      
    } catch (err) {
      let errorMessage = "Imeshindwa kuhifadhi ratiba";
      
      if (err.response?.data) {
        if (err.response.data.detail) {
          errorMessage = err.response.data.detail;
        } else if (err.response.data.message) {
          errorMessage = err.response.data.message;
        } else if (typeof err.response.data === 'string') {
          errorMessage = err.response.data;
        } else {
          const firstError = Object.values(err.response.data)[0];
          if (Array.isArray(firstError)) {
            errorMessage = firstError[0];
          } else if (typeof firstError === 'string') {
            errorMessage = firstError;
          }
        }
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (loading) return;
    onClose?.();
    navigate("/home");
  };

  const handleClickOutsideModal = (e) => {
    if (e.target === e.currentTarget && !loading) {
      handleCancel();
    }
  };

  if (!open) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-auto"
      onClick={handleClickOutsideModal}
    >
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-lg shadow-lg max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {initialData ? t("timetable.edit") : t("timetable.add")}
          </h2>
          <button
            onClick={handleCancel}
            disabled={loading}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50 p-1"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-700 dark:text-red-400 font-medium">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* WORKSTATION */}
          <div>
            <label className="font-medium text-gray-700 dark:text-gray-300">{t("timetable.workstation")} *</label>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{t("timetable.workstation_help")}</p>
            <select
              name="workstation"
              value={form.workstation}
              onChange={handleChange}
              className={`${inputClass} ${formErrors.workstation ? 'border-red-300 dark:border-red-600' : ''}`}
              required
            >
              <option value="">{t("common.select") || "Chagua..."}</option>
              {workstations.map((ws) => (
                <option key={ws.id} value={ws.id}>
                  {ws.school_name} — {ws.teacher_info?.full_name || "Mwalimu"}
                </option>
              ))}
            </select>
            {formErrors.workstation && (
              <p className="text-red-500 dark:text-red-400 text-sm mt-1">{formErrors.workstation}</p>
            )}
          </div>

          {/* SUBJECT SEARCH - WITH DARK MODE FIX */}
          <div className="relative" ref={suggestionsRef}>
            <label className="font-medium text-gray-700 dark:text-gray-300">{t("timetable.subject")} *</label>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{t("timetable.subject_help")}</p>
            
            <div className="relative">
              <input
                ref={firstInputRef}
                name="subject_name"
                value={form.subject_name}
                onChange={handleChange}
                placeholder={t("timetable.subject_placeholder")}
                className={`${inputClass} ${formErrors.subject_version ? 'border-red-300 dark:border-red-600' : ''} pr-10`}
                autoComplete="off"
                disabled={loading}
                required
              />
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                {searching ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                ) : (
                  <svg className="w-4 h-4 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                )}
              </div>
            </div>
            
            {formErrors.subject_version && (
              <p className="text-red-500 dark:text-red-400 text-sm mt-1">{formErrors.subject_version}</p>
            )}

            {/* DROPDOWN - COMPLETE DARK MODE SUPPORT */}
            {showSuggestions && (
              <div className="absolute top-full left-0 right-0 z-50 mt-1">
                <div className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 shadow-lg dark:shadow-gray-900/50 max-h-64 overflow-y-auto">
                  {searching ? (
                    <div className="p-4 text-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 dark:border-blue-400 mx-auto"></div>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                        {t("common.loading")}
                      </p>
                    </div>
                  ) : subjectOptions.length === 0 ? (
                    <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                      {subjectQuery.length < 2 
                        ? "Andika angalau herufi 2" 
                        : "Hakuna masomo yaliyopatikana"}
                    </div>
                  ) : (
                    <div>
                      {/* Header with dark mode */}
                      <div className="px-4 py-2 bg-gray-50 dark:bg-gray-900 border-b border-gray-300 dark:border-gray-600">
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                          Chagua somo ({subjectOptions.length})
                        </p>
                      </div>
                      
                      {/* List with dark mode */}
                      <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                        {subjectOptions.map((s) => (
                          <li
                            key={s.id}
                            onClick={() => handleSelectSubject(s)}
                            className="px-4 py-3 cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                          >
                            <div className="font-medium text-gray-900 dark:text-white mb-1">
                              {s.name}
                            </div>
                            <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                              {s.class_level && (
                                <div>
                                  <span className="font-medium">Darasa:</span> {s.class_level}
                                </div>
                              )}
                              {s.year && (
                                <div>
                                  <span className="font-medium">Mtaala:</span> {s.year}
                                </div>
                              )}
                              {s.code && (
                                <div>
                                  <span className="font-medium">Code:</span> {s.code}
                                </div>
                              )}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* READ-ONLY FIELDS */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">{t("timetable.class_level")}</label>
              <input
                value={form.class_level || t("timetable.not_selected")}
                readOnly
                className={`${inputClass} bg-gray-100 dark:bg-gray-900 text-gray-500 dark:text-gray-400`}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">{t("timetable.syllabus_year")}</label>
              <input
                value={form.syllabus_year || t("timetable.not_selected")}
                readOnly
                className={`${inputClass} bg-gray-100 dark:bg-gray-900 text-gray-500 dark:text-gray-400`}
              />
            </div>
          </div>

          {/* STUDENTS */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">{t("timetable.registered_boys")}</label>
              <input
                type="number"
                name="registeredboys"
                placeholder={t("timetable.registered_boys")}
                value={form.registeredboys}
                onChange={handleChange}
                className={inputClass}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">{t("timetable.registered_girls")}</label>
              <input
                type="number"
                name="registeredgirls"
                placeholder={t("timetable.registered_girls")}
                value={form.registeredgirls}
                onChange={handleChange}
                className={inputClass}
              />
            </div>
          </div>
          
          {/* STATUS */}
          <label className="flex flex-col gap-1">
            <span className="flex items-center gap-2">
              <input
                type="checkbox"
                name="status"
                checked={form.status}
                onChange={handleChange}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
              />
              <span className="font-medium text-gray-700 dark:text-gray-300">{t("timetable.status")}</span>
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">{t("timetable.status_help")}</span>
          </label>

          {/* ACTIONS */}
          <div className="flex justify-end gap-2 pt-4">
            <button
              type="button"
              onClick={handleCancel}
              disabled={loading}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
            >
              {t("common.cancel")}
            </button>
            <button 
              type="submit" 
              disabled={loading || !form.workstation || !form.subject_version}
              className="px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 flex items-center gap-2 transition-colors"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  {t("common.saving")}
                </>
              ) : (
                t("common.save")
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}