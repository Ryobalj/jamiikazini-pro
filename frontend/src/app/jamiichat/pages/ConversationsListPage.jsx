// src/app/jamiichat/pages/ConversationsListPage.jsx

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import { MessageCircle, Loader2, Store } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function ConversationsListPage() {
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/jamiichat/conversations/")
      .then((res) => setConversations(res.data?.results || res.data || []))
      .catch(() => setConversations([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <Card>
        <CardHeader title="Mazungumzo Yangu" icon={<MessageCircle className="w-5 h-5" />} divider />
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : conversations.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
              Huna mazungumzo bado.
            </p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {conversations.map((c) => (
                <button
                  key={c.id}
                  onClick={() => navigate(`/jamiichat/${c.id}`)}
                  className="w-full flex items-center justify-between py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 -mx-2 px-2 rounded-lg transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 font-semibold">
                      {c.other_participant?.full_name?.[0]?.toUpperCase() || "?"}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white flex items-center gap-1">
                        {c.other_participant?.full_name || c.other_participant?.email || "Mtumiaji"}
                        {c.business_name && (
                          <span className="flex items-center gap-0.5 text-xs text-purple-500">
                            <Store className="w-3 h-3" /> {c.business_name}
                          </span>
                        )}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-[220px]">
                        {c.last_message?.content || "..."}
                      </p>
                    </div>
                  </div>
                  {c.unread_count > 0 && (
                    <span className="bg-purple-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {c.unread_count}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
