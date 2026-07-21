// src/pages/HelpPage.jsx

import React from "react";
import { useTranslation } from "react-i18next";
import * as Icons from "lucide-react";

const TOC = [
  { id: "intro", icon: "Info", key: "intro" },
  { id: "getting-started", icon: "Rocket", key: "getting_started" },
  { id: "wallet", icon: "Wallet", key: "wallet" },
  { id: "marketplace", icon: "ShoppingBag", key: "marketplace" },
  { id: "businesses", icon: "Store", key: "businesses" },
  { id: "multidomain", icon: "Globe", key: "multidomain" },
  { id: "institutions", icon: "Building2", key: "institutions" },
  { id: "logistics", icon: "Truck", key: "logistics" },
  { id: "realestate", icon: "Home", key: "realestate" },
  { id: "agriculture", icon: "Wheat", key: "agriculture" },
  { id: "construction", icon: "HardHat", key: "construction" },
  { id: "teaching", icon: "GraduationCap", key: "teaching" },
  { id: "payments", icon: "Receipt", key: "payments" },
  { id: "chat", icon: "MessageCircle", key: "chat" },
  { id: "security", icon: "ShieldCheck", key: "security" },
  { id: "language", icon: "Languages", key: "language" },
  { id: "faq", icon: "HelpCircle", key: "faq" },
  { id: "support", icon: "LifeBuoy", key: "support" },
];

function Section({ id, num, label, children }) {
  return (
    <section id={id} className="scroll-mt-24 mb-10">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white border-b border-amber-500/60 pb-2 mb-3">
        {num}. {label}
      </h2>
      <div className="space-y-3 text-sm sm:text-base text-gray-700 dark:text-gray-300 leading-relaxed">
        {children}
      </div>
    </section>
  );
}

function SubHeading({ children }) {
  return <h3 className="font-semibold text-amber-700 dark:text-amber-500 mt-4">{children}</h3>;
}

function Steps({ items }) {
  if (!Array.isArray(items)) return null;
  return (
    <ol className="list-decimal list-inside space-y-1 pl-1">
      {items.map((it, i) => (
        <li key={i}>{it}</li>
      ))}
    </ol>
  );
}

function Bullets({ items }) {
  if (!Array.isArray(items)) return null;
  return (
    <ul className="list-disc list-inside space-y-1 pl-1">
      {items.map((it, i) => (
        <li key={i}>{it}</li>
      ))}
    </ul>
  );
}

function Note({ children, kind }) {
  return (
    <div className="border-l-4 border-amber-500 bg-amber-50 dark:bg-amber-900/20 px-4 py-2 rounded-r text-sm">
      <span className="font-semibold text-amber-800 dark:text-amber-400">{kind}: </span>
      <span className="italic">{children}</span>
    </div>
  );
}

function FaqItem({ q, a }) {
  return (
    <div className="mb-3">
      <p className="font-semibold text-gray-900 dark:text-white">{q}</p>
      <p>{a}</p>
    </div>
  );
}

