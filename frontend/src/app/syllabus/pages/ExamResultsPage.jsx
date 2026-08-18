// src/app/syllabus/pages/ExamResultsPage.jsx
import React, { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import { Plus, Download, Save } from "lucide-react";
import api from "../../../lib/axios.js";
import WorkstationFormModal from "../components/WorkstationFormModal.jsx";

export default function ExamResultsPage() {
  const { t } = useTranslation("syllabus");

  const inputClass =
    "w-full rounded-lg border px-3 py-2 border-gray-300 dark:border-gray-600 " +
    "bg-white dark:bg-gray-700 text-gray-900 dark:text-white " +
    "focus:outline-none focus:ring-2 focus:ring-blue-500";

  const [workstation, setWorkstation] = useState(null);
  const [classLevels, setClassLevels] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [exams, setExams] = useState([]);
  const [selectedExamId, setSelectedExamId] = useState("");
  const [students, setStudents] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pdfLoading, setPdfLoading] = useState(null);
  const [pdfSubjectId, setPdfSubjectId] = useState("");

  const [examForm, setExamForm] = useState({
    class_level: "", subjects: [], name: "Upimaji wa Nusu Muhula", term: 1, year: new Date().getFullYear(), max_score_per_subject: 50,
  });
  const [studentForm, setStudentForm] = useState({ full_name: "", gender: "F" });
  const [marksGrid, setMarksGrid] = useState({});

  const selectedExam = exams.find((e) => e.id === selectedExamId) || null;

  const loadBaseData = useCallback(async () => {
    setLoading(true);
    try {
      const wsRes = await api.get("/syllabus/teacher-workstations/");
      const ws = Array.isArray(wsRes.data) ? wsRes.data[0] : null;
      setWorkstation(ws || null);
      if (!ws) return;

      const [clRes, subRes, examRes] = await Promise.all([
        api.get("/syllabus/class-levels/"),
        api.get("/syllabus/subjects/"),
        api.get("/syllabus/exams/", { params: { workstation: ws.id } }),
      ]);
      setClassLevels(Array.isArray(clRes.data) ? clRes.data : clRes.data?.results || []);
      setSubjects(Array.isArray(subRes.data) ? subRes.data : subRes.data?.results || []);
      const examList = Array.isArray(examRes.data) ? examRes.data : examRes.data?.results || [];
      setExams(examList);
      if (examList.length > 0) setSelectedExamId(examList[0].id);
    } catch (err) {
      console.error(err);
      toast.error(t("errors.failed_to_load"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    loadBaseData();
  }, [loadBaseData]);

  const loadExamData = useCallback(async () => {
    if (!selectedExam || !workstation) {
      setStudents([]);
      setResults(null);
      return;
    }
    try {
      const [studRes, marksRes, resultsRes] = await Promise.all([
        api.get("/syllabus/students/", { params: { workstation: workstation.id, class_level: selectedExam.class_level } }),
        api.get(`/syllabus/exams/${selectedExam.id}/marks/`),
        api.get(`/syllabus/exams/${selectedExam.id}/results/`),
      ]);
      const studentList = Array.isArray(studRes.data) ? studRes.data : studRes.data?.results || [];
      setStudents(studentList);
      setResults(resultsRes.data);

      const grid = {};
      const marksList = Array.isArray(marksRes.data) ? marksRes.data : [];
      marksList.forEach((m) => {
        grid[`${m.student}_${m.subject}`] = m.score;
      });
      setMarksGrid(grid);
      if (selectedExam.subjects?.length) setPdfSubjectId(selectedExam.subjects[0]);
    } catch (err) {
      console.error(err);
      toast.error(t("errors.failed_to_load"));
    }
  }, [selectedExam, workstation, t]);

  useEffect(() => {
    loadExamData();
  }, [loadExamData]);

  const handleCreateExam = async (e) => {
    e.preventDefault();
    if (!workstation) return;
    try {
      const res = await api.post("/syllabus/exams/", {
        workstation: workstation.id,
        class_level: examForm.class_level,
        subjects: examForm.subjects,
        name: examForm.name,
        term: examForm.term,
        year: examForm.year,
        max_score_per_subject: examForm.max_score_per_subject,
      });
      setExams((prev) => [res.data, ...prev]);
      setSelectedExamId(res.data.id);
      toast.success(t("exam_results.exam_created") || "Mtihani umeundwa.");
    } catch (err) {
      console.error(err);
      toast.error(t("errors.failed_to_save"));
    }
  };

  const handleAddStudent = async (e) => {
    e.preventDefault();
    if (!workstation || !selectedExam) return;
    try {
      const res = await api.post("/syllabus/students/", {
        workstation: workstation.id,
        class_level: selectedExam.class_level,
        full_name: studentForm.full_name,
        gender: studentForm.gender,
      });
      setStudents((prev) => [...prev, res.data]);
      setStudentForm({ full_name: "", gender: "F" });
    } catch (err) {
      console.error(err);
      toast.error(t("errors.failed_to_save"));
    }
  };

  const handleScoreChange = (studentId, subjectId, value) => {
    setMarksGrid((prev) => ({ ...prev, [`${studentId}_${subjectId}`]: value }));
  };

  const handleSaveMarks = async () => {
    if (!selectedExam) return;
    const entries = [];
    students.forEach((s) => {
      (selectedExam.subjects || []).forEach((subjId) => {
        const value = marksGrid[`${s.id}_${subjId}`];
        if (value !== undefined && value !== "") {
          entries.push({ student: s.id, subject: subjId, score: value });
        }
      });
    });
    if (entries.length === 0) return;
    try {
      await api.post(`/syllabus/exams/${selectedExam.id}/marks/`, entries);
      toast.success(t("exam_results.marks_saved") || "Alama zimehifadhiwa.");
      const resultsRes = await api.get(`/syllabus/exams/${selectedExam.id}/results/`);
      setResults(resultsRes.data);
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.[0] || t("errors.failed_to_save"));
    }
  };

  const EXAM_URLS = {
    pdf: {
      class: (id) => `/syllabus/exams/pdf/class-report/?exam_id=${id}`,
      subject: (id, subjId) => `/syllabus/exams/pdf/subject/?exam_id=${id}&subject_id=${subjId}`,
    },
    xlsx: {
      class: (id) => `/syllabus/exams/xlsx/class-report/?exam_id=${id}`,
      subject: (id, subjId) => `/syllabus/exams/xlsx/subject/?exam_id=${id}&subject_id=${subjId}`,
    },
  };
  const EXAM_MIME_TYPES = {
    pdf: "application/pdf",
    xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  };

  const downloadFile = async (kind, format) => {
    if (!selectedExam) return;
    const loadingKey = `${kind}_${format}`;
    setPdfLoading(loadingKey);
    try {
      const url = kind === "class"
        ? EXAM_URLS[format].class(selectedExam.id)
        : EXAM_URLS[format].subject(selectedExam.id, pdfSubjectId);
      const response = await api.get(url, { responseType: "blob" });
      const blob = new Blob([response.data], { type: EXAM_MIME_TYPES[format] });
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `Matokeo.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      if (err.response?.status === 403) {
        toast.error(t("subscription.required_for_pdf"));
      } else {
        toast.error(t("errors.failed_to_download"));
      }
    } finally {
      setPdfLoading(null);
    }
  };

  if (loading) return <p className="p-6 text-sm text-gray-500">{t("common.loading")}...</p>;

  if (!workstation) {
    // The syllabus-wide route guard should already prevent reaching this page
    // without a workstation; this is a defensive fallback (e.g. workstation
    // deleted mid-session) that still lets the teacher set one up here
    // instead of stranding them on a dead-end message.
    return <WorkstationFormModal open={true} onSubmit={() => loadBaseData()} />;
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold">{t("exam_results.title")}</h1>
        <p className="text-sm text-gray-600 dark:text-gray-300">{t("exam_results.subtitle")}</p>
      </div>

      {/* Exam picker + create form */}
      <div className="border rounded-lg p-4 space-y-3">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="text-sm font-medium">{t("exam_results.select_exam")}</label>
            <select className={inputClass} value={selectedExamId} onChange={(e) => setSelectedExamId(e.target.value)}>
              <option value="">{t("common.select")}</option>
              {exams.map((ex) => (
                <option key={ex.id} value={ex.id}>{ex.name} - {ex.class_level_name} ({ex.term_display} {ex.year})</option>
              ))}
            </select>
          </div>
        </div>

        <form onSubmit={handleCreateExam} className="grid grid-cols-1 sm:grid-cols-3 gap-3 border-t pt-3">
          <div>
            <label className="text-sm font-medium">{t("exam_results.class_level")}</label>
            <select className={inputClass} value={examForm.class_level} onChange={(e) => setExamForm((p) => ({ ...p, class_level: e.target.value }))} required>
              <option value="">{t("common.select")}</option>
              {classLevels.map((cl) => <option key={cl.id} value={cl.id}>{cl.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium">{t("exam_results.subjects")}</label>
            <select
              multiple
              className={inputClass}
              value={examForm.subjects}
              onChange={(e) => setExamForm((p) => ({ ...p, subjects: Array.from(e.target.selectedOptions, (o) => o.value) }))}
              required
            >
              {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-2">
            <div>
              <label className="text-sm font-medium">{t("exam_results.exam_name")}</label>
              <input className={inputClass} value={examForm.name} onChange={(e) => setExamForm((p) => ({ ...p, name: e.target.value }))} />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <select className={inputClass} value={examForm.term} onChange={(e) => setExamForm((p) => ({ ...p, term: Number(e.target.value) }))}>
                <option value={1}>{t("exam_results.term1")}</option>
                <option value={2}>{t("exam_results.term2")}</option>
              </select>
              <input type="number" className={inputClass} value={examForm.year} onChange={(e) => setExamForm((p) => ({ ...p, year: Number(e.target.value) }))} />
            </div>
          </div>
          <button type="submit" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 w-fit">
            <Plus size={16} /> {t("exam_results.create_exam")}
          </button>
        </form>
      </div>

      {selectedExam && (
        <>
          {/* Add student */}
          <div className="border rounded-lg p-4">
            <h2 className="font-semibold mb-2">{t("exam_results.students")}</h2>
            <form onSubmit={handleAddStudent} className="flex flex-wrap items-end gap-3 mb-4">
              <input
                className={inputClass}
                placeholder={t("exam_results.student_name")}
                value={studentForm.full_name}
                onChange={(e) => setStudentForm((p) => ({ ...p, full_name: e.target.value }))}
                required
              />
              <select className={inputClass} value={studentForm.gender} onChange={(e) => setStudentForm((p) => ({ ...p, gender: e.target.value }))}>
                <option value="F">{t("exam_results.female")}</option>
                <option value="M">{t("exam_results.male")}</option>
              </select>
              <button type="submit" className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border hover:bg-gray-50 dark:hover:bg-gray-700">
                <Plus size={16} /> {t("exam_results.add_student")}
              </button>
            </form>

            {/* Marks grid */}
            {students.length > 0 && (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm border-collapse">
                  <thead className="bg-gray-100 dark:bg-gray-800">
                    <tr>
                      <th className="border px-2 py-1">{t("exam_results.student_name")}</th>
                      {(selectedExam.subjects || []).map((subjId) => (
                        <th key={subjId} className="border px-2 py-1">
                          {subjects.find((s) => s.id === subjId)?.name || subjId}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {students.map((s) => (
                      <tr key={s.id}>
                        <td className="border px-2 py-1">{s.full_name}</td>
                        {(selectedExam.subjects || []).map((subjId) => (
                          <td key={subjId} className="border px-1 py-1">
                            <input
                              type="number"
                              step="0.5"
                              min="0"
                              max={selectedExam.max_score_per_subject}
                              className="w-20 rounded border px-1 py-0.5 bg-white dark:bg-gray-700"
                              value={marksGrid[`${s.id}_${subjId}`] ?? ""}
                              onChange={(e) => handleScoreChange(s.id, subjId, e.target.value)}
                            />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                <button
                  onClick={handleSaveMarks}
                  className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700"
                >
                  <Save size={16} /> {t("exam_results.save_marks")}
                </button>
              </div>
            )}
          </div>

          {/* Results preview */}
          {results && results.students?.length > 0 && (
            <div className="border rounded-lg p-4 overflow-x-auto">
              <h2 className="font-semibold mb-2">{t("exam_results.results_preview")}</h2>
              <table className="min-w-full text-sm border-collapse">
                <thead className="bg-gray-100 dark:bg-gray-800">
                  <tr>
                    <th className="border px-2 py-1">{t("exam_results.student_name")}</th>
                    <th className="border px-2 py-1">{t("exam_results.total")}</th>
                    <th className="border px-2 py-1">{t("exam_results.average")}</th>
                    <th className="border px-2 py-1">{t("exam_results.grade")}</th>
                    <th className="border px-2 py-1">{t("exam_results.rank")}</th>
                  </tr>
                </thead>
                <tbody>
                  {results.students.map((r) => (
                    <tr key={r.student_id}>
                      <td className="border px-2 py-1">{r.student_name}</td>
                      <td className="border px-2 py-1">{r.total ?? "-"}</td>
                      <td className="border px-2 py-1">{r.average ? Number(r.average).toFixed(2) : "-"}</td>
                      <td className="border px-2 py-1">{r.overall_grade ?? "-"}</td>
                      <td className="border px-2 py-1">{r.overall_rank ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* PDF downloads */}
          <div className="border rounded-lg p-4 flex flex-wrap items-end gap-3">
            <div>
              <label className="text-sm font-medium">{t("exam_results.subject_for_pdf")}</label>
              <select className={inputClass} value={pdfSubjectId} onChange={(e) => setPdfSubjectId(e.target.value)}>
                {(selectedExam.subjects || []).map((subjId) => (
                  <option key={subjId} value={subjId}>{subjects.find((s) => s.id === subjId)?.name || subjId}</option>
                ))}
              </select>
            </div>
            <button
              onClick={() => downloadFile("subject", "pdf")}
              disabled={pdfLoading !== null || !pdfSubjectId}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
            >
              <Download size={16} /> {pdfLoading === "subject_pdf" ? t("common.loading") : t("exam_results.download_subject_pdf")}
            </button>
            <button
              onClick={() => downloadFile("subject", "xlsx")}
              disabled={pdfLoading !== null || !pdfSubjectId}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
            >
              <Download size={16} /> {pdfLoading === "subject_xlsx" ? t("common.loading") : t("exam_results.download_subject_xlsx")}
            </button>
            <button
              onClick={() => downloadFile("class", "pdf")}
              disabled={pdfLoading !== null}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
            >
              <Download size={16} /> {pdfLoading === "class_pdf" ? t("common.loading") : t("exam_results.download_class_pdf")}
            </button>
            <button
              onClick={() => downloadFile("class", "xlsx")}
              disabled={pdfLoading !== null}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
            >
              <Download size={16} /> {pdfLoading === "class_xlsx" ? t("common.loading") : t("exam_results.download_class_xlsx")}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
