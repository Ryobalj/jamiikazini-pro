// src/app/jamiichat/pages/JamiichatPage.jsx

import React from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { MessageCircle, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import InputField from "@/components/InputField";

export default function JamiichatPage() {
  const { id } = useParams();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Card className="h-[80vh] flex flex-col">
          <CardHeader 
            title={id ? "Conversation" : "Jamiichat"} 
            icon={<MessageCircle className="w-5 h-5" />} 
            divider 
          />
          <CardContent className="flex-1 overflow-y-auto">
            <div className="text-center text-gray-500 py-12">
              <MessageCircle className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p>Select a conversation or start a new one</p>
            </div>
          </CardContent>
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex gap-2">
              <InputField placeholder="Type a message..." className="flex-1" />
              <Button>
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}