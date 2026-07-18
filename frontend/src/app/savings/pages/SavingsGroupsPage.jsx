// src/app/savings/pages/SavingsGroupsPage.jsx
//
// VICOBA/SACCOS - orodha ya vikundi vya mtumiaji, fomu ya kuanzisha kikundi
// kipya, na fomu ya kujiunga kwa msimbo wa mwaliko. Jamiikazini si taasisi ya
// fedha yenye leseni - ujumbe huu unaonekana wazi hapa.

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Users, Plus, LogIn, Loader2, ShieldAlert, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";
import api from "@/lib/axios";
import { useCurrency } from "@/context/CurrencyContext";

export default function SavingsGroupsPage() {
  const { t } = useTranslation("savings");
  const navigate = useNavigate();
  const { formatCurrency } = useCurrency();

  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);

  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [threshold, setThreshold] = useState("51");
  const [creating, setCreating] = useState(false);

  const [showJoin, setShowJoin] = useState(false);
  const [inviteCode, setInviteCode] = useState("");
  const [contributionAmount, setContributionAmount] = useState("");
  const [joining, setJoining] = useState(false);

  const fetchGroups = () => {
    setLoading(true);
    api
      .get("/savings/groups/")
      .then((res) => setGroups(Array.isArray(res.data) ? res.data : res.data?.results || []))
      .catch(() => setGroups([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchGroups();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error(t("name_required", "Weka jina la kikundi."));
      return;
    }
    setCreating(true);
    try {
      await api.post("/savings/groups/", {
        name: name.trim(),
        approval_threshold_percent: threshold || "51",
      });
      toast.success(t("group_created", "Kikundi kimeanzishwa."));
      setName(""); setThreshold("51"); setShowCreate(false);
      fetchGroups();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("action_failed", "Imeshindwa. Jaribu tena."));
    } finally {
      setCreating(false);
    }
  };

  const handleJoin = async (e) => {
    e.preventDefault();
    if (!inviteCode.trim()) {
      toast.error(t("invite_code_required", "Weka msimbo wa mwaliko."));
      return;
    }
    setJoining(true);
    try {
      await api.post("/savings/groups/join/", {
        invite_code: inviteCode.trim(),
        contribution_amount: contributionAmount || "0",
      });
      toast.success(t("joined_success", "Umejiunga na kikundi."));
      setInviteCode(""); setContributionAmount(""); setShowJoin(false);
      fetchGroups();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("join_failed", "Msimbo huu wa mwaliko haupatikani."));
    } finally {
      setJoining(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-4 sm:p-6 space-y-5">
      <div className="flex items-center gap-2">
        <Users className="w-6 h-6 text-emerald-600" />
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t("title", "VICOBA/SACCOS - Vikundi vya Akiba")}
        </h1>
      </div>

      <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
        <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <p className="text-xs text-amber-800 dark:text-amber-300">
          {t("disclaimer", "Jamiikazini si taasisi ya fedha yenye leseni. Vikundi hivi ni zana ya kuwezesha makubaliano ya wanachama wenyewe - fedha za mfuko wa pamoja hutolewa tu baada ya kura ya kutosha ya wanachama.")}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Button size="sm" className="w-full bg-emerald-600 hover:bg-emerald-700" onClick={() => { setShowCreate((v) => !v); setShowJoin(false); }}>
          <Plus className="w-4 h-4 mr-1" /> {t("create_group", "Anzisha Kikundi")}
        </Button>
        <Button size="sm" variant="outline" className="w-full" onClick={() => { setShowJoin((v) => !v); setShowCreate(false); }}>
          <LogIn className="w-4 h-4 mr-1" /> {t("join_group", "Jiunge na Kikundi")}
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardContent className="p-4">
            <form onSubmit={handleCreate} className="space-y-3">
              <input
                type="text" value={name} onChange={(e) => setName(e.target.value)}
                placeholder={t("name_placeholder", "Jina la kikundi, mfano: VICOBA Wanawake")}
                className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
              />
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400">
                  {t("threshold_label", "Asilimia ya kura zinazohitajika kutoa fedha")}
                </label>
                <input
                  type="number" min="1" max="100" step="1" value={threshold} onChange={(e) => setThreshold(e.target.value)}
                  className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                />
              </div>
              <Button type="submit" disabled={creating} className="w-full">
                {creating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                {t("create_submit", "Anzisha")}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {showJoin && (
        <Card>
          <CardContent className="p-4">
            <form onSubmit={handleJoin} className="space-y-3">
              <input
                type="text" value={inviteCode} onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
                placeholder={t("invite_code_placeholder", "Msimbo wa Mwaliko")}
                className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg tracking-widest uppercase"
              />
              <input
                type="number" min="0" step="0.01" value={contributionAmount} onChange={(e) => setContributionAmount(e.target.value)}
                placeholder={t("contribution_amount_placeholder", "Mchango wa Kawaida (hiari)")}
                className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
              />
              <Button type="submit" disabled={joining} className="w-full">
                {joining ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                {t("join_submit", "Jiunge")}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t("my_groups", "Vikundi Vyangu")}
        </h2>
        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
          </div>
        ) : groups.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
            {t("no_groups", "Hujajiunga na kikundi chochote bado.")}
          </p>
        ) : (
          groups.map((g) => (
            <Card key={g.id} className="cursor-pointer hover:border-emerald-400 transition-colors" onClick={() => navigate(`/savings/${g.id}`)}>
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">{g.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {g.member_count} {t("members_suffix", "wanachama")} · {t(`role_${g.my_role?.toLowerCase()}`, g.my_role)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">{formatCurrency(g.balance)}</span>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
