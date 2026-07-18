// src/app/construction/pages/AvailableTendersPage.jsx
//
// Mkandarasi anavinjari miradi inayopokea zabuni (OPEN), anatoa zabuni yake,
// kisha akichaguliwa anawasilisha kila hatua (milestone) kwa uthibitisho wa
// picha kabla mteja hajaidhinisha malipo.

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { HardHat, Loader2, PackageCheck } from "lucide-react";
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

export default function AvailableTendersPage() {
  const { t } = useTranslation("construction");
  const { id: businessId } = useParams();
  const { formatCurrency } = useCurrency();

  const [openProjects, setOpenProjects] = useState([]);
  const [myProjects, setMyProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [bidInputs, setBidInputs] = useState({});
  const [actingId, setActingId] = useState(null);

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      api.get("/construction/projects/open/").then((r) => r.data).catch(() => []),
      api.get("/construction/projects/").then((r) => r.data?.results || r.data || []).catch(() => []),
    ]).then(([open, mine]) => {
      setOpenProjects(open);
      setMyProjects(mine.filter((p) => p.status === "AWARDED" || p.status === "COMPLETED"));
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleBid = async (projectId) => {
    const bid = bidInputs[projectId] || {};
    if (!bid.price || !bid.timeline_days) {
      toast.error(t("bid_fields_required", "Weka bei na muda wa siku."));
      return;
    }
    setActingId(projectId);
    try {
      await api.post(`/construction/projects/${projectId}/bids/`, {
        business_id: businessId, price: bid.price, timeline_days: bid.timeline_days, notes: bid.notes || "",
      });
      toast.success(t("bid_submitted", "Zabuni yako imetumwa."));
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("bid_failed", "Imeshindwa kutuma zabuni."));
    } finally {
      setActingId(null);
    }
  };

  const handleSubmitMilestone = async (projectId, milestoneId) => {
    setActingId(milestoneId);
    try {
      await api.post(`/construction/projects/${projectId}/submit-milestone/`, { milestone_id: milestoneId });
      toast.success(t("milestone_submitted", "Hatua imewasilishwa - inasubiri idhini ya mteja."));
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("action_failed", "Imeshindwa. Jaribu tena."));
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-2">
          <HardHat className="w-5 h-5 text-orange-600" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("open_tenders_heading", "Zabuni Zinazopatikana")}
          </h2>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
          {t("open_tenders_description", "Wateja wanatafuta makandarasi - toa zabuni yako.")}
        </p>

        {loading ? (
          <div className="flex justify-center py-10">
            <Loader2 className="w-6 h-6 animate-spin text-orange-600" />
          </div>
        ) : openProjects.length === 0 ? (
          <div className="text-center py-8 text-gray-400 dark:text-gray-500">
            <PackageCheck className="w-8 h-8 mx-auto mb-2" />
            <p>{t("open_tenders_empty", "Hakuna miradi inayopokea zabuni kwa sasa.")}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {openProjects.map((p) => (
              <Card key={p.id}>
                <CardContent className="p-4 space-y-2">
                  <p className="text-sm text-gray-900 dark:text-white">{p.scope_description}</p>
                  {p.budget_ceiling && (
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t("budget_ceiling_label", "Bajeti ya Juu")}: {formatCurrency(p.budget_ceiling)}
                    </p>
                  )}
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      type="number" min="0" step="0.01"
                      value={bidInputs[p.id]?.price || ""}
                      onChange={(e) => setBidInputs((prev) => ({ ...prev, [p.id]: { ...prev[p.id], price: e.target.value } }))}
                      placeholder={t("your_price", "Bei Yako")}
                      className="w-32 p-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                    />
                    <input
                      type="number" min="1"
                      value={bidInputs[p.id]?.timeline_days || ""}
                      onChange={(e) => setBidInputs((prev) => ({ ...prev, [p.id]: { ...prev[p.id], timeline_days: e.target.value } }))}
                      placeholder={t("timeline_days_placeholder", "Siku")}
                      className="w-24 p-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                    />
                    <Button size="sm" disabled={actingId === p.id} onClick={() => handleBid(p.id)}>
                      {actingId === p.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("submit_bid", "Tuma Zabuni")}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
          {t("my_awarded_heading", "Miradi Niliyopewa")}
        </h2>
        {myProjects.length === 0 ? (
          <p className="text-sm text-gray-400">{t("no_awarded", "Hujapewa mradi wowote bado.")}</p>
        ) : (
          <div className="space-y-3">
            {myProjects.map((p) => (
              <Card key={p.id}>
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-900 dark:text-white line-clamp-2">{p.scope_description}</p>
                    <span className={`shrink-0 px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_STYLES[p.status]}`}>
                      {t(`status_${p.status?.toLowerCase()}`, p.status)}
                    </span>
                  </div>
                  {(p.milestones || []).map((m) => (
                    <div key={m.id} className="flex items-center justify-between border border-gray-200 dark:border-gray-700 rounded-lg p-2 text-sm">
                      <div>
                        <p className="text-gray-900 dark:text-white">{m.name}</p>
                        <p className="text-gray-500 dark:text-gray-400">{formatCurrency(m.amount)}</p>
                      </div>
                      {m.status === "PENDING" ? (
                        <Button size="sm" disabled={actingId === m.id} onClick={() => handleSubmitMilestone(p.id, m.id)}>
                          {actingId === m.id ? <Loader2 className="w-4 h-4 animate-spin" /> : t("submit_milestone", "Wasilisha Kazi")}
                        </Button>
                      ) : (
                        <span className="text-xs text-gray-400">{t(`milestone_status_${m.status?.toLowerCase()}`, m.status)}</span>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
