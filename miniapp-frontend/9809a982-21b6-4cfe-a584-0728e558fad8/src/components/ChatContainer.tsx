import React, { useCallback, useState } from 'react';
import { Message } from '../types';
import { fetchChatResponse } from '../lib/mockApi';
import { EmptyState } from './EmptyState';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
export function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const handleSendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: content.trim()
      };
      const assistantMessageId = (Date.now() + 1).toString();
      const loadingMessage: Message = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        isLoading: true
      };
      setMessages((prev) => [...prev, userMessage, loadingMessage]);
      setIsLoading(true);
      try {
        const response = await fetchChatResponse(content);
        setMessages((prev) =>
        prev.map((msg) =>
        msg.id === assistantMessageId ?
        {
          ...msg,
          isLoading: false,
          content: response.answer,
          citations: response.citations,
          noResult: response.noResult
        } :
        msg
        )
        );
      } catch (error) {
        setMessages((prev) =>
        prev.map((msg) =>
        msg.id === assistantMessageId ?
        {
          ...msg,
          isLoading: false,
          isError: true,
          content: ''
        } :
        msg
        )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading]
  );
  const handleClearChat = useCallback(() => {
    setMessages([]);
  }, []);
  return (
    <div className="flex-1 flex flex-col relative bg-[#faf7f2] min-h-0">
      {messages.length === 0 ?
      <div className="flex-1 overflow-y-auto">
          <EmptyState onSelectPrompt={handleSendMessage} />
        </div> :

      <MessageList messages={messages} />
      }

      <div className="mt-auto">
        <ChatInput
          onSend={handleSendMessage}
          onClear={handleClearChat}
          disabled={isLoading}
          showClear={messages.length > 0} />
        
      </div>
    </div>);

}