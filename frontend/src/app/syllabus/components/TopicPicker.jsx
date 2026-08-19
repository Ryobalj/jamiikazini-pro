// src/app/syllabus/components/TopicPicker.jsx

import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";

/**
 * Grouped (by main competence -> specific competence) checklist of
 * LearningActivity topics, used to scope one section's question pool.
 * `topics` is the full flat list for the subject (fetched once and
 * shared across every section's picker); `selectedIds`/`onChange` are
 * this one section's own selection.
 */
export default function TopicPicker({ topics, loading, selectedIds, onChange }) {
  const { t } = useTranslation("syllabus");

  const groups = useMemo(() => {
    const list = [];
    const byKey = new Map();
    topics.forEach((topic) => {
      const key = `${topic.main_competence_name}|||${topic.specific_competence_name}`;
      let group = byKey.get(key);
      if (!group) {
        group = { mainCompetence: topic.main_competence_name, specificCompetence: topic.specific_competence_name, items: [] };
        byKey.set(key, group);
        list.push(group);
      }
      group.items.push(topic);
    });
    return list;
  }, [topics]);

  const toggleTopic = (id) => {
    onChange(selectedIds.includes(id) ? selectedIds.filter((t) => t !== id) : [...selectedIds, id]);
  };

  const toggleGroup = (items, allSelected) => {
    const ids = items.map((i) => i.id);
    onChange(allSelected ? selectedIds.filter((id) => !ids.includes(id)) : Array.from(new Set([...selectedIds, ...ids])));
  };

  if (loading) {
    return <div className="text-sm text-gray-500">{t("common.loading")}...</div>;
  }
  if (groups.length === 0) {
    return <p className="text-sm text-gray-500">{t("quiz.no_topics")}</p>;
  }

  return (
    <div>
      <div className="max-h-56 overflow-y-auto space-y-3 pr-1">
        {groups.map((group, gi) => {
          const groupIds = group.items.map((i) => i.id);
          const allSelected = groupIds.every((id) => selectedIds.includes(id));
          return (
            <div key={gi}>
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-semibold text-gray-600 dark:text-gray-300">
                  {group.mainCompetence} — {group.specificCompetence}
                </p>
                <button
                  type="button"
                  onClick={() => toggleGroup(group.items, allSelected)}
                  className="text-xs text-blue-600 hover:underline shrink-0 ml-2"
                >
                  {allSelected ? t("quiz.clear_group") : t("quiz.select_group")}
                </button>
              </div>
              <div className="space-y-1">
                {group.items.map((topic) => (
                  <label key={topic.id} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(topic.id)}
                      onChange={() => toggleTopic(topic.id)}
                      className="mt-0.5"
                    />
                    <span>{topic.name}</span>
                  </label>
                ))}
              </div>
            </div>
          );
        })}
      </div>
      {selectedIds.length > 0 && (
        <button type="button" onClick={() => onChange([])} className="mt-2 text-xs text-red-600 hover:underline">
          {t("quiz.clear_all_topics")}
        </button>
      )}
    </div>
  );
}
