"use client";
import {useEffect, useRef} from "react";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

export default function ChatMessages() {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Example messages - replace with real data
  const messages: Message[] = [
    {
      id: "1",
      content: "Hello! How can I help you today?",
      isUser: false,
      timestamp: new Date(),
    },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({behavior: "smooth"});
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="mx-auto max-w-4xl space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`chat ${message.isUser ? "chat-end" : "chat-start"}`}>
            <div className={`chat-bubble ${message.isUser ? "bg-primary text-primary-content" : ""}`}>
              {message.content}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