export default function HelpPage() {
  const { t } = useTranslation("common");
  const b = (key) => t(`help.body.${key}`, { defaultValue: "" });
  const arr = (key) => {
    const v = t(`help.body.${key}`, { returnObjects: true, defaultValue: [] });
    return Array.isArray(v) ? v : [];
  };
  const faqItems = arr("faq.items");

  return (
    <div className="max-w-5xl mx-auto pb-16">
      <header className="mb-8 text-center">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white">
          {t("help.title", { defaultValue: "JamiiKazini User Manual" })}
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          {t("help.subtitle", { defaultValue: "A complete guide to using every part of the platform" })}
        </p>
      </header>

      {/* Table of Contents */}
      <nav className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-10 bg-white dark:bg-gray-800 rounded-xl shadow p-3">
        {TOC.map((item) => {
          const Icon = Icons[item.icon] || Icons.Circle;
          return (
            <a
              key={item.id}
              href={`#${item.id}`}
              className="flex items-center gap-2 px-2 py-2 rounded-lg text-xs sm:text-sm text-gray-700 dark:text-gray-300 hover:bg-amber-50 dark:hover:bg-gray-700 hover:text-amber-700 dark:hover:text-amber-400 transition-colors"
            >
              <Icon size={16} className="shrink-0" />
              <span>{t(`help.toc.${item.key}`, { defaultValue: item.key })}</span>
            </a>
          );
        })}
      </nav>

      <Section id="intro" num={1} label={t("help.toc.intro")}>
        <p>{b("intro.p1")}</p>
        <SubHeading>{b("intro.subheading")}</SubHeading>
        <Bullets items={arr("intro.bullets")} />
        <p>{b("intro.p2")}</p>
      </Section>

      <Section id="getting-started" num={2} label={t("help.toc.getting_started")}>
        <SubHeading>{b("getting_started.subheading1")}</SubHeading>
        <Steps items={arr("getting_started.steps")} />
        <SubHeading>{b("getting_started.subheading2")}</SubHeading>
        <p>{b("getting_started.p1")}</p>
        <SubHeading>{b("getting_started.subheading3")}</SubHeading>
        <p>{b("getting_started.p2")}</p>
        <SubHeading>{b("getting_started.subheading4")}</SubHeading>
        <p>{b("getting_started.p3")}</p>
      </Section>

      <Section id="wallet" num={3} label={t("help.toc.wallet")}>
        <p>{b("wallet.p1")}</p>
        <SubHeading>{b("wallet.subheading1")}</SubHeading>
        <p>{b("wallet.p2")}</p>
        <SubHeading>{b("wallet.subheading2")}</SubHeading>
        <Steps items={arr("wallet.steps")} />
        <SubHeading>{b("wallet.subheading3")}</SubHeading>
        <Bullets items={arr("wallet.bullets")} />
      </Section>

      <Section id="marketplace" num={4} label={t("help.toc.marketplace")}>
        <SubHeading>{b("marketplace.subheading1")}</SubHeading>
        <Bullets items={arr("marketplace.bullets1")} />
        <SubHeading>{b("marketplace.subheading2")}</SubHeading>
        <Steps items={arr("marketplace.steps")} />
        <p>{b("marketplace.p1")}</p>
        <SubHeading>{b("marketplace.subheading3")}</SubHeading>
        <p>{b("marketplace.p2")}</p>
      </Section>

      <Section id="businesses" num={5} label={t("help.toc.businesses")}>
        <SubHeading>{b("businesses.subheading1")}</SubHeading>
        <Steps items={arr("businesses.steps")} />
        <SubHeading>{b("businesses.subheading2")}</SubHeading>
        <p>{b("businesses.p1")}</p>
        <SubHeading>{b("businesses.subheading3")}</SubHeading>
        <p>{b("businesses.p2")}</p>
        <Note kind={t("help.note_label", { defaultValue: "Note" })}>{b("businesses.note")}</Note>
        <SubHeading>{b("businesses.subheading4")}</SubHeading>
        <p>{b("businesses.p3")}</p>
        <SubHeading>{b("businesses.subheading5")}</SubHeading>
        <Bullets items={arr("businesses.bullets2")} />
      </Section>

      <Section id="multidomain" num={6} label={t("help.toc.multidomain")}>
        <p>{b("multidomain.p1")}</p>
        <Steps items={arr("multidomain.steps")} />
        <Note kind={t("help.note_label", { defaultValue: "Note" })}>{b("multidomain.note")}</Note>
      </Section>

      <Section id="institutions" num={7} label={t("help.toc.institutions")}>
        <p>{b("institutions.p1")}</p>
        <SubHeading>{b("institutions.subheading1")}</SubHeading>
        <Bullets items={arr("institutions.bullets")} />
      </Section>

      <Section id="logistics" num={8} label={t("help.toc.logistics")}>
        <Bullets items={arr("logistics.bullets")} />
      </Section>

      <Section id="realestate" num={9} label={t("help.toc.realestate")}>
        <Bullets items={arr("realestate.bullets")} />
      </Section>

      <Section id="agriculture" num={10} label={t("help.toc.agriculture")}>
        <p>{b("agriculture.p1")}</p>
      </Section>

      <Section id="construction" num={11} label={t("help.toc.construction")}>
        <p>{b("construction.p1")}</p>
      </Section>

      <Section id="teaching" num={12} label={t("help.toc.teaching")}>
        <p>{b("teaching.p1")}</p>
        <Steps items={arr("teaching.steps")} />
      </Section>

      <Section id="payments" num={13} label={t("help.toc.payments")}>
        <Bullets items={arr("payments.bullets")} />
      </Section>

      <Section id="chat" num={14} label={t("help.toc.chat")}>
        <p>{b("chat.p1")}</p>
      </Section>

      <Section id="security" num={15} label={t("help.toc.security")}>
        <Bullets items={arr("security.bullets")} />
      </Section>

      <Section id="language" num={16} label={t("help.toc.language")}>
        <p>{b("language.p1")}</p>
      </Section>

      <Section id="faq" num={17} label={t("help.toc.faq")}>
        {faqItems.map((item, i) => (
          <FaqItem key={i} q={item.q} a={item.a} />
        ))}
      </Section>

      <Section id="support" num={18} label={t("help.toc.support")}>
        <Bullets items={arr("support.bullets")} />
      </Section>
    </div>
  );
}
