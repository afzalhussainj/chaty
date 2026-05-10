import React from 'react';
import { BookOpen } from 'lucide-react';
import { StarterPrompts } from './StarterPrompts';
interface EmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
}
export function EmptyState({ onSelectPrompt }: EmptyStateProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-12 md:py-24">
      <div className="w-16 h-16 bg-[#1e293b] rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-slate-200">
        <BookOpen className="w-8 h-8 text-[#faf7f2]" />
      </div>

      <h2 className="text-2xl md:text-3xl font-bold font-serif text-[#1e293b] mb-3 text-center">
        How can I help you today?
      </h2>

      <p className="text-slate-500 text-center max-w-md mb-8 leading-relaxed">
        Ask me anything about the university. I'll find answers directly from
        official web pages and PDF documents.
      </p>

      <StarterPrompts onSelect={onSelectPrompt} />
    </div>);

}