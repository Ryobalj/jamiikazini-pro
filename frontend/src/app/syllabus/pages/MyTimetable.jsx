// src/app/syllabus/pages/MyTimetable.jsx
import React, { useEffect, useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Plus, Download } from "lucide-react";
import { toast } from "react-toastify";

// Components
import TimetableGroup from "../components/TimetableGroup";
import TimetableWeekGrid from "../components/TimetableWeekGrid";
import EmptyTimetableState from "../components/EmptyTimetableState";
import TimetableFormModal from "../components/TimetableFormModal";
import WorkstationFormModal from "../components/WorkstationFormModal";

// Lib
import api from "../../../lib/axios.js";

export default function MyTimetable() {
  const { t } = useTranslation("syllabus");

  const [loading, setLoading] = useState(true);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState(null);

  const [timetables, setTimetables] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [workstation, setWorkstation] = useState(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingRow, setEditingRow] = useState(null);
  const [workstationModalOpen, setWorkstationModalOpen] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(null);

  const TIMETABLE_URLS = {
    pdf: { mine: "/syllabus/timetables/pdf/", school: "/syllabus/timetables/school-pdf/" },
    xlsx: { mine: "/syllabus/timetables/xlsx/", school: "/syllabus/timetables/school-xlsx/" },
  };
  const MIME_TYPES = {
    pdf: "application/pdf",
    xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  };

  const downloadTimetableFile = async (scope, format) => {
    const loadingKey = `${scope}_${format}`;
    setPdfLoading(loadingKey);
    try {
      const url = TIMETABLE_URLS[format][scope];
      const response = await api.get(url, { responseType: "blob" });
      const blob = new Blob([response.data], { type: MIME_TYPES[format] });
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `${scope === "school" ? "Ratiba_Kuu" : "Ratiba_Yangu"}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      if (err.response?.status === 403) {
        toast.error(t("subscription.required_for_pdf") || "Unahitaji kujiunga ili kupakua faili hii.");
      } else {
        toast.error(t("errors.failed_to_download") || "Imeshindwa kupakua faili.");
      }
    } finally {
      setPdfLoading(null);
    }
  };

  // ---------------------------
  // FETCH WORKSTATION & TIMETABLES
  // ---------------------------
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 1️⃣ Pata workstation ya user
      const wsRes = await api.get("/syllabus/teacher-workstations/");
      const wsData = Array.isArray(wsRes.data) ? wsRes.data : [];

      if (wsData.length === 0) {
        setWorkstationModalOpen(true);
        setWorkstation(null);
        setTimetables([]);
        setSubjects([]);
        return;
      }

      const userWs = wsData[0]; // OneToOne, mwalimu ana workstation moja tu
      setWorkstation(userWs);

      // 2️⃣ Pata timetables zote za workstation hiyo
      const ttRes = await api.get("/syllabus/timetables/", {
        params: { workstation: userWs.id },
      });
      const ttData = Array.isArray(ttRes.data) ? ttRes.data : [];
      setTimetables(ttData);

      // 3️⃣ Pata subject versions kwa workstation hiyo (haihitajiki kuonyesha
      // ratiba - ikishindwa (mfano 403 kwa mwalimu wa kawaida) isizuie ukurasa
      // mzima kuonekana).
      try {
        const subjRes = await api.get("/syllabus/subject-versions/", {
          params: { timetable: userWs.id },
        });
        const subjData = Array.isArray(subjRes.data) ? subjRes.data : [];
        setSubjects(subjData);
      } catch (subjErr) {
        console.error(subjErr);
        setSubjects([]);
      }

      // Open timetable modal if none exists
      if (ttData.length === 0) setModalOpen(true);
    } catch (err) {
      console.error(err);
      if (err.response?.status === 429) {
        setError(t("my_timetable.too_many_requests") || "Umepiga requests nyingi. Subiri kidogo kisha jaribu tena.");
      } else {
        setError(t("errors.failed_to_load"));
      }
    } finally {
      setLoading(false);
      setInitialLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // ---------------------------
  // Group timetable by subject + class
  // ---------------------------
  const grouped = useMemo(() => {
    return timetables.reduce((acc, item) => {
      const key = `${item.subject_display}-${item.class_level_display}`;
      acc[key] ||= {
        subjectName: item.subject_display,
        className: item.class_level_display,
        rows: [],
      };
      acc[key].rows.push(item);
      return acc;
    }, {});
  }, [timetables]);

  // ---------------------------
  // MODAL HANDLERS
  // ---------------------------
  const openAddModal = () => {
    setEditingRow(null);
    setModalOpen(true);
  };

  const openEditModal = (row) => {
    setEditingRow(row);
    setModalOpen(true);
  };

  const handleDelete = async (row) => {
    try {
      await api.delete(`/syllabus/timetables/${row.id}/`);
      setTimetables((prev) => prev.filter((t) => t.id !== row.id));
    } catch (err) {
      console.error(err);
      alert(t("errors.failed_to_delete"));
    }
  };

  const handleTimetableSubmit = async (data) => {
    if (editingRow) {
      const res = await api.patch(`/syllabus/timetables/${editingRow.id}/`, data);
      setTimetables((prev) =>
        prev.map((t) => (t.id === editingRow.id ? res.data : t))
      );
    } else {
      const res = await api.post("/syllabus/timetables/", data);
      setTimetables((prev) => [...prev, res.data]);
    }
    setModalOpen(false);
  };

  const handleWorkstationSubmit = (ws) => {
    setWorkstation(ws);
    setWorkstationModalOpen(false);
    setModalOpen(true);
  };

  const hasWorkstation = !!workstation;

  // ---------------------------
  // RENDER
  // ---------------------------
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">{t("my_timetable.title")}</h1>
          <p className="text-sm text-gray-600 dark:text-gray-300">{t("my_timetable.subtitle")}</p>
        </div>

        {hasWorkstation && (
          <div className="flex flex-wrap items-center gap-2">
            <button
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
              onClick={() => downloadTimetableFile("mine", "pdf")}
              disabled={pdfLoading !== null || timetables.length === 0}
            >
              <Download size={16} />
              {pdfLoading === "mine_pdf" ? t("common.loading") : t("timetable.download_mine")}
            </button>
            <button
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
              onClick={() => downloadTimetableFile("mine", "xlsx")}
              disabled={pdfLoading !== null || timetables.length === 0}
            >
              <Download size={16} />
              {pdfLoading === "mine_xlsx" ? t("common.loading") : t("timetable.download_mine_xlsx")}
            </button>
            <button
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
              onClick={() => downloadTimetableFile("school", "pdf")}
              disabled={pdfLoading !== null}
            >
              <Download size={16} />
              {pdfLoading === "school_pdf" ? t("common.loading") : t("timetable.download_school")}
            </button>
            <button
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
              onClick={() => downloadTimetableFile("school", "xlsx")}
              disabled={pdfLoading !== null}
            >
              <Download size={16} />
              {pdfLoading === "school_xlsx" ? t("common.loading") : t("timetable.download_school_xlsx")}
            </button>
            <button
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
              onClick={openAddModal}
            >
              <Plus size={16} />
              {t("my_timetable.add")}
            </button>
          </div>
        )}
      </div>

      {/* Loading / Error */}
      {loading && <p className="text-sm text-gray-500">{t("common.loading")}...</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* Empty state */}
      {!loading && !error && timetables.length === 0 && hasWorkstation && (
        <EmptyTimetableState t={t} />
      )}

      {/* Weekly Grid */}
      {!loading && !error && timetables.length > 0 && (
        <div>
          <h2 className="font-semibold mb-2">{t("timetable.weekly_schedule")}</h2>
          <TimetableWeekGrid timetables={timetables} t={t} onEdit={openEditModal} />
        </div>
      )}

      {/* Timetable Groups */}
      {!loading && !error &&
        Object.values(grouped).map((group) => (
          <TimetableGroup
            key={`${group.subjectName}-${group.className}`}
            group={group}
            t={t}
            onEdit={openEditModal}
            onDelete={handleDelete}
          />
        ))}

      {/* Timetable Modal */}
      {hasWorkstation && !initialLoading && (
        <TimetableFormModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          initialData={editingRow}
          onSubmit={handleTimetableSubmit}
          subjects={subjects}
          workstations={workstation ? [workstation] : []}
        />
      )}

      {/* Workstation Modal */}
      {!initialLoading && (
        <WorkstationFormModal
          open={workstationModalOpen}
          onClose={() => setWorkstationModalOpen(false)}
          onSubmit={handleWorkstationSubmit}
        />
      )}
    </div>
  );
}