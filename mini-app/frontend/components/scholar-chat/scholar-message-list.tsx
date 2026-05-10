"use client";

import { useEffect, useRef } from "react";

import type { ScholarMessage } from "@/types/scholar-chat";

import { ScholarMessageBubble } from "./scholar-message-bubble";

export function ScholarMessageList({ messages }: { messages: ScholarMessage[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
      <div className="mx-auto flex max-w-4xl flex-col">
        {messages.map((message) => (
          <ScholarMessageBubble key={message.id} message={message} />
        ))}
        <div ref={bottomRef} className="h-4" />
      </div>
    </div>
  );
}
