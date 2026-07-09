// src/app/syllabus/components/SchemeTable.jsx
import React, { useState } from "react";
import { ChevronDown, ChevronUp, Copy } from "lucide-react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

export default function SchemeTable({ schemeData }) {
  const { t } = useTranslation("syllabus");
  const [expandedRows, setExpandedRows] = useState({});
  const [showAll, setShowAll] = useState(false);

  const totalItems = schemeData.schedule_items?.length || 0;
  const displayItems = showAll ? schemeData.schedule_items : schemeData.schedule_items?.slice(0, 10);

  const toggleRow = (index) => {
    setExpandedRows(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(t("common.copied"), { position: "bottom-right" });
    } catch {
      toast.error(t("common.copy_failed"), { position: "bottom-right" });
    }
  };

  // Function to get header key from display name
  const getHeaderKey = (header) => {
    const mapping = {
      "Uwezo Mkuu": "main_competence",
      "Uwezo Maalum": "specific_competence", 
      "Shughuli za Kufundisha": "learning_activity",
      "Shughuli za Mwanafunzi": "student_activity",
      "Mwezi": "month",
      "Nambari ya Wiki": "week_number",
      "Vipindi": "periods",
      "Mbinu": "methodology",
      "Vyanzo": "references",
      "Vifaa vya Kufundishia": "teaching_aids",
      "Vigezo vya Tathmini": "assessment_criteria",
      "Maelezo/Maoni": "remarks"
    };
    return mapping[header] || header.toLowerCase();
  };

  if (!displayItems || displayItems.length === 0) {
    return (
      <div className="p-12 text-center">
        <p className="text-gray-600 dark:text-gray-400">
          {t("scheme.no_data")}
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-900">
          <tr>
            {schemeData.headers?.map((header, index) => (
              <th
                key={index}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap"
              >
                {header}
              </th>
            ))}
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
              {t("common.actions")}
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          {displayItems.map((row, idx) => {
            const isBreak = row.student_activity?.includes("LIKIZO") || row.student_activity?.includes("MITIHANI");
            
            return (
              <React.Fragment key={idx}>
                <tr className={`hover:bg-gray-50 dark:hover:bg-gray-700/50 ${
                  isBreak ? 'bg-yellow-50 dark:bg-yellow-900/10' : ''
                }`}>
                  {schemeData.headers?.map((header, hIdx) => {
                    const key = getHeaderKey(header);
                    const value = row[key] || '';
                    
                    return (
                      <td
                        key={hIdx}
                        className="px-4 py-3 text-sm text-gray-900 dark:text-gray-300 whitespace-normal max-w-xs"
                      >
                        <div className="truncate max-w-[200px]" title={String(value)}>
                          {String(value)}
                        </div>
                      </td>
                    );
                  })}
                  <td className="px-4 py-3 text-sm">
                    <div className="flex gap-2">
                      <button
                        onClick={() => toggleRow(idx)}
                        className="text-blue-600 dark:text-blue-400 hover:text-blue-800"
                        title={expandedRows[idx] ? t("common.collapse") : t("common.expand")}
                      >
                        {expandedRows[idx] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>
                      <button
                        onClick={() => copyToClipboard(JSON.stringify(row, null, 2))}
                        className="text-gray-600 dark:text-gray-400 hover:text-gray-800"
                        title={t("common.copy")}
                      >
                        <Copy size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
                
                {/* Expanded Row */}
                {expandedRows[idx] && (
                  <tr className="bg-gray-50 dark:bg-gray-900/30">
                    <td colSpan={schemeData.headers?.length + 1} className="px-4 py-3">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <h4 className="font-medium mb-2 text-gray-900 dark:text-white">{t("common.full_details")}</h4>
                          <pre className="text-xs bg-gray-100 dark:bg-gray-800 p-3 rounded-lg overflow-x-auto text-gray-800 dark:text-gray-300">
                            {JSON.stringify(row, null, 2)}
                          </pre>
                        </div>
                        <div>
                          <h4 className="font-medium mb-2 text-gray-900 dark:text-white">{t("common.details")}</h4>
                          <ul className="space-y-2 text-sm">
                            {row.main_competence && (
                              <li>
                                <span className="font-medium">{t("scheme.headers.main_competence")}:</span> {row.main_competence}
                              </li>
                            )}
                            {row.specific_competence && (
                              <li>
                                <span className="font-medium">{t("scheme.headers.specific_competence")}:</span> {row.specific_competence}
                              </li>
                            )}
                            {row.learning_activity && (
                              <li>
                                <span className="font-medium">{t("scheme.headers.learning_activity")}:</span> {row.learning_activity}
                              </li>
                            )}
                            {row.periods > 0 && (
                              <li>
                                <span className="font-medium">{t("scheme.headers.periods")}:</span> {row.periods}
                              </li>
                            )}
                            {row.remarks && (
                              <li>
                                <span className="font-medium">{t("scheme.headers.remarks")}:</span> {row.remarks}
                              </li>
                            )}
                          </ul>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>
      
      {/* Show More/Less */}
      {totalItems > 10 && (
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 text-center">
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm font-medium"
          >
            {showAll ? t("common.show_less") : `${t("common.show_all")} (${totalItems})`}
          </button>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {showAll ? `${t("common.viewing_all")} ${totalItems}` : `${t("common.viewing")} 10 ${t("common.of")} ${totalItems}`}
          </p>
        </div>
      )}
    </div>
  );
}