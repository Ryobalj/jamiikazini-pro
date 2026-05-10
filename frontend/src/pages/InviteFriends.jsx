// src/pages/InviteFriends.jsx
import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  FaWhatsapp,
  FaFacebook,
  FaTelegram,
  FaXTwitter,
  FaInstagram,
  FaLinkedin,
  FaTiktok,
  FaCopy,
} from "react-icons/fa6";
import { useAppContext } from "@/context/AppContext"; // adjust path if needed

const InviteFriends = () => {
  const { t } = useTranslation();
  const { user } = useAppContext();
  const [copied, setCopied] = useState(false);

  const shareUrl = "https://jamiikazini.com"; // 🔁 Dev link if needed
  const userName = user?.full_name?.trim();
  const shareText = userName
    ? `${userName} ${t("invite.invites_you")}`
    : t("invite.share_text");

  const fullText = `${shareText} ${shareUrl}`;
  const encodedText = encodeURIComponent(fullText);

  const links = {
    whatsapp: `https://wa.me/?text=${encodedText}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
    telegram: `https://t.me/share/url?url=${encodedText}`,
    twitter: `https://x.com/intent/tweet?text=${encodedText}`,
    linkedin: `https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(
      shareUrl
    )}&title=${encodeURIComponent(shareText)}`,
    instagram: `https://www.instagram.com/`, // not sharable link
    tiktok: `https://www.tiktok.com/`, // not sharable link
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  return (
    <div className="p-4 bg-white rounded-xl shadow-md max-w-md mx-auto text-center">
      <h2 className="text-xl font-semibold text-gray-800 mb-3">
        {t("invite.title")}
      </h2>

      <div className="grid gap-3">
        <a href={links.whatsapp} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition">
          <FaWhatsapp className="mr-2" /> WhatsApp
        </a>
        <a href={links.facebook} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition">
          <FaFacebook className="mr-2" /> Facebook
        </a>
        <a href={links.telegram} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center bg-sky-500 text-white py-2 rounded-lg hover:bg-sky-600 transition">
          <FaTelegram className="mr-2" /> Telegram
        </a>
        <a href={links.twitter} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center bg-black text-white py-2 rounded-lg hover:bg-gray-900 transition">
          <FaXTwitter className="mr-2" /> X (Twitter)
        </a>
        <a href={links.linkedin} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center bg-blue-800 text-white py-2 rounded-lg hover:bg-blue-900 transition">
          <FaLinkedin className="mr-2" /> LinkedIn
        </a>
        <a href={links.instagram} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center bg-pink-500 text-white py-2 rounded-lg hover:bg-pink-600 transition">
          <FaInstagram className="mr-2" /> Instagram
        </a>
        <a href={links.tiktok} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center bg-black text-white py-2 rounded-lg hover:bg-gray-800 transition">
          <FaTiktok className="mr-2" /> TikTok
        </a>

        <button
          onClick={handleCopy}
          className="flex items-center justify-center bg-gray-800 text-white py-2 rounded-lg hover:bg-gray-900 transition"
        >
          <FaCopy className="mr-2" />{" "}
          {copied ? t("invite.link_copied") : t("invite.copy_link")}
        </button>
      </div>
    </div>
  );
};

export default InviteFriends;