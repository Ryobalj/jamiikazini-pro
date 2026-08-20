// src/app/syllabus/pages/MasterTimetablePage.jsx
import React, { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Plus, Download, Sparkles, Users, AlertTriangle, CheckCircle2 } from "lucide-react";
import { toast } from "react-toastify";
import api from "../../../lib/axios.js";

// This page never touches TimeTable / "Ratiba Yangu" - it's a
// self-contained tool for the teacher who builds the school's master
// schedule. Colleagues added here are lightweight roster entries (name
// + initials), not real accounts, so only the person who built this
// roster can view/export it.
export default function MasterTimetablePage() {
  const { t } = useTranslation("syllabus");

  const [rosters, setRosters] = useState([]);
  const [rosterId, setRosterId] = useState(null);
  const [loadingRosters, setLoadingRosters] = useState(true);
  const [newRosterName, setNewRosterName] = useState("");
  const [newRosterYear, setNewRosterYear] = useState(new Date().getFullYear());

  const [periodSlots, setPeriodSlots] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [subjectVersions, setSubjectVersions] = useState([]);
  const [activityTypes, setActivityTypes] = useState([]);
  const [grid, setGrid] = useState([]);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const [teacherForm, setTeacherForm] = useState({ full_name: "", initials: "" });
  const [assignForm, setAssignForm] = useState({ teacher: "", subject_version: "", periods_per_week_override: "" });
  const [blockForm, setBlockForm] = useState({ day_of_week: 1, period_slot: "", activity_type: "" });

  const [generating, setGenerating] = useState(false);
  const [generateResult, setGenerateResult] = useState(null);

  const [gridFilterTeacher, setGridFilterTeacher] = useState("");
  const [gridFilterClass, setGridFilterClass] = useState("");

  const roster = rosters.find((r) => r.id === rosterId) || null;
  const classLevels = Array.from(
    new Map(
      assignments.map((a) => [a.subject_version, { id: a.subject_version, name: a.class_level_name }])
    ).values()
  );

  // ---------------------------
  // ROSTERS
  // ---------------------------
  const loadRosters = useCallback(async () => {
    setLoadingRosters(true);
    try {
      const res = await api.get("/syllabus/master-timetable-rosters/");
      const data = Array.isArray(res.data) ? res.data : [];
      setRosters(data);
      if (data.length > 0 && !rosterId) setRosterId(data[0].id);
    } catch (err) {
      toast.error(t("master_timetable.load_error") || "Imeshindwa kupakia roster.");
    } finally {
      setLoadingRosters(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadRosters();
    api.get("/syllabus/timetable-activity-types/").then((res) => setActivityTypes(res.data || []));
  }, [loadRosters]);

  const createRoster = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post("/syllabus/master-timetable-rosters/", {
        name: newRosterName,
        year: Number(newRosterYear),
      });
      await api.post(`/syllabus/master-timetable-rosters/${res.data.id}/seed-default-periods/`);
      setNewRosterName("");
      setRosters((prev) => [res.data, ...prev]);
      setRosterId(res.data.id);
      toast.success(t("master_timetable.roster_created") || "Roster imeundwa.");
    } catch (err) {
      toast.error(
        err.response?.data?.year?.[0] ||
        err.response?.data?.detail ||
        t("master_timetable.create_error") || "Imeshindwa kuunda roster."
      );
    }
  };

  // ---------------------------
  // ROSTER DETAIL
  // ---------------------------
  const loadDetail = useCallback(async () => {
    if (!rosterId) return;
    setLoadingDetail(true);
    try {
      const [psRes, teachersRes, assignRes, gridRes] = await Promise.all([
        api.get("/syllabus/master-timetable-period-slots/", { params: { roster: rosterId } }),
        api.get("/syllabus/master-timetable-teachers/", { params: { roster: rosterId } }),
        api.get("/syllabus/master-timetable-assignments/", { params: { roster: rosterId } }),
        api.get(`/syllabus/master-timetable-rosters/${rosterId}/grid/`),
      ]);
      setPeriodSlots((psRes.data || []).sort((a, b) => a.order - b.order));
      setTeachers(teachersRes.data || []);
      setAssignments(assignRes.data || []);
      setGrid(gridRes.data || []);
    } catch (err) {
      toast.error(t("master_timetable.load_error") || "Imeshindwa kupakia taarifa za roster.");
    } finally {
      setLoadingDetail(false);
    }
  }, [rosterId, t]);

  useEffect(() => {
    loadDetail();
    setGenerateResult(null);
  }, [loadDetail]);

  // ---------------------------
  // SUBJECT SEARCH (for assignment form)
  // ---------------------------
  const searchSubjects = async (query) => {
    if (!query || query.trim().length < 2) {
      setSubjectVersions([]);
      return;
    }
    try {
      const res = await api.get("/syllabus/subject-versions-readonly/", {
        params: { search: query.trim(), limit: 20 },
      });
      const data = Array.isArray(res.data) ? res.data : res.data?.results || [];
      setSubjectVersions(data);
    } catch {
      setSubjectVersions([]);
    }
  };

  // ---------------------------
  // TEACHER / ASSIGNMENT / BLOCK ACTIONS
  // ---------------------------
  const addTeacher = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post("/syllabus/master-timetable-teachers/", {
        roster: rosterId,
        full_name: teacherForm.full_name,
        initials: teacherForm.initials.toUpperCase(),
      });
      setTeachers((prev) => [...prev, res.data]);
      setTeacherForm({ full_name: "", initials: "" });
    } catch (err) {
      toast.error(err.response?.data?.initials?.[0] || t("master_timetable.add_teacher_error") || "Imeshindwa kuongeza mwalimu.");
    }
  };

  const removeTeacher = async (id) => {
    try {
      await api.delete(`/syllabus/master-timetable-teachers/${id}/`);
      setTeachers((prev) => prev.filter((tt) => tt.id !== id));
      setAssignments((prev) => prev.filter((a) => a.teacher !== id));
    } catch {
      toast.error(t("master_timetable.remove_error") || "Imeshindwa kuondoa.");
    }
  };

  const addAssignment = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post("/syllabus/master-timetable-assignments/", {
        roster: rosterId,
        teacher: assignForm.teacher,
        subject_version: assignForm.subject_version,
        periods_per_week_override: assignForm.periods_per_week_override || null,
      });
      setAssignments((prev) => [...prev, res.data]);
      setAssignForm({ teacher: assignForm.teacher, subject_version: "", periods_per_week_override: "" });
      setSubjectVersions([]);
    } catch (err) {
      toast.error(
        err.response?.data?.[0] || err.response?.data?.detail ||
        t("master_timetable.add_assignment_error") || "Imeshindwa kugawa somo."
      );
    }
  };

  const removeAssignment = async (id) => {
    try {
      await api.delete(`/syllabus/master-timetable-assignments/${id}/`);
      setAssignments((prev) => prev.filter((a) => a.id !== id));
    } catch {
      toast.error(t("master_timetable.remove_error") || "Imeshindwa kuondoa.");
    }
  };

  const addBlock = async (e) => {
    e.preventDefault();
    try {
      await api.post("/syllabus/master-timetable-slots/", {
        roster: rosterId,
        day_of_week: Number(blockForm.day_of_week),
        period_slot: blockForm.period_slot,
        class_level: null,
        activity_type: blockForm.activity_type,
      });
      toast.success(t("master_timetable.block_added") || "Shughuli ya shule nzima imewekwa.");
      loadDetail();
    } catch (err) {
      toast.error(err.response?.data?.non_field_errors?.[0] || t("master_timetable.block_error") || "Imeshindwa kuweka shughuli.");
    }
  };

  // ---------------------------
  // GENERATE + GRID FILTER
  // ---------------------------
  const generate = async () => {
    setGenerating(true);
    setGenerateResult(null);
    try {
      const res = await api.post(`/syllabus/master-timetable-rosters/${rosterId}/generate/`);
      setGenerateResult(res.data);
      if (res.data.is_complete) {
        toast.success(t("master_timetable.generate_success") || "Ratiba imetengenezwa kikamilifu!");
      } else {
        toast.warning(t("master_timetable.generate_partial") || "Ratiba imetengenezwa - kuna migongano ya kutatua.");
      }
      loadDetail();
    } catch (err) {
      toast.error(t("master_timetable.generate_error") || "Imeshindwa kutengeneza ratiba.");
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    if (!rosterId) return;
    const params = {};
    if (gridFilterTeacher) params.teacher = gridFilterTeacher;
    if (gridFilterClass) params.class_level = gridFilterClass;
    api.get(`/syllabus/master-timetable-rosters/${rosterId}/grid/`, { params }).then((res) => setGrid(res.data || []));
  }, [rosterId, gridFilterTeacher, gridFilterClass]);

  const downloadFile = async (format) => {
    try {
      const params = { language: "sw" };
      if (gridFilterTeacher) params.teacher = gridFilterTeacher;
      if (gridFilterClass) params.class_level = gridFilterClass;
      const res = await api.get(`/syllabus/master-timetables/${rosterId}/${format}/`, {
        params, responseType: "blob",
      });
      const mime = format === "pdf" ? "application/pdf" : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
      const blob = new Blob([res.data], { type: mime });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${roster?.name || "Ratiba_Kuu"}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      if (err.response?.status === 403) {
        toast.error(t("subscription.required_for_pdf") || "Unahitaji kujiunga ili kupakua faili hii.");
      } else {
        toast.error(t("errors.failed_to_download") || "Imeshindwa kupakua faili.");
      }
    }
  };

  const daysOfWeek = [
    { value: 1, label: t("timetable.days.monday") },
    { value: 2, label: t("timetable.days.tuesday") },
    { value: 3, label: t("timetable.days.wednesday") },
    { value: 4, label: t("timetable.days.thursday") },
    { value: 5, label: t("timetable.days.friday") },
    { value: 6, label: t("timetable.days.saturday") },
  ];

  const gridByDay = grid.reduce((acc, s) => {
    (acc[s.day_of_week] ||= []).push(s);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">{t("master_timetable.title") || "Ratiba Kuu ya Shule"}</h1>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          {t("master_timetable.subtitle") ||
            "Ongeza walimu wenzako na masomo wanayofundisha, kisha tengeneza ratiba kiotomatiki. Hii ni tofauti na 'Ratiba Yangu' - unayoiona hapa ni yako pekee, kwa ajili ya kuchapisha/kupakua ratiba kuu ya shule."}
        </p>
      </div>

      {/* Roster picker/creator */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <select
            className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white"
            value={rosterId || ""}
            onChange={(e) => setRosterId(e.target.value)}
            disabled={loadingRosters}
          >
            <option value="">{t("common.select") || "Chagua..."}</option>
            {rosters.map((r) => (
              <option key={r.id} value={r.id}>{r.name} ({r.year})</option>
            ))}
          </select>
        </div>
        <form onSubmit={createRoster} className="flex flex-wrap items-end gap-2">
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
              {t("master_timetable.new_roster_name") || "Jina la Ratiba Mpya"}
            </label>
            <input
              type="text"
              value={newRosterName}
              onChange={(e) => setNewRosterName(e.target.value)}
              placeholder={t("master_timetable.roster_name_placeholder") || "Mfano: Ratiba Kuu 2026"}
              className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white"
              required
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">{t("scheme.year") || "Mwaka"}</label>
            <input
              type="number"
              value={newRosterYear}
              onChange={(e) => setNewRosterYear(e.target.value)}
              className="w-24 rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white"
              required
            />
          </div>
          <button type="submit" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700">
            <Plus size={16} /> {t("master_timetable.create_roster") || "Unda Roster"}
          </button>
        </form>
      </div>

      {rosterId && !loadingDetail && (
        <>
          {/* Teacher roster */}
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3">
            <h2 className="font-semibold flex items-center gap-2"><Users size={18} /> {t("master_timetable.teachers_heading") || "Walimu Wenzako"}</h2>
            <div className="flex flex-wrap gap-2">
              {teachers.map((tt) => (
                <span key={tt.id} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-700 text-sm">
                  {tt.full_name} ({tt.initials})
                  <button onClick={() => removeTeacher(tt.id)} className="ml-1 text-red-500 hover:text-red-700">×</button>
                </span>
              ))}
              {teachers.length === 0 && (
                <p className="text-sm text-gray-400">{t("master_timetable.no_teachers") || "Bado hujaongeza walimu."}</p>
              )}
            </div>
            <form onSubmit={addTeacher} className="flex flex-wrap items-end gap-2">
              <input
                type="text" placeholder={t("master_timetable.teacher_name") || "Jina Kamili"}
                value={teacherForm.full_name}
                onChange={(e) => setTeacherForm((p) => ({ ...p, full_name: e.target.value }))}
                className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white"
                required
              />
              <input
                type="text" placeholder={t("master_timetable.initials") || "Herufi (mf. DR)"}
                value={teacherForm.initials} maxLength={10}
                onChange={(e) => setTeacherForm((p) => ({ ...p, initials: e.target.value }))}
                className="w-32 rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white"
                required
              />
              <button type="submit" className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-700 text-white hover:bg-gray-800">
                <Plus size={16} /> {t("master_timetable.add_teacher") || "Ongeza"}
              </button>
            </form>
          </div>

          {/* Assignments */}
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3">
            <h2 className="font-semibold">{t("master_timetable.assignments_heading") || "Ugawaji wa Masomo"}</h2>
            <div className="space-y-1">
              {assignments.map((a) => (
                <div key={a.id} className="flex items-center justify-between text-sm p-2 rounded-lg bg-gray-50 dark:bg-gray-900">
                  <span>
                    <strong>{a.teacher_initials}</strong> — {a.subject_name} ({a.class_level_name}) —{" "}
                    {a.effective_periods_per_week} {t("master_timetable.periods_per_week") || "vipindi/wiki"}
                  </span>
                  <button onClick={() => removeAssignment(a.id)} className="text-red-500 hover:text-red-700">×</button>
                </div>
              ))}
              {assignments.length === 0 && (
                <p className="text-sm text-gray-400">{t("master_timetable.no_assignments") || "Bado hakuna ugawaji wa masomo."}</p>
              )}
            </div>
            <form onSubmit={addAssignment} className="flex flex-wrap items-end gap-2">
              <select
                value={assignForm.teacher}
                onChange={(e) => setAssignForm((p) => ({ ...p, teacher: e.target.value }))}
                className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white"
                required
              >
                <option value="">{t("master_timetable.pick_teacher") || "Chagua Mwalimu"}</option>
                {teachers.map((tt) => (
                  <option key={tt.id} value={tt.id}>{tt.full_name} ({tt.initials})</option>
                ))}
              </select>
              <div className="relative">
                <input
                  type="text"
                  placeholder={t("timetable.subject_placeholder") || "Tafuta somo..."}
                  onChange={(e) => searchSubjects(e.target.value)}
                  className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white"
                />
                {subjectVersions.length > 0 && (
                  <ul className="absolute z-10 mt-1 w-64 max-h-48 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-lg">
                    {subjectVersions.map((sv) => (
                      <li
                        key={sv.id}
                        onClick={() => { setAssignForm((p) => ({ ...p, subject_version: sv.id })); setSubjectVersions([]); }}
                        className="px-3 py-2 text-sm cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20"
                      >
                        {sv.subject_name || sv.subject?.name} ({sv.class_level_name || sv.class_level?.name})
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <input
                type="number" placeholder={t("master_timetable.override_periods") || "Vipindi/wiki (hiari)"}
                value={assignForm.periods_per_week_override}
                onChange={(e) => setAssignForm((p) => ({ ...p, periods_per_week_override: e.target.value }))}
                className="w-40 rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white"
              />
              <button
                type="submit"
                disabled={!assignForm.teacher || !assignForm.subject_version}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-700 text-white hover:bg-gray-800 disabled:opacity-50"
              >
                <Plus size={16} /> {t("master_timetable.add_assignment") || "Gawa"}
              </button>
            </form>
          </div>

          {/* Whole-school activity blocks */}
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3">
            <h2 className="font-semibold">{t("master_timetable.blocks_heading") || "Shughuli za Shule Nzima"}</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {t("master_timetable.blocks_help") || "Weka hizi kabla ya kutengeneza ratiba (mfano: Ijumaa Dini) - hazitabadilishwa na uzalishaji wa kiotomatiki."}
            </p>
            <form onSubmit={addBlock} className="flex flex-wrap items-end gap-2">
              <select
                value={blockForm.day_of_week}
                onChange={(e) => setBlockForm((p) => ({ ...p, day_of_week: e.target.value }))}
                className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white"
              >
                {daysOfWeek.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
              </select>
              <select
                value={blockForm.period_slot}
                onChange={(e) => setBlockForm((p) => ({ ...p, period_slot: e.target.value }))}
                className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white"
                required
              >
                <option value="">{t("master_timetable.pick_period") || "Chagua Kipindi"}</option>
                {periodSlots.filter((ps) => !ps.is_break).map((ps) => (
                  <option key={ps.id} value={ps.id}>{ps.label}</option>
                ))}
              </select>
              <select
                value={blockForm.activity_type}
                onChange={(e) => setBlockForm((p) => ({ ...p, activity_type: e.target.value }))}
                className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white"
                required
              >
                <option value="">{t("master_timetable.pick_activity") || "Chagua Shughuli"}</option>
                {activityTypes.filter((a) => !a.is_fixed_routine).map((a) => (
                  <option key={a.id} value={a.id}>{a.label_sw}</option>
                ))}
              </select>
              <button type="submit" className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-700 text-white hover:bg-gray-800">
                <Plus size={16} /> {t("master_timetable.add_block") || "Weka"}
              </button>
            </form>
          </div>

          {/* Generate */}
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3">
            <button
              onClick={generate}
              disabled={generating || assignments.length === 0}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50"
            >
              <Sparkles size={16} /> {generating ? t("common.loading") : (t("master_timetable.generate") || "Tengeneza Ratiba")}
            </button>

            {generateResult && (
              <div className={`p-3 rounded-lg ${generateResult.is_complete ? "bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800" : "bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800"}`}>
                <p className="flex items-center gap-2 text-sm font-medium">
                  {generateResult.is_complete
                    ? <><CheckCircle2 size={16} className="text-green-600" /> {t("master_timetable.all_placed", { count: generateResult.placed_count }) || `Vipindi vyote ${generateResult.placed_count} vimewekwa kikamilifu.`}</>
                    : <><AlertTriangle size={16} className="text-amber-600" /> {t("master_timetable.some_unplaced") || "Baadhi ya vipindi havikuwekwa - angalia migongano hapa chini:"}</>
                  }
                </p>
                {!generateResult.is_complete && (
                  <ul className="mt-2 text-sm space-y-1">
                    {generateResult.unplaced.map((u, i) => (
                      <li key={i} className="text-amber-700 dark:text-amber-300">
                        {u.teacher_name} — {u.subject_name} ({u.class_level_name}): {t("master_timetable.periods_short", { count: u.periods_short }) || `vipindi ${u.periods_short} havikupata nafasi`}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>

          {/* Master grid */}
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-semibold">{t("master_timetable.grid_heading") || "Ratiba Kuu"}</h2>
              <div className="flex flex-wrap items-center gap-2">
                <select
                  value={gridFilterTeacher}
                  onChange={(e) => setGridFilterTeacher(e.target.value)}
                  className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-1.5 text-sm dark:bg-gray-700 dark:text-white"
                >
                  <option value="">{t("master_timetable.all_teachers") || "Walimu Wote"}</option>
                  {teachers.map((tt) => <option key={tt.id} value={tt.id}>{tt.initials}</option>)}
                </select>
                <select
                  value={gridFilterClass}
                  onChange={(e) => setGridFilterClass(e.target.value)}
                  className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-1.5 text-sm dark:bg-gray-700 dark:text-white"
                >
                  <option value="">{t("master_timetable.all_classes") || "Madarasa Yote"}</option>
                  {classLevels.map((cl) => <option key={cl.id} value={cl.id}>{cl.name}</option>)}
                </select>
                <button onClick={() => downloadFile("pdf")} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-sm hover:bg-gray-50 dark:hover:bg-gray-700">
                  <Download size={14} /> PDF
                </button>
                <button onClick={() => downloadFile("xlsx")} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-sm hover:bg-gray-50 dark:hover:bg-gray-700">
                  <Download size={14} /> XLSX
                </button>
              </div>
            </div>

            {grid.length === 0 ? (
              <p className="text-sm text-gray-400">{t("master_timetable.no_grid") || "Bado hakuna ratiba - bofya 'Tengeneza Ratiba' hapo juu."}</p>
            ) : (
              <div className="space-y-4">
                {daysOfWeek.map((d) => {
                  const dayItems = gridByDay[d.value];
                  if (!dayItems || dayItems.length === 0) return null;
                  return (
                    <div key={d.value}>
                      <h3 className="text-sm font-semibold mb-1">{d.label}</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-xs border border-gray-200 dark:border-gray-700">
                          <tbody>
                            {dayItems
                              .sort((a, b) => (a.class_level_name || "").localeCompare(b.class_level_name || ""))
                              .map((s) => (
                                <tr key={s.id} className="border-t border-gray-100 dark:border-gray-800">
                                  <td className="px-2 py-1 font-medium">{s.class_level_name || (t("master_timetable.whole_school") || "Shule Nzima")}</td>
                                  <td className="px-2 py-1">
                                    {s.subject_name ? `${s.subject_name} (${s.teacher_initials})` : (s.activity_label || s.custom_label)}
                                  </td>
                                </tr>
                              ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
