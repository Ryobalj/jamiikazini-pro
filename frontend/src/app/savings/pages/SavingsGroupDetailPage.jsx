// src/app/savings/pages/SavingsGroupDetailPage.jsx
//
// Ukurasa wa kikundi kimoja cha VICOBA/SACCOS: salio la mfuko wa pamoja,
// mchango, ombi la kutoa fedha, na kura ya wanachama kwa maombi ya PENDING.

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Wallet, Copy, Loader2, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";
import { useAppContext } from "@/context/AppContext";

const REQUEST_STATUS_STYLES = {
  PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  EXECUTED: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  REJECTED: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  APPROVED: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
};

export default function SavingsGroupDetailPage() {
  const { t } = useTranslation("savings");
  const navigate = useNavigate();
  const { id } = useParams();
  const { formatCurrency } = useCurrency();
  const { user } = useAppContext();

  const [group, setGroup] = useState(null);
  const [contributions, setContributions] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);

  const [contributeAmount, setContributeAmount] = useState("");
  const [contributing, setContributing] = useState(false);

  const [withdrawAmount, setWithdrawAmount] = useState("");
  const [withdrawPurpose, setWithdrawPurpose] = useState("");
  const [requesting, setRequesting] = useState(false);

  const [votingId, setVotingId] = useState(null);

  const fetchAll = () => {
    setLoading(true);
    Promise.all([
      api.get(`/savings/groups/${id}/`).catch(() => null),
      api.get(`/savings/groups/${id}/contributions/`).catch(() => ({ data: [] })),
      api.get(`/savings/groups/${id}/withdrawal-requests/`).catch(() => ({ data: [] })),
    ])
      .then(([groupRes, contribRes, requestsRes]) => {
        setGroup(groupRes?.data || null);
        setContributions(Array.isArray(contribRes.data) ? contribRes.data : []);
        setRequests(Array.isArray(requestsRes.data) ? requestsRes.data : []);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const copyInviteCode = () => {
    if (!group?.invite_code) return;
    navigator.clipboard.writeText(group.invite_code);
    toast.success(t("code_copied", "Msimbo umenakiliwa."));
  };

  const handleContribute = async (e) => {
    e.preventDefault();
    if (!contributeAmount || Number(contributeAmount) <= 0) {
      toast.error(t("amount_required", "Weka kiasi sahihi."));
      return;
    }
    setContributing(true);
    try {
      await api.post(`/savings/groups/${id}/contribute/`, { amount: contributeAmount });
      toast.success(t("contribution_success", "Mchango wako umepokelewa."));
      setContributeAmount("");
      fetchAll();
    } catch (error) {
      const detail = error.response?.data?.detail || error.response?.data?.amount;
      toast.error(typeof detail === "string" ? detail : (Array.isArray(detail) ? detail[0] : t("action_failed", "Imeshindwa. Jaribu tena.")));
    } finally {
      setContributing(false);
    }
  };

  const handleRequestWithdrawal = async (e) => {
    e.preventDefault();
    if (!withdrawAmount || Number(withdrawAmount) <= 0) {
      toast.error(t("amount_required", "Weka kiasi sahihi."));
      return;
    }
    setRequesting(true);
    try {
      await api.post(`/savings/groups/${id}/request-withdrawal/`, {
        amount: withdrawAmount, purpose: withdrawPurpose,
      });
      toast.success(t("withdrawal_requested", "Ombi lako limetumwa kwa kura ya wanachama."));
      setWithdrawAmount(""); setWithdrawPurpose("");
      fetchAll();
    } catch (error) {
      const detail = error.response?.data?.detail || error.response?.data?.amount;
      toast.error(typeof detail === "string" ? detail : (Array.isArray(detail) ? detail[0] : t("action_failed", "Imeshindwa. Jaribu tena.")));
    } finally {
      setRequesting(false);
    }
  };

  const castVote = async (requestId, decision) => {
    setVotingId(requestId);
    try {
      await api.post(`/savings/groups/${id}/vote-withdrawal/`, { request_id: requestId, decision });
      toast.success(decision === "APPROVE" ? t("vote_approved", "Umeidhinisha ombi hili.") : t("vote_rejected", "Umekataa ombi hili."));
      fetchAll();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("action_failed", "Imeshindwa. Jaribu tena."));
    } finally {
      setVotingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
      </div>
    );
  }

  if (!group) {
    return (
      <div className="max-w-2xl mx-auto p-4 sm:p-6 text-center py-16">
        <p className="text-sm text-gray-500 dark:text-gray-400">{t("group_not_found", "Kikundi hakipatikani.")}</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-4 sm:p-6 space-y-5">
      <button
        onClick={() => navigate("/savings")}
        className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
      >
        <ArrowLeft className="w-4 h-4" /> {t("back", "Rudi")}
      </button>

      <Card>
        <CardContent className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">{group.name}</h1>
            <span className="text-xs text-gray-500 dark:text-gray-400">{t(`role_${group.my_role?.toLowerCase()}`, group.my_role)}</span>
          </div>
          <div className="flex items-center gap-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            <Wallet className="w-5 h-5" /> {formatCurrency(group.balance)}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {group.member_count} {t("members_suffix", "wanachama")} · {t("threshold_suffix", "asilimia {{pct}}% ya kura zinahitajika kutoa fedha", { pct: group.approval_threshold_percent })}
          </p>
          <button onClick={copyInviteCode} className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400">
            <Copy className="w-3 h-3" /> {t("invite_code_label", "Msimbo wa Mwaliko")}: <span className="font-mono font-semibold tracking-widest">{group.invite_code}</span>
          </button>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white">{t("contribute_heading", "Changia Mfuko")}</h2>
          <form onSubmit={handleContribute} className="flex gap-2">
            <input
              type="number" min="0.01" step="0.01" value={contributeAmount} onChange={(e) => setContributeAmount(e.target.value)}
              placeholder={t("amount", "Kiasi")}
              className="flex-1 p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
            />
            <Button type="submit" size="sm" disabled={contributing}>
              {contributing ? <Loader2 className="w-4 h-4 animate-spin" /> : t("contribute_submit", "Changia")}
            </Button>
          </form>

          {contributions.length > 0 && (
            <div className="pt-2 space-y-1.5 max-h-48 overflow-y-auto">
              {contributions.map((c) => (
                <div key={c.id} className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-300 border-b border-gray-100 dark:border-gray-800 pb-1">
                  <span>{c.member_name}</span>
                  <span className="font-medium">{formatCurrency(c.amount)}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white">{t("request_withdrawal_heading", "Omba Kutoa Fedha")}</h2>
          <form onSubmit={handleRequestWithdrawal} className="space-y-2">
            <input
              type="number" min="0.01" step="0.01" value={withdrawAmount} onChange={(e) => setWithdrawAmount(e.target.value)}
              placeholder={t("amount", "Kiasi")}
              className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
            />
            <input
              type="text" value={withdrawPurpose} onChange={(e) => setWithdrawPurpose(e.target.value)}
              placeholder={t("purpose_placeholder", "Kwa nini unahitaji fedha hizi?")}
              className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
            />
            <Button type="submit" size="sm" disabled={requesting} className="w-full">
              {requesting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {t("request_submit", "Tuma Ombi kwa Kura")}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t("withdrawal_requests_heading", "Maombi ya Kutoa Fedha")}</h2>
        {requests.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-6">{t("no_requests", "Hakuna maombi bado.")}</p>
        ) : (
          requests.map((r) => {
            const myVote = r.approvals?.find((a) => a.user === user?.id || a.member === user?.id);
            return (
              <Card key={r.id}>
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-gray-900 dark:text-white">{formatCurrency(r.amount)}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${REQUEST_STATUS_STYLES[r.status]}`}>
                      {t(`request_status_${r.status?.toLowerCase()}`, r.status)}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{r.requested_by_name} {r.purpose ? `· ${r.purpose}` : ""}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {t("votes_progress", "Kura {{approve}}/{{required}} zinazohitajika", { approve: r.approve_count, required: r.required_approval_count })}
                    {r.reject_count > 0 ? ` · ${t("reject_count", "{{count}} wamekataa", { count: r.reject_count })}` : ""}
                  </p>

                  {r.status === "PENDING" && (
                    <div className="flex gap-2 pt-1">
                      <Button
                        size="sm" disabled={votingId === r.id || myVote?.decision === "APPROVE"}
                        onClick={() => castVote(r.id, "APPROVE")}
                      >
                        {votingId === r.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4 mr-1" />}
                        {myVote?.decision === "APPROVE" ? t("already_approved", "Umeidhinisha") : t("approve", "Idhinisha")}
                      </Button>
                      <Button
                        size="sm" variant="secondary" disabled={votingId === r.id || myVote?.decision === "REJECT"}
                        onClick={() => castVote(r.id, "REJECT")}
                      >
                        {votingId === r.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <X className="w-4 h-4 mr-1" />}
                        {myVote?.decision === "REJECT" ? t("already_rejected", "Umekataa") : t("reject", "Kataa")}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}
