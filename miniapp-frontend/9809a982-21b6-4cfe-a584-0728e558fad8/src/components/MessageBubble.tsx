import React from 'react';
import { Message } from '../types';
import { CitationList } from './CitationList';
import { LoadingIndicator } from './LoadingIndicator';
import { ErrorState } from './ErrorState';
import { NoResultState } from './NoResultState';
import { User, BookOpen } from 'lucide-react';
interface MessageBubbleProps {
  message: Message;
}
export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  return (
    <div
      className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      
      <div
        className={`flex max-w-[85%] md:max-w-[75%] gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1 ${isUser ? 'bg-[#1e293b] text-white' : 'bg-white border border-slate-200 text-[#1e293b] shadow-sm'}`}>
          
          {isUser ?
          <User className="w-4 h-4" /> :

          <BookOpen className="w-4 h-4" />
          }
        </div>

        {/* Message Content Container */}
        <div
          className={`flex flex-col gap-2 min-w-0 ${isUser ? 'items-end' : 'items-start'}`}>
          
          {/* Bubble */}
          <div
            className={`px-4 py-3 rounded-2xl shadow-sm ${isUser ? 'bg-[#1e293b] text-white rounded-tr-sm' : 'bg-white border border-slate-200/60 text-slate-800 rounded-tl-sm'}`}>
            
            {message.isLoading ?
            <LoadingIndicator /> :
            message.isError ?
            <ErrorState /> :
            message.noResult ?
            <NoResultState /> :

            <div className="max-w-none text-sm md:text-base leading-relaxed">
                {message.content.split('\n').map((paragraph, i) =>
              <p key={i} className={i === 0 ? 'mt-0' : 'mt-3'}>
                    {paragraph}
                  </p>
              )}
              </div>
            }

            {/* Citations */}
            {!isUser &&
            !message.isLoading &&
            !message.isError &&
            !message.noResult &&
            message.citations &&
            message.citations.length > 0 &&
            <CitationList citations={message.citations} />
            }
          </div>

          <span className="text-[10px] text-slate-400 px-1">
            {isUser ? 'You' : 'University Assistant'}
          </span>
        </div>
      </div>
    </div>);

}