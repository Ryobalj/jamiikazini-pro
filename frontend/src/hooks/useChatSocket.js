// src/hooks/useChatSocket.js

import { useEffect, useRef, useState, useCallback } from "react";
import api from "@/lib/axios";

function getWsBaseUrl() {
  const httpBase = api.defaults.baseURL.replace(/\/api\/v1\/?$/, "");
  return httpBase.replace(/^http/, "ws");
}

/**
 * Inaunganisha WebSocket ya mazungumzo maalum na inarudisha ujumbe unaokuja
 * papo hapo. Historia ya awali (REST) haihusiki hapa - ipakie tofauti.
 */
export function useChatSocket(conversationId, { onMessage } = {}) {
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    if (!conversationId) return undefined;

    const token = localStorage.getItem("access_token");
    const url = `${getWsBaseUrl()}/ws/chat/${conversationId}/?token=${encodeURIComponent(token || "")}`;
    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage?.(data);
      } catch {
        // ignore malformed frames
      }
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]);

  const sendMessage = useCallback((content) => {
    const socket = socketRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ content }));
      return true;
    }
    return false;
  }, []);

  return { connected, sendMessage };
}
