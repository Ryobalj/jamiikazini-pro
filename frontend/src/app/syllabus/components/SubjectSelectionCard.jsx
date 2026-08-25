// src/app/syllabus/components/SubjectSelectionCard.jsx
import React, { useState } from "react";
import { Pencil, Check, X } from "lucide-react";
import { toast } from "react-toastify";
import api from "@/lib/axios";

const SubjectSelectionCard = ({
  timetables,
  selectedTimetable,
  setSelectedTimetable,
  setForm,
  currentSubjectInfo,
  t
}) => {
  const [editingRegistered, setEditingRegistered] = useState(false);
  const [regBoys, setRegBoys] = useState("");
  const [regGirls, setRegGirls] = useState("");
  const [savingRegistered, setSavingRegistered] = useState(false);

  const startEditRegistered = () => {
    setRegBoys(String(currentSubjectInfo?.registeredBoys ?? 0));
    setRegGirls(String(currentSubjectInfo?.registeredGirls ?? 0));
    setEditingRegistered(true);
  };

  const cancelEditRegistered = () => {
    setEditingRegistered(false);
  };

  const saveRegistered = async () => {
    if (!selectedTimetable) return;
    setSavingRegistered(true);
    try {
      const res = await api.patch(`/syllabus/timetables/${selectedTimetable.id}/`, {
        registeredboys: Number(regBoys) || 0,
        registeredgirls: Number(regGirls) || 0,
      });
      setSelectedTimetable(res.data);
      setEditingRegistered(false);
      toast.success(t("common.update_success"));
    } catch (err) {
      console.error(err);
      toast.error(t("common.error"));
    } finally {
      setSavingRegistered(false);
    }
  };

  const handleTimetableChange = (e) => {
    // TimeTable.id is a UUID string, not a numeric id - comparing with
    // Number(e.target.value) always produces NaN and never matches,
    // silently leaving selectedTimetable unset no matter what the
    // teacher picks (breaking every downstream Learning Activity load).
    const timetable = timetables.find(t => t.id === e.target.value);
    setSelectedTimetable(timetable);

    if (timetable) {
      setForm(prev => ({
        ...prev,
        boys_attended: timetable.registeredboys || "",
        girls_attended: timetable.registeredgirls || "",
      }));
      // Learning/specific activities are loaded independently by
      // ActivitySearchCard's own useEffect (watches selectedTimetable).
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {t("lesson_plan.lesson_details")}
      </h2>
      
      {/* Timetable Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {t("lesson_plan.subject")} *
        </label>
        <select
          className="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-3 dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
          onChange={handleTimetableChange}
          value={selectedTimetable?.id || ""}
        >
          <option value="">{t("lesson_plan.select_subject")}</option>
          {timetables.map((timetableItem) => (
            <option key={timetableItem.id} value={timetableItem.id}>
              {timetableItem.subject_name} - {timetableItem.class_level_name}
            </option>
          ))}
        </select>
        
        {/* Selected Subject Info */}
        {currentSubjectInfo && (
          <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">{t("lesson_plan.subject")}:</span>
                <span className="font-semibold ml-2">{currentSubjectInfo.subject}</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">{t("my_subjects.class")}:</span>
                <span className="font-semibold ml-2">{currentSubjectInfo.class}</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">{t("my_subjects.periods_per_week")}:</span>
                <span className="font-semibold ml-2">{currentSubjectInfo.periods}</span>
              </div>
            </div>

            {/* Registered Pupils - editable so mid-term intake/transfers can be reflected */}
            <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-800">
              {!editingRegistered ? (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">
                    {t("my_subjects.total_students")}:{" "}
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {currentSubjectInfo.totalStudents}
                    </span>{" "}
                    <span className="text-gray-500 dark:text-gray-400">
                      ({t("timetable.registered_boys")}: {currentSubjectInfo.registeredBoys}, {t("timetable.registered_girls")}: {currentSubjectInfo.registeredGirls})
                    </span>
                  </span>
                  <button
                    type="button"
                    onClick={startEditRegistered}
                    className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 p-1"
                    title={t("common.edit")}
                  >
                    <Pencil size={16} />
                  </button>
                </div>
              ) : (
                <div className="flex flex-wrap items-end gap-3 text-sm">
                  <div>
                    <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                      {t("timetable.registered_boys")}
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={regBoys}
                      onChange={(e) => setRegBoys(e.target.value)}
                      className="w-24 border border-gray-300 dark:border-gray-600 rounded-lg p-1.5 dark:bg-gray-700 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                      {t("timetable.registered_girls")}
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={regGirls}
                      onChange={(e) => setRegGirls(e.target.value)}
                      className="w-24 border border-gray-300 dark:border-gray-600 rounded-lg p-1.5 dark:bg-gray-700 dark:text-white"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={saveRegistered}
                    disabled={savingRegistered}
                    className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300 p-1.5 disabled:opacity-50"
                    title={t("common.save")}
                  >
                    <Check size={18} />
                  </button>
                  <button
                    type="button"
                    onClick={cancelEditRegistered}
                    disabled={savingRegistered}
                    className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 p-1.5 disabled:opacity-50"
                    title={t("common.cancel")}
                  >
                    <X size={18} />
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SubjectSelectionCard;