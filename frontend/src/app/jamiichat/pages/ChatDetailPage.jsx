// src/app/jamiichat/pages/ChatDetailPage.jsx

import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import { ArrowLeft, Loader2, Store } from "lucide-react";
import ChatWindow from "@/app/jamiichat/components/ChatWindow";

export default function ChatDetailPage() {
  const { id: conversationId } = useParams();
  const navigate = useNavigate();
  const [conversation, setConversation] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get(`/jamiichat/conversations/${conversationId}/`)
      .then((res) => setConversation(res.data))
      .catch(() => setConversation(null))
      .finally(() => setLoading(false));
  }, [conversationId]);

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6 h-[calc(100vh-6rem)] flex flex-col">
      <div className="flex items-center gap-3 pb-3 border-b border-gray-100 dark:border-gray-700">
        <button
          onClick={() => navigate("/jamiichat")}
          className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
        ) : (
          <div>
            <p className="font-semibold text-gray-900 dark:text-white flex items-center gap-1">
              {conversation?.other_participant?.full_name || conversation?.other_participant?.email || "Mazungumzo"}
            </p>
            {conversation?.business_name && (
              <p className="text-xs text-purple-500 flex items-center gap-1">
                <Store className="w-3 h-3" /> {conversation.business_name}
              </p>
            )}
          </div>
        )}
      </div>
      <div className="flex-1 min-h-0 bg-white dark:bg-gray-800 rounded-b-2xl shadow-soft">
        <ChatWindow conversationId={conversationId} />
      </div>
    </div>
  );
}
