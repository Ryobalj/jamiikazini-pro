// src/app/homepage/pages/HomepageManagerPage.jsx

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "@/lib/axios";
import {
  ArrowLeft,
  Loader2,
  Save,
  ExternalLink,
  PlusCircle,
  Trash2,
  Layout,
  Info,
  Sparkles,
  HelpCircle,
  MessageSquareQuote,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";

function useSectionList(basePath) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchItems = useCallback(() => {
    setLoading(true);
    api
      .get(basePath)
      .then((res) => setItems(res.data?.results || res.data || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [basePath]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const remove = async (id) => {
    try {
      await api.delete(`${basePath}${id}/`);
      setItems((prev) => prev.filter((i) => i.id !== id));
    } catch {
      toast.error("Imeshindwa kufuta.");
    }
  };

  return { items, loading, fetchItems, remove };
}

export default function HomepageManagerPage() {
  const { ownerType, ownerId } = useParams();
  const navigate = useNavigate();

  const [homepage, setHomepage] = useState(null);
  const [loadingHomepage, setLoadingHomepage] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(null);

  useEffect(() => {
    api
      .get(`/homepage/mine/${ownerType}/${ownerId}/`)
      .then((res) => {
        setHomepage(res.data);
        setForm(res.data);
      })
      .catch(() => toast.error("Huwezi kusimamia homepage hii."))
      .finally(() => setLoadingHomepage(false));
  }, [ownerType, ownerId]);

  const heroPath = homepage ? `/homepage/homepages/${homepage.id}/hero-sections/` : null;
  const aboutPath = homepage ? `/homepage/homepages/${homepage.id}/about-sections/` : null;
  const whatWeDoPath = homepage ? `/homepage/homepages/${homepage.id}/what-we-do/` : null;
  const faqPath = homepage ? `/homepage/homepages/${homepage.id}/faqs/` : null;
  const testimonialPath = homepage ? `/homepage/homepages/${homepage.id}/testimonials/` : null;

  const hero = useSectionList(heroPath || "");
  const about = useSectionList(aboutPath || "");
  const whatWeDo = useSectionList(whatWeDoPath || "");
  const faq = useSectionList(faqPath || "");
  const testimonial = useSectionList(testimonialPath || "");

  const saveSettings = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await api.patch(`/homepage/mine/${ownerType}/${ownerId}/`, {
        name: form.name,
        tagline: form.tagline,
        contact_email: form.contact_email,
        contact_phone: form.contact_phone,
        contact_address: form.contact_address,
        social_facebook: form.social_facebook,
        social_instagram: form.social_instagram,
        primary_color: form.primary_color,
        is_published: form.is_published,
      });
      setHomepage(res.data);
      toast.success("Mipangilio imehifadhiwa.");
    } catch {
      toast.error("Imeshindwa kuhifadhi.");
    } finally {
      setSaving(false);
    }
  };

  const addHero = async () => {
    if (!heroPath) return;
    try {
      await api.post(heroPath, { title: "Karibu" });
      hero.fetchItems();
    } catch {
      toast.error("Imeshindwa kuongeza.");
    }
  };

  const addAbout = async () => {
    if (!aboutPath) return;
    try {
      await api.post(aboutPath, { description: "Andika kuhusu sisi hapa..." });
      about.fetchItems();
    } catch {
      toast.error("Imeshindwa kuongeza.");
    }
  };

  const addWhatWeDo = async () => {
    if (!whatWeDoPath) return;
    try {
      await api.post(whatWeDoPath, { description: "Andika tunachofanya..." });
      whatWeDo.fetchItems();
    } catch {
      toast.error("Imeshindwa kuongeza.");
    }
  };

  const addFaq = async () => {
    if (!faqPath) return;
    try {
      await api.post(faqPath, { question: "Swali...", answer: "Jibu..." });
      faq.fetchItems();
    } catch {
      toast.error("Imeshindwa kuongeza.");
    }
  };

  const addTestimonial = async () => {
    if (!testimonialPath) return;
    try {
      await api.post(testimonialPath, { client_name: "Jina la mteja", content: "Maoni yao..." });
      testimonial.fetchItems();
    } catch {
      toast.error("Imeshindwa kuongeza.");
    }
  };

  if (loadingHomepage) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!homepage || !form) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-6 text-center text-gray-500 dark:text-gray-400">
        Huwezi kusimamia homepage hii.
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
        >
          <ArrowLeft className="w-4 h-4" />
          Rudi
        </button>
        <Link
          to={`/homepage/${ownerType}/${ownerId}`}
          target="_blank"
          className="flex items-center gap-1 text-sm text-purple-600 dark:text-purple-400 hover:underline"
        >
          <ExternalLink className="w-4 h-4" />
          Ona Homepage
        </Link>
      </div>

      <Card>
        <CardHeader title="Mipangilio ya Homepage" icon={<Layout className="w-5 h-5" />} divider />
        <CardContent>
          <form onSubmit={saveSettings} className="space-y-3">
            <input
              type="text"
              value={form.name || ""}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Jina"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            <input
              type="text"
              value={form.tagline || ""}
              onChange={(e) => setForm({ ...form, tagline: e.target.value })}
              placeholder="Tagline"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            <div className="grid grid-cols-2 gap-3">
              <input
                type="email"
                value={form.contact_email || ""}
                onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
                placeholder="Barua Pepe"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              <input
                type="text"
                value={form.contact_phone || ""}
                onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
                placeholder="Simu"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <input
              type="text"
              value={form.contact_address || ""}
              onChange={(e) => setForm({ ...form, contact_address: e.target.value })}
              placeholder="Anwani"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={form.primary_color || "#6d28d9"}
                onChange={(e) => setForm({ ...form, primary_color: e.target.value })}
                className="w-10 h-10 rounded border border-gray-300 dark:border-gray-600"
              />
              <span className="text-sm text-gray-500 dark:text-gray-400">Rangi kuu</span>
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
              <input
                type="checkbox"
                checked={form.is_published}
                onChange={(e) => setForm({ ...form, is_published: e.target.checked })}
              />
              Homepage ionekane kwa umma
            </label>
            <Button type="submit" disabled={saving} className="bg-purple-600 hover:bg-purple-700">
              {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
              Hifadhi
            </Button>
          </form>
        </CardContent>
      </Card>

      <SectionCard
        title="Hero (Banner Kuu)"
        icon={<Sparkles className="w-5 h-5" />}
        state={hero}
        onAdd={addHero}
        renderItem={(item) => item.title}
      />
      <SectionCard
        title="Kuhusu Sisi"
        icon={<Info className="w-5 h-5" />}
        state={about}
        onAdd={addAbout}
        renderItem={(item) => item.title || item.description?.slice(0, 60)}
      />
      <SectionCard
        title="Tunachofanya"
        icon={<Layout className="w-5 h-5" />}
        state={whatWeDo}
        onAdd={addWhatWeDo}
        renderItem={(item) => item.title}
      />
      <SectionCard
        title="Maswali (FAQ)"
        icon={<HelpCircle className="w-5 h-5" />}
        state={faq}
        onAdd={addFaq}
        renderItem={(item) => item.question}
      />
      <SectionCard
        title="Maoni ya Wateja"
        icon={<MessageSquareQuote className="w-5 h-5" />}
        state={testimonial}
        onAdd={addTestimonial}
        renderItem={(item) => item.client_name}
      />
    </div>
  );
}

function SectionCard({ title, icon, state, onAdd, renderItem }) {
  const { items, loading, remove } = state;
  return (
    <Card>
      <CardHeader
        title={title}
        icon={icon}
        actions={
          <Button size="sm" className="bg-purple-600 hover:bg-purple-700" onClick={onAdd}>
            <PlusCircle className="w-4 h-4 mr-1" />
            Ongeza
          </Button>
        }
        divider
      />
      <CardContent>
        {loading ? (
          <Loader2 className="w-5 h-5 animate-spin mx-auto text-gray-400" />
        ) : items.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Hakuna bado. Bofya "Ongeza".</p>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {items.map((item) => (
              <div key={item.id} className="flex items-center justify-between py-2">
                <span className="text-sm text-gray-800 dark:text-gray-200 truncate pr-2">
                  {renderItem(item) || "(bila jina)"}
                </span>
                <Button size="sm" variant="outline" onClick={() => remove(item.id)}>
                  <Trash2 className="w-4 h-4 text-red-500" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
