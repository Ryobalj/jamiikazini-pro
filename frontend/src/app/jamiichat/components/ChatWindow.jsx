// src/app/jamiichat/components/ChatWindow.jsx

import React, { useState, useEffect, useRef, useCallback } from "react";
import api from "@/lib/axios";
import { Send, Loader2, Wifi, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "react-toastify";
import { useChatSocket } from "@/hooks/useChatSocket";
import { useAppContext } from "@/context/AppContext";

export default function ChatWindow({ conversationId }) {
  const { user } = useAppContext();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [draft, setDraft] = useState("");
  const bottomRef = useRef(null);

  const handleIncoming = useCallback((message) => {
    setMessages((prev) => (prev.some((m) => m.id === message.id) ? prev : [...prev, message]));
  }, []);

  const { connected, sendMessage } = useChatSocket(conversationId, { onMessage: handleIncoming });

  useEffect(() => {
    if (!conversationId) return;
    setLoading(true);
    api
      .get(`/jamiichat/conversations/${conversationId}/messages/`)
      .then((res) => setMessages(res.data || []))
      .catch(() => toast.error("Imeshindwa kupakia ujumbe."))
      .finally(() => setLoading(false));
    api.post(`/jamiichat/conversations/${conversationId}/mark-read/`).catch(() => {});
  }, [conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text) return;
    const sent = sendMessage(text);
    if (!sent) {
      toast.error("Muunganisho umekatika. Jaribu tena.");
      return;
    }
    setDraft("");
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-end gap-1 px-3 py-1 text-xs text-gray-400">
        {connected ? (
          <>
            <Wifi className="w-3 h-3 text-green-500" /> Mtandaoni
          </>
        ) : (
          <>
            <WifiOff className="w-3 h-3 text-gray-400" /> Inaunganisha...
          </>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        {loading ? (
          <Loader2 className="w-6 h-6 animate-spin mx-auto text-gray-400 mt-8" />
        ) : messages.length === 0 ? (
          <p className="text-sm text-gray-400 text-center mt-8">Hakuna ujumbe bado. Anzisha mazungumzo!</p>
        ) : (
          messages.map((m) => {
            // FlexibleIDField huserialize user.id kama string upande wa
            // /auth/me/, wakati m.sender inatoka WebSocket/Message serializer
            // kama namba - String() inazuia === isishindwe kimya kimya.
            const isMine = String(m.sender) === String(user?.id);
            return (
              <div key={m.id} className={`flex ${isMine ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[75%] px-3 py-2 rounded-2xl text-sm ${
                    isMine
                      ? "bg-purple-600 text-white rounded-br-sm"
                      : "bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-bl-sm"
                  }`}
                >
                  {!isMine && <p className="text-[10px] font-medium opacity-70 mb-0.5">{m.sender_name}</p>}
                  <p className="whitespace-pre-line break-words">{m.content}</p>
                </div>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="flex items-center gap-2 p-3 border-t border-gray-100 dark:border-gray-700">
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Andika ujumbe..."
          className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-full bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-purple-500"
        />
        <Button type="submit" size="sm" className="bg-purple-600 hover:bg-purple-700 rounded-full w-10 h-10 p-0">
          <Send className="w-4 h-4" />
        </Button>
      </form>
    </div>
  );
}
