// src/app/syllabus/pages/QuizGeneratorPage.jsx

import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, RefreshCw, AlertCircle, CheckCircle, Download, Sparkles, Plus, Trash2 } from "lucide-react";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import TopicPicker from "../components/TopicPicker";

const PAPER_TYPES = ["quiz", "test", "examination"];
const QUESTION_TYPES = [
  "mcq", "matching", "fill_blank", "short_answer", "calculation", "sequencing", "true_false", "map_diagram", "comprehension",
];
const DIFFICULTIES = ["easy", "medium", "hard"];
const SECTION_LETTERS = "ABCDEFGH";

let localIdCounter = 0;
const nextLocalId = () => `local-${++localIdCounter}`;

const newSlot = () => ({ localId: nextLocalId(), question_type: "calculation", difficulty: "medium", count: 1, marks_per_item: 1 });
const newSection = (index) => ({
  localId: nextLocalId(),
  name: `SEHEMU ${SECTION_LETTERS[index] || index + 1}`,
  topicIds: [],
  slots: [newSlot()],
});

export default function QuizGeneratorPage() {
  const { t } = useTranslation("syllabus");
  const navigate = useNavigate();

  const [workstation, setWorkstation] = useState(null);
  const [timetableSubjects, setTimetableSubjects] = useState([]);
  const [examFormats, setExamFormats] = useState([]);

  const [mode, setMode] = useState("auto"); // "auto" | "manual"
  const [paperType, setPaperType] = useState("quiz");
  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedFormat, setSelectedFormat] = useState("");
  const [title, setTitle] = useState("");
  const [year, setYear] = useState(new Date().getFullYear());
  const [term, setTerm] = useState("");

  // Shared topic list for the selected subject (fetched once, used by every section's picker)
  const [topics, setTopics] = useState([]);
  const [topicsLoading, setTopicsLoading] = useState(false);

  // Automated mode: chosen format's own sections + per-section topic scope
  const [formatDetail, setFormatDetail] = useState(null);
  const [formatDetailLoading, setFormatDetailLoading] = useState(false);
  const [sectionTopics, setSectionTopics] = useState({}); // { [sectionId]: topicId[] }

  // Manual mode: teacher-built sections
  const [manualSections, setManualSections] = useState([newSection(0)]);
  const [manualTimeMinutes, setManualTimeMinutes] = useState("");
  const [manualInstructions, setManualInstructions] = useState("");

  const [paper, setPaper] = useState(null);
  const [shortfalls, setShortfalls] = useState(null);

  const [initialLoading, setInitialLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(null);

  const hasWorkstation = !!workstation;
  const hasSubjects = timetableSubjects.length > 0;
  const formatsForType = examFormats.filter((f) => f.paper_type === paperType);
  const isFormValid =
    mode === "auto"
      ? Boolean(selectedSubject && selectedFormat)
      : Boolean(selectedSubject && manualSections.length > 0 && manualSections.every((s) => s.name.trim() && s.slots.length > 0));

  /* ===================== FETCH INITIAL DATA ===================== */
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
            subjects.push({ id: tt.subject_version, name: tt.subject_name, className: tt.class_level_name || tt.class_level_display });
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
    if (selectedFormat && !formatsForType.some((f) => f.id === selectedFormat)) {
      setSelectedFormat("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paperType]);

  /* ===================== FETCH TOPICS FOR SELECTED SUBJECT ===================== */
  useEffect(() => {
    setSectionTopics({});
    setManualSections([newSection(0)]);
    if (!selectedSubject) {
      setTopics([]);
      return;
    }
    let cancelled = false;
    setTopicsLoading(true);
    api
      .get("/syllabus/learning-activities/", { params: { subject_version: selectedSubject } })
      .then((res) => {
        if (cancelled) return;
        setTopics(Array.isArray(res.data) ? res.data : res.data?.results || []);
      })
      .catch(() => {
        if (!cancelled) setTopics([]);
      })
      .finally(() => {
        if (!cancelled) setTopicsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedSubject]);

  /* ===================== FETCH CHOSEN FORMAT'S SECTIONS (AUTO MODE) ===================== */
  useEffect(() => {
    setSectionTopics({});
    if (!selectedFormat) {
      setFormatDetail(null);
      return;
    }
    let cancelled = false;
    setFormatDetailLoading(true);
    api
      .get(`/syllabus/exam-formats/${selectedFormat}/`)
      .then((res) => {
        if (!cancelled) setFormatDetail(res.data);
      })
      .catch(() => {
        if (!cancelled) setFormatDetail(null);
      })
      .finally(() => {
        if (!cancelled) setFormatDetailLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedFormat]);

  /* ===================== MANUAL MODE HELPERS ===================== */
  const addSection = useCallback(() => {
    setManualSections((prev) => [...prev, newSection(prev.length)]);
  }, []);
  const removeSection = useCallback((localId) => {
    setManualSections((prev) => prev.filter((s) => s.localId !== localId));
  }, []);
  const updateSection = useCallback((localId, patch) => {
    setManualSections((prev) => prev.map((s) => (s.localId === localId ? { ...s, ...patch } : s)));
  }, []);
  const addSlot = useCallback((sectionLocalId) => {
    setManualSections((prev) =>
      prev.map((s) => (s.localId === sectionLocalId ? { ...s, slots: [...s.slots, newSlot()] } : s))
    );
  }, []);
  const removeSlot = useCallback((sectionLocalId, slotLocalId) => {
    setManualSections((prev) =>
      prev.map((s) => (s.localId === sectionLocalId ? { ...s, slots: s.slots.filter((sl) => sl.localId !== slotLocalId) } : s))
    );
  }, []);
  const updateSlot = useCallback((sectionLocalId, slotLocalId, patch) => {
    setManualSections((prev) =>
      prev.map((s) =>
        s.localId === sectionLocalId
          ? { ...s, slots: s.slots.map((sl) => (sl.localId === slotLocalId ? { ...sl, ...patch } : sl)) }
          : s
      )
    );
  }, []);

  const manualTotalMarks = manualSections.reduce(
    (sum, s) => sum + s.slots.reduce((sSum, sl) => sSum + Number(sl.count || 0) * Number(sl.marks_per_item || 0), 0),
    0
  );
  const manualTotalQuestions = manualSections.reduce((sum, s) => sum + s.slots.reduce((sSum, sl) => sSum + Number(sl.count || 0), 0), 0);

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
      const basePayload = {
        subject_version: selectedSubject,
        title,
        year: year || null,
        term: term || null,
      };
      const payload =
        mode === "auto"
          ? {
              ...basePayload,
              exam_format: selectedFormat,
              section_topics: Object.entries(sectionTopics)
                .filter(([, ids]) => ids.length > 0)
                .map(([section, topic_ids]) => ({ section, topic_ids })),
            }
          : {
              ...basePayload,
              paper_type: paperType,
              time_allowed_minutes: manualTimeMinutes || null,
              instructions: manualInstructions,
              custom_sections: manualSections.map((s) => ({
                name: s.name,
                topic_ids: s.topicIds,
                slots: s.slots.map((sl) => ({
                  question_type: sl.question_type,
                  difficulty: sl.difficulty,
                  count: Number(sl.count) || 1,
                  marks_per_item: Number(sl.marks_per_item) || 1,
                })),
              })),
            };

      const res = await api.post("/syllabus/quiz/generate/", payload);
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
          data?.non_field_errors?.[0] ||
          (typeof data === "object" ? Object.values(data)[0] : null) ||
          t("quiz.error_generic");
        setError(Array.isArray(msg) ? msg[0] : msg);
        toast.error(Array.isArray(msg) ? msg[0] : msg);
      }
    } finally {
      setGenerating(false);
    }
  }, [
    isFormValid, mode, selectedSubject, selectedFormat, sectionTopics, paperType,
    manualTimeMinutes, manualInstructions, manualSections, title, year, term, t,
  ]);

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
        <button onClick={() => navigate(-1)} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" title={t("common.back")}>
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
          <button onClick={fetchInitialData} disabled={generating || downloading} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" title={t("common.refresh")}>
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
          <button onClick={() => navigate("/teaching/timetable")} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            {t("timetable.go_to_timetable")}
          </button>
        </div>
      )}

      {hasWorkstation && hasSubjects && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-4">
            {/* Paper type tabs */}
            <div className="flex gap-2">
              {PAPER_TYPES.map((pt) => (
                <button
                  key={pt}
                  onClick={() => setPaperType(pt)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${paperType === pt ? "bg-blue-600 text-white" : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"}`}
                >
                  {t(`quiz.paper_type.${pt}`)}
                </button>
              ))}
            </div>

            {/* Mode toggle */}
            <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700 pb-4">
              {["auto", "manual"].map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${mode === m ? "bg-indigo-600 text-white" : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"}`}
                >
                  {t(`quiz.mode.${m}`)}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 -mt-2">{t(`quiz.mode_hint.${mode}`)}</p>

            {/* Subject (shared) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t("quiz.subject_label")}</label>
              <select value={selectedSubject} onChange={(e) => setSelectedSubject(e.target.value)} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-2">
                <option value="">{t("quiz.choose_subject")}</option>
                {timetableSubjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} ({s.className})</option>
                ))}
              </select>
            </div>

            {/* ============ AUTO MODE ============ */}
            {mode === "auto" && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t("quiz.format_label")}</label>
                  <select value={selectedFormat} onChange={(e) => setSelectedFormat(e.target.value)} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-2">
                    <option value="">{t("quiz.choose_format")}</option>
                    {formatsForType.map((f) => (
                      <option key={f.id} value={f.id}>{f.name} ({f.total_marks} {t("quiz.marks")})</option>
                    ))}
                  </select>
                  {formatsForType.length === 0 && <p className="text-xs text-amber-600 mt-1">{t("quiz.no_formats_for_type")}</p>}
                </div>

                {selectedFormat && (
                  <div className="space-y-3">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{t("quiz.section_topics_label")}</p>
                    {formatDetailLoading ? (
                      <div className="text-sm text-gray-500">{t("common.loading")}...</div>
                    ) : (
                      formatDetail?.sections?.map((section) => (
                        <div key={section.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                          <p className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">{section.name}</p>
                          <TopicPicker
                            topics={topics}
                            loading={topicsLoading}
                            selectedIds={sectionTopics[section.id] || []}
                            onChange={(ids) => setSectionTopics((prev) => ({ ...prev, [section.id]: ids }))}
                          />
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ============ MANUAL MODE ============ */}
            {mode === "manual" && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t("quiz.time_minutes_label")}</label>
                    <input type="number" value={manualTimeMinutes} onChange={(e) => setManualTimeMinutes(e.target.value)} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-2" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t("quiz.instructions_label")}</label>
                    <input type="text" value={manualInstructions} onChange={(e) => setManualInstructions(e.target.value)} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-2" />
                  </div>
                </div>

                <div className="space-y-4">
                  {manualSections.map((section, si) => (
                    <div key={section.localId} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-3">
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={section.name}
                          onChange={(e) => updateSection(section.localId, { name: e.target.value })}
                          className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-2 font-medium"
                        />
                        {manualSections.length > 1 && (
                          <button type="button" onClick={() => removeSection(section.localId)} className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg" title={t("quiz.remove_section")}>
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>

                      {/* Slots */}
                      <div className="space-y-2">
                        {section.slots.map((slot) => (
                          <div key={slot.localId} className="grid grid-cols-2 md:grid-cols-5 gap-2 items-center">
                            <select value={slot.question_type} onChange={(e) => updateSlot(section.localId, slot.localId, { question_type: e.target.value })} className="rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-1.5 text-sm">
                              {QUESTION_TYPES.map((qt) => (
                                <option key={qt} value={qt}>{t(`quiz.question_type.${qt}`)}</option>
                              ))}
                            </select>
                            <select value={slot.difficulty} onChange={(e) => updateSlot(section.localId, slot.localId, { difficulty: e.target.value })} className="rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-1.5 text-sm">
                              {DIFFICULTIES.map((d) => (
                                <option key={d} value={d}>{t(`quiz.difficulty.${d}`)}</option>
                              ))}
                            </select>
                            <input
                              type="number" min={1} value={slot.count}
                              onChange={(e) => updateSlot(section.localId, slot.localId, { count: e.target.value })}
                              placeholder={t("quiz.slot_count")}
                              className="rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-1.5 text-sm"
                            />
                            <input
                              type="number" min={1} value={slot.marks_per_item}
                              onChange={(e) => updateSlot(section.localId, slot.localId, { marks_per_item: e.target.value })}
                              placeholder={t("quiz.slot_marks")}
                              className="rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-1.5 text-sm"
                            />
                            {section.slots.length > 1 && (
                              <button type="button" onClick={() => removeSlot(section.localId, slot.localId)} className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg justify-self-start">
                                <Trash2 size={14} />
                              </button>
                            )}
                          </div>
                        ))}
                        <button type="button" onClick={() => addSlot(section.localId)} className="flex items-center gap-1 text-xs text-blue-600 hover:underline">
                          <Plus size={12} /> {t("quiz.add_slot")}
                        </button>
                      </div>

                      {/* Topics for this section */}
                      <div>
                        <p className="text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">{t("quiz.topics_label")}</p>
                        <TopicPicker
                          topics={topics}
                          loading={topicsLoading}
                          selectedIds={section.topicIds}
                          onChange={(ids) => updateSection(section.localId, { topicIds: ids })}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                <button type="button" onClick={addSection} className="flex items-center gap-1.5 text-sm text-blue-600 hover:underline font-medium">
                  <Plus size={16} /> {t("quiz.add_section")}
                </button>

                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {t("quiz.manual_totals", { questions: manualTotalQuestions, marks: manualTotalMarks })}
                </p>
              </div>
            )}

            <button
              onClick={handleGenerate}
              disabled={!isFormValid || generating}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
            >
              <Sparkles size={18} />
              {generating ? t("quiz.generating") : t("quiz.generate_button")}
            </button>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-gray-200 dark:border-gray-700">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t("quiz.title_label")}</label>
                <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder={t("quiz.title_placeholder")} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-2" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t("quiz.year_label")}</label>
                  <input type="number" value={year} onChange={(e) => setYear(e.target.value)} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-2" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t("quiz.term_label")}</label>
                  <select value={term} onChange={(e) => setTerm(e.target.value)} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white p-2">
                    <option value="">-</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Shortfall error */}
          {shortfalls && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
              <h3 className="font-semibold text-red-700 dark:text-red-400 mb-2">{t("quiz.not_enough_questions")}</h3>
              <ul className="list-disc list-inside text-sm text-red-600 dark:text-red-300 space-y-1">
                {shortfalls.map((s, i) => (<li key={i}>{s}</li>))}
              </ul>
            </div>
          )}

          {/* Generated paper preview */}
          {paper && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{paper.title || paper.exam_format_name}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{paper.subject_name} • {paper.class_level_name}</p>
                </div>
                <button onClick={handleDownload} disabled={downloading} className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg text-sm font-medium">
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
                      {items.map((gpq) => (<li key={gpq.id}>{gpq.question_detail?.prompt}</li>))}
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
