import React, { useEffect, useRef } from 'react';
import { Message } from '../types';
import { MessageBubble } from './MessageBubble';
interface MessageListProps {
  messages: Message[];
}
export function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: 'smooth'
    });
  }, [messages]);
  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
      <div className="max-w-4xl mx-auto flex flex-col">
        {messages.map((message) =>
        <MessageBubble key={message.id} message={message} />
        )}
        <div ref={bottomRef} className="h-4" />
      </div>
    </div>);

}