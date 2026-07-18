// src/app/construction/pages/RequestProjectPage.jsx
//
// Mteja anachapisha mradi wa ujenzi, analinganisha zabuni kadhaa kutoka kwa
// makandarasi, kisha anachagua moja - bei yote ya zabuni inashikiliwa (HOLD)
// mara moja, na kila hatua (milestone) inayokamilika inatoa sehemu yake.

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { HardHat, Plus, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";

const STATUS_STYLES = {
  OPEN: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  AWARDED: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  COMPLETED: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  CANCELLED: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
};

export default function RequestProjectPage() {
  const { t } = useTranslation("construction");
  const { formatCurrency } = useCurrency();

  const [scopeDescription, setScopeDescription] = useState("");
  const [budgetCeiling, setBudgetCeiling] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [location, setLocation] = useState(null);

  const [projects, setProjects] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [actingId, setActingId] = useState(null);
  const [selectingBidId, setSelectingBidId] = useState({});
  const [milestoneDrafts, setMilestoneDrafts] = useState({});

  const fetchProjects = () => {
    setLoadingProjects(true);
    api
      .get("/construction/projects/")
      .then((res) => setProjects(Array.isArray(res.data) ? res.data : res.data?.results || []))
      .catch(() => setProjects([]))
      .finally(() => setLoadingProjects(false));
  };

  useEffect(() => {
    fetchProjects();
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => setLocation(null)
      );
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!scopeDescription.trim()) {
      toast.error(t("scope_required", "Elezea kazi unayohitaji."));
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/construction/projects/", {
        scope_description: scopeDescription.trim(),
        budget_ceiling: budgetCeiling || undefined,
        lat: location?.lat, lng: location?.lng,
      });
      toast.success(t("project_posted", "Mradi wako umechapishwa - makandarasi wanaweza kutoa zabuni."));
      setScopeDescription(""); setBudgetCeiling("");
      fetchProjects();
    } catch (error) {
      toast.error(t("project_failed", "Imeshindwa kuchapisha mradi."));
    } finally {
      setSubmitting(false);
    }
  };

  const startSelectingBid = (projectId, bidId, price) => {
    setSelectingBidId((prev) => ({ ...prev, [projectId]: bidId }));
    setMilestoneDrafts((prev) => ({
      ...prev,
      [projectId]: [{ name: t("default_milestone_name", "Kazi Kamili"), amount: price }],
    }));
  };

  const updateMilestoneDraft = (projectId, index, field, value) => {
    setMilestoneDrafts((prev) => {
      const rows = [...(prev[projectId] || [])];
      rows[index] = { ...rows[index], [field]: value };
      return { ...prev, [projectId]: rows };
    });
  };

  const addMilestoneRow = (projectId) => {
    setMilestoneDrafts((prev) => ({
      ...prev,
      [projectId]: [...(prev[projectId] || []), { name: "", amount: "" }],
    }));
  };

  const removeMilestoneRow = (projectId, index) => {
    setMilestoneDrafts((prev) => ({
      ...prev,
      [projectId]: (prev[projectId] || []).filter((_, i) => i !== index),
    }));
  };

  const confirmSelectBid = async (projectId) => {
    const bidId = selectingBidId[projectId];
    const milestones = milestoneDrafts[projectId] || [];
    if (!milestones.length || milestones.some((m) => !m.name || !m.amount)) {
      toast.error(t("milestones_incomplete", "Jaza jina na kiasi cha kila hatua."));
      return;
    }
    setActingId(projectId);
    try {
      await api.post(`/construction/projects/${projectId}/select-bid/`, { bid_id: bidId, milestones });
      toast.success(t("bid_selected", "Umechagua zabuni - bei nzima imeshikiliwa."));
      setSelectingBidId((prev) => ({ ...prev, [projectId]: null }));
      fetchProjects();
    } catch (error) {
      const detail = error.response?.data?.detail || error.response?.data?.milestones;
      toast.error(typeof detail === "string" ? detail : (Array.isArray(detail) ? detail[0] : t("action_failed", "Imeshindwa. Jaribu tena.")));
    } finally {
      setActingId(null);
    }
  };

  const approveMilestone = async (projectId, milestoneId) => {
    setActingId(milestoneId);
    try {
      await api.post(`/construction/projects/${projectId}/approve-milestone/`, { milestone_id: milestoneId });
      toast.success(t("milestone_approved", "Hatua imeidhinishwa - malipo yametolewa."));
      fetchProjects();
    } catch (error) {
      toast.error(error.response?.data?.detail || t("action_failed", "Imeshindwa. Jaribu tena."));
    } finally {
      setActingId(null);
    }
  };

  const cancelProject = async (projectId) => {
    setActingId(projectId);
    try {
      await api.post(`/construction/projects/${projectId}/cancel/`);
      toast.success(t("cancelled_success", "Mradi umeghairiwa."));
      fetchProjects();
    } catch (error) {
      toast.error(error.response?.data?.detail || t("action_failed", "Imeshindwa. Jaribu tena."));
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-4 sm:p-6 space-y-5">
      <div className="flex items-center gap-2">
        <HardHat className="w-6 h-6 text-orange-600" />
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t("title", "Mradi wa Ujenzi/Kandarasi")}
        </h1>
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        {t("subtitle", "Chapisha maelezo ya kazi, linganisha zabuni kutoka kwa makandarasi kadhaa, kisha lipa kwa awamu kadri kazi inavyoendelea.")}
      </p>

      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSubmit} className="space-y-3">
            <textarea
              value={scopeDescription} onChange={(e) => setScopeDescription(e.target.value)}
              rows={3}
              placeholder={t("scope_placeholder", "Mfano: Kujenga uzio wa mita 50 pande za nyumba...")}
              className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
            />
            <input
              type="number" min="0" step="0.01" value={budgetCeiling} onChange={(e) => setBudgetCeiling(e.target.value)}
              placeholder={t("budget_ceiling_placeholder", "Bajeti ya Juu (hiari)")}
              className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
            />
            <Button type="submit" disabled={submitting} className="w-full">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {t("submit", "Chapisha Mradi")}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t("my_projects", "Miradi Yangu")}
        </h2>
        {loadingProjects ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-orange-600" />
          </div>
        ) : projects.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
            {t("no_projects", "Hujawahi kuchapisha mradi bado.")}
          </p>
        ) : (
          projects.map((p) => (
            <Card key={p.id}>
              <CardContent className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-gray-900 dark:text-white line-clamp-2">{p.scope_description}</p>
                  <span className={`shrink-0 px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_STYLES[p.status]}`}>
                    {t(`status_${p.status?.toLowerCase()}`, p.status)}
                  </span>
                </div>

                {p.status === "OPEN" && (
                  <div className="space-y-2">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t("bids_heading", "Zabuni")} ({p.bids?.length || 0})
                    </p>
                    {(p.bids || []).map((bid) => (
                      <div key={bid.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-2 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-900 dark:text-white">{bid.contractor_name}</span>
                          <span className="text-gray-600 dark:text-gray-300">{formatCurrency(bid.price)} - {bid.timeline_days} {t("days", "siku")}</span>
                        </div>
                        {selectingBidId[p.id] === bid.id ? (
                          <div className="mt-2 space-y-1.5">
                            {(milestoneDrafts[p.id] || []).map((m, idx) => (
                              <div key={idx} className="flex gap-1.5">
                                <input
                                  type="text" value={m.name}
                                  onChange={(e) => updateMilestoneDraft(p.id, idx, "name", e.target.value)}
                                  placeholder={t("milestone_name_placeholder", "Jina la hatua")}
                                  className="flex-1 p-1 text-xs border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-800"
                                />
                                <input
                                  type="number" min="0" step="0.01" value={m.amount}
                                  onChange={(e) => updateMilestoneDraft(p.id, idx, "amount", e.target.value)}
                                  placeholder={t("amount", "Kiasi")}
                                  className="w-24 p-1 text-xs border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-800"
                                />
                                <button type="button" onClick={() => removeMilestoneRow(p.id, idx)} className="text-red-500">
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            ))}
                            <button type="button" onClick={() => addMilestoneRow(p.id)} className="flex items-center gap-1 text-xs text-orange-600">
                              <Plus className="w-3 h-3" /> {t("add_milestone", "Ongeza Hatua")}
                            </button>
                            <Button size="sm" disabled={actingId === p.id} onClick={() => confirmSelectBid(p.id)} className="w-full">
                              {actingId === p.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("confirm_select", "Thibitisha na Shikilia Fedha")}
                            </Button>
                          </div>
                        ) : (
                          <Button size="sm" className="mt-1.5" onClick={() => startSelectingBid(p.id, bid.id, bid.price)}>
                            {t("select_bid", "Chagua Zabuni Hii")}
                          </Button>
                        )}
                      </div>
                    ))}
                    <Button size="sm" variant="secondary" disabled={actingId === p.id} onClick={() => cancelProject(p.id)}>
                      {t("cancel", "Ghairi Mradi")}
                    </Button>
                  </div>
                )}

                {(p.status === "AWARDED" || p.status === "COMPLETED") && (
                  <div className="space-y-2">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t("contractor_label", "Mkandarasi")}: {p.contractor_name}
                    </p>
                    {(p.milestones || []).map((m) => (
                      <div key={m.id} className="flex items-center justify-between border border-gray-200 dark:border-gray-700 rounded-lg p-2 text-sm">
                        <div>
                          <p className="text-gray-900 dark:text-white">{m.name}</p>
                          <p className="text-gray-500 dark:text-gray-400">{formatCurrency(m.amount)}</p>
                        </div>
                        {m.status === "SUBMITTED" ? (
                          <Button size="sm" disabled={actingId === m.id} onClick={() => approveMilestone(p.id, m.id)}>
                            {actingId === m.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("approve_milestone", "Idhinisha")}
                          </Button>
                        ) : (
                          <span className="text-xs text-gray-400">{t(`milestone_status_${m.status?.toLowerCase()}`, m.status)}</span>
                        )}
                      </div>
                    ))}
                    {p.status === "AWARDED" && (
                      <Button size="sm" variant="secondary" disabled={actingId === p.id} onClick={() => cancelProject(p.id)}>
                        {t("cancel", "Ghairi Mradi")}
                      </Button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
