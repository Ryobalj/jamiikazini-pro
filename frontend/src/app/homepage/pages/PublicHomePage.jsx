// src/app/homepage/pages/PublicHomePage.jsx

import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import api from "@/lib/axios";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import {
  Loader2,
  Phone,
  Mail,
  MapPin,
  Facebook,
  Instagram,
  Twitter,
  ChevronDown,
  Star,
} from "lucide-react";

export default function PublicHomePage() {
  const { ownerType, ownerId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [openFaq, setOpenFaq] = useState(null);

  useDocumentTitle(data?.name);

  useEffect(() => {
    api
      .get(`/homepage/public/${ownerType}/${ownerId}/`)
      .then((res) => setData(res.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [ownerType, ownerId]);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-center px-4">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-white mb-2">
          Ukurasa haupatikani
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Homepage hii haipo au bado haijachapishwa.
        </p>
      </div>
    );
  }

  const primary = data.primary_color || "#6d28d9";
  const hero = data.hero_sections?.[0];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-2">
          {data.logo && <img src={data.logo} alt={data.name} className="w-8 h-8 rounded" />}
          <span className="font-bold text-lg text-gray-900 dark:text-white">{data.name}</span>
        </div>
        {data.tagline && (
          <span className="hidden sm:block text-sm text-gray-500 dark:text-gray-400">{data.tagline}</span>
        )}
      </header>

      {/* Hero */}
      {hero && (
        <section
          className="relative px-6 py-20 text-center text-white"
          style={{
            backgroundColor: primary,
            backgroundImage: hero.background_image ? `url(${hero.background_image})` : undefined,
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        >
          <div className="absolute inset-0 bg-black/40" />
          <div className="relative max-w-2xl mx-auto">
            <h1 className="text-3xl sm:text-5xl font-bold mb-4">{hero.title}</h1>
            {hero.subtitle && <p className="text-lg opacity-90 mb-6">{hero.subtitle}</p>}
            {hero.cta_text && (
              <a
                href={hero.cta_link || "#contact"}
                className="inline-block px-6 py-3 bg-white text-gray-900 rounded-full font-medium hover:bg-gray-100 transition-colors"
              >
                {hero.cta_text}
              </a>
            )}
          </div>
        </section>
      )}

      {/* About */}
      {data.about_sections?.map((about) => (
        <section key={about.id} className="px-6 py-16 max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{about.title}</h2>
          <p className="text-gray-600 dark:text-gray-300 whitespace-pre-line mb-6">{about.description}</p>
          {(about.mission || about.vision) && (
            <div className="grid sm:grid-cols-2 gap-6 mb-6">
              {about.mission && (
                <div>
                  <h3 className="font-semibold text-purple-600 mb-1">Dhamira Yetu</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{about.mission}</p>
                </div>
              )}
              {about.vision && (
                <div>
                  <h3 className="font-semibold text-purple-600 mb-1">Dira Yetu</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{about.vision}</p>
                </div>
              )}
            </div>
          )}
          {about.stats?.length > 0 && (
            <div className="flex flex-wrap gap-8 mt-6">
              {about.stats.map((s, i) => (
                <div key={i} className="text-center">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{s.number}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{s.label}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      ))}

      {/* What We Do */}
      {data.what_we_do_sections?.map((wwd) => (
        <section key={wwd.id} className="px-6 py-16 bg-gray-50 dark:bg-gray-800/50">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2 text-center">{wwd.title}</h2>
            {wwd.subtitle && (
              <p className="text-center text-gray-500 dark:text-gray-400 mb-8">{wwd.subtitle}</p>
            )}
            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6">
              {wwd.services?.map((s) => (
                <div key={s.id} className="p-5 bg-white dark:bg-gray-900 rounded-2xl shadow-soft">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1">{s.title}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{s.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      ))}

      {/* Testimonials */}
      {data.testimonials?.length > 0 && (
        <section className="px-6 py-16 max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-8 text-center">Wanachosema Wateja</h2>
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6">
            {data.testimonials.map((tst) => (
              <div key={tst.id} className="p-5 border border-gray-100 dark:border-gray-700 rounded-2xl">
                <div className="flex gap-0.5 mb-2">
                  {Array.from({ length: tst.rating }).map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">"{tst.content}"</p>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{tst.client_name}</p>
                {tst.client_role && <p className="text-xs text-gray-400">{tst.client_role}</p>}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* FAQ */}
      {data.faqs?.length > 0 && (
        <section className="px-6 py-16 max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-8 text-center">Maswali Yanayoulizwa Mara kwa Mara</h2>
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {data.faqs.map((faq) => (
              <div key={faq.id} className="py-4">
                <button
                  onClick={() => setOpenFaq(openFaq === faq.id ? null : faq.id)}
                  className="w-full flex items-center justify-between text-left"
                >
                  <span className="font-medium text-gray-900 dark:text-white">{faq.question}</span>
                  <ChevronDown
                    className={`w-4 h-4 text-gray-400 transition-transform ${openFaq === faq.id ? "rotate-180" : ""}`}
                  />
                </button>
                {openFaq === faq.id && (
                  <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">{faq.answer}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Footer / Contact */}
      <footer id="contact" className="px-6 py-10 bg-gray-900 text-gray-300">
        <div className="max-w-4xl mx-auto flex flex-wrap gap-6 justify-between items-center">
          <div className="space-y-1 text-sm">
            {data.contact_email && (
              <p className="flex items-center gap-2"><Mail className="w-4 h-4" /> {data.contact_email}</p>
            )}
            {data.contact_phone && (
              <p className="flex items-center gap-2"><Phone className="w-4 h-4" /> {data.contact_phone}</p>
            )}
            {data.contact_address && (
              <p className="flex items-center gap-2"><MapPin className="w-4 h-4" /> {data.contact_address}</p>
            )}
          </div>
          <div className="flex gap-3">
            {data.social_facebook && (
              <a href={data.social_facebook} target="_blank" rel="noreferrer"><Facebook className="w-5 h-5" /></a>
            )}
            {data.social_instagram && (
              <a href={data.social_instagram} target="_blank" rel="noreferrer"><Instagram className="w-5 h-5" /></a>
            )}
            {data.social_twitter && (
              <a href={data.social_twitter} target="_blank" rel="noreferrer"><Twitter className="w-5 h-5" /></a>
            )}
          </div>
        </div>
      </footer>
    </div>
  );
}
