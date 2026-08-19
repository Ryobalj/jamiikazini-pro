// src/app/syllabus/pages/QuizGeneratorPage.jsx

import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, RefreshCw, AlertCircle, CheckCircle, Download, Sparkles } from "lucide-react";
import { toast } from "react-toastify";
import api from "@/lib/axios";

const PAPER_TYPES = ["quiz", "test", "examination"];

export default function QuizGeneratorPage() {
  const { t } = useTranslation("syllabus");
  const navigate = useNavigate();

  const [workstation, setWorkstation] = useState(null);
  const [timetableSubjects, setTimetableSubjects] = useState([]);
  const [examFormats, setExamFormats] = useState([]);

  const [paperType, setPaperType] = useState("quiz");
  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedFormat, setSelectedFormat] = useState("");
  const [title, setTitle] = useState("");
  const [year, setYear] = useState(new Date().getFullYear());
  const [term, setTerm] = useState("");

  const [paper, setPaper] = useState(null);
  const [shortfalls, setShortfalls] = useState(null);

  const [initialLoading, setInitialLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(null);

  const hasWorkstation = !!workstation;
  const hasSubjects = timetableSubjects.length > 0;
  const formatsForType = examFormats.filter((f) => f.paper_type === paperType);
  const isFormValid = Boolean(selectedSubject && selectedFormat);

  /* ===================== FETCH DATA ===================== */
  const fetchInitialData = useCallback(async () => {
    setInitialLoading(true);
    setError(null);
    try {
      const wsRes = await api.get("/syllabus/teacher-workstations/");
      const wsData = Array.isArray(wsRes.data) ? wsRes.data : wsRes.data?.results || [];
      const ws = wsData[0] || null;
      setWorkstation(ws);

      if (ws) {
        const ttRes = await api.get("/syllabus/timetables/", { params: { workstation: ws.id } });
        const ttData = Array.isArray(ttRes.data) ? ttRes.data : ttRes.data?.results || [];
        const seen = new Set();
        const subjects = [];
        ttData.forEach((tt) => {
          const key = tt.subject_version;
          if (!seen.has(key)) {
            seen.add(key);
            subjects.push({
              id: tt.subject_version,
              name: tt.subject_name,
              className: tt.class_level_name || tt.class_level_display,
            });
          }
        });
        setTimetableSubjects(subjects);
      } else {
        setTimetableSubjects([]);
      }

      const fmtRes = await api.get("/syllabus/exam-formats/");
      const fmtData = Array.isArray(fmtRes.data) ? fmtRes.data : fmtRes.data?.results || [];
      setExamFormats(fmtData);
    } catch (err) {
      console.error("Failed to load quiz generator data:", err);
      setError(t("quiz.error_generic"));
    } finally {
      setInitialLoading(false);
    }
  }, [t]);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  useEffect(() => {
    // Selected format may no longer belong to the newly chosen paper type
    if (selectedFormat && !formatsForType.some((f) => f.id === selectedFormat)) {
      setSelectedFormat("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paperType]);

  /* ===================== GENERATE ===================== */
  const handleGenerate = useCallback(async () => {
    if (!isFormValid) {
      toast.warning(t("quiz.select_subject_and_format"));
      return;
    }
    setGenerating(true);
    setPaper(null);
    setShortfalls(null);
    setError(null);

    try {
      const res = await api.post("/syllabus/quiz/generate/", {
        exam_format: selectedFormat,
        subject_version: selectedSubject,
        title,
        year: year || null,
        term: term || null,
      });
      setPaper(res.data);
      toast.success(t("quiz.generated_success"));
    } catch (err) {
      const data = err.response?.data;
      if (data?.shortfalls) {
        setShortfalls(data.shortfalls);
        toast.error(t("quiz.not_enough_questions"));
      } else {
        const msg =
          data?.subject_version ||
          data?.detail ||
          (typeof data === "object" ? Object.values(data)[0] : null) ||
          t("quiz.error_generic");
        setError(Array.isArray(msg) ? msg[0] : msg);
        toast.error(Array.isArray(msg) ? msg[0] : msg);
      }
    } finally {
      setGenerating(false);
    }
  }, [isFormValid, selectedFormat, selectedSubject, title, year, term, t]);

  /* ===================== DOWNLOAD ===================== */
  const handleDownload = useCallback(async () => {
    if (!paper) return;
    setDownloading(true);
    try {
      const res = await api.get(`/syllabus/quiz/${paper.id}/pdf/`, { responseType: "blob", timeout: 60000 });
      const blob = new Blob([res.data], { type: "application/zip" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${paperType}_${paper.subject_name}_${paper.class_level_name}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success(t("quiz.pdf_downloaded"));
    } catch (err) {
      const status = err.response?.status;
      if (status === 402 || status === 403) {
        toast.error(t("subscription.required_message") || err.response?.data?.detail);
      } else {
        toast.error(t("quiz.error_generic"));
      }
    } finally {
      setDownloading(false);
    }
  }, [paper, paperType, t]);

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
    <div className="max-w-5xl mx-auto p-4 md:p-6">
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t("quiz.title")}</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">{t("quiz.subtitle")}</p>
          <div className="mt-2 flex items-center gap-2">
            {hasWorkstation ? (
              <div className="flex items-center gap-1 text-sm text-green-600">
                <CheckCircle size={14} />
                <span>{workstation.school_name} • {workstation.district}</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-sm text-red-600">
                <AlertCircle size={14} />
                <span>{t("workstation.required_message")}</span>
              </div>
            )}
          </div>
        </div>
        <div className="ml-auto">
          <button
            onClick={fetchInitialData}
            disabled={generating || downloading}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title={t("common.refresh")}
          >
            <RefreshCw size={18} className="text-gray-600 dark:text-gray-400" />
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 mb-6">
          <p className="text-red-600 dark:text-red-300 text-sm">{error}</p>
        </div>
      )}

      {!hasWorkstation && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-6 text-center">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">{t("workstation.workstation_required")}</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{t("workstation.required_message")}</p>
        </div>
      )}

      {hasWorkstation && !hasSubjects && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6 text-center">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">{t("my_subjects.empty_title")}</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{t("timetable.timetable_required_message")}</p>
          <button
            onClick={() => navigate("/teaching/timetable")}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {t("timetable.go_to_timetable")}
          </button>
        </div>
      )}

      {hasWorkstation && hasSubjects && (
        <div className="space-y-6">
          {/* Selection */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-4">
            {/* Paper type tabs */}
            <div className="flex gap-2">
              {PAPER_TYPES.map((pt) => (
                <button
                  key={pt}
                  onClick={() => setPaperType(pt)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    paperType === pt
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                  }`}
                >
                  {t(`quiz.paper_type.${pt}`)}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t("quiz.subject_label")}
                </label>
                <select
                  value={selectedSubject}
                  onChange={(e) => setSelectedSubject(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-2"
                >
                  <option value="">{t("quiz.choose_subject")}</option>
                  {timetableSubjects.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.className})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t("quiz.format_label")}
                </label>
                <select
                  value={selectedFormat}
                  onChange={(e) => setSelectedFormat(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-2"
                >
                  <option value="">{t("quiz.choose_format")}</option>
                  {formatsForType.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name} ({f.total_marks} {t("quiz.marks")})
                    </option>
                  ))}
                </select>
                {formatsForType.length === 0 && (
                  <p className="text-xs text-amber-600 mt-1">{t("quiz.no_formats_for_type")}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t("quiz.title_label")}
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder={t("quiz.title_placeholder")}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-2"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t("quiz.year_label")}
                  </label>
                  <input
                    type="number"
                    value={year}
                    onChange={(e) => setYear(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t("quiz.term_label")}
                  </label>
                  <select
                    value={term}
                    onChange={(e) => setTerm(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-2"
                  >
                    <option value="">-</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                  </select>
                </div>
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={!isFormValid || generating}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
            >
              <Sparkles size={18} />
              {generating ? t("quiz.generating") : t("quiz.generate_button")}
            </button>
          </div>

          {/* Shortfall error */}
          {shortfalls && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
              <h3 className="font-semibold text-red-700 dark:text-red-400 mb-2">{t("quiz.not_enough_questions")}</h3>
              <ul className="list-disc list-inside text-sm text-red-600 dark:text-red-300 space-y-1">
                {shortfalls.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Generated paper preview */}
          {paper && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {paper.title || paper.exam_format_name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {paper.subject_name} • {paper.class_level_name}
                  </p>
                </div>
                <button
                  onClick={handleDownload}
                  disabled={downloading}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg text-sm font-medium"
                >
                  <Download size={16} />
                  {downloading ? t("common.saving") : t("quiz.download_button")}
                </button>
              </div>

              <div className="space-y-3">
                {Object.entries(
                  paper.paper_questions.reduce((acc, gpq) => {
                    (acc[gpq.section_name] = acc[gpq.section_name] || []).push(gpq);
                    return acc;
                  }, {})
                ).map(([sectionName, items]) => (
                  <div key={sectionName} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                    <p className="font-medium text-gray-800 dark:text-gray-200 mb-2">
                      {sectionName} ({items.reduce((sum, i) => sum + i.marks, 0)} {t("quiz.marks")})
                    </p>
                    <ol className="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-decimal list-inside">
                      {items.map((gpq) => (
                        <li key={gpq.id}>{gpq.question_detail?.prompt}</li>
                      ))}
                    </ol>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
