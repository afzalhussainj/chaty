import React from 'react';
import { Citation } from '../types';
import { CitationCard } from './CitationCard';
interface CitationListProps {
  citations: Citation[];
}
export function CitationList({ citations }: CitationListProps) {
  if (!citations || citations.length === 0) return null;
  return (
    <div className="mt-4 pt-4 border-t border-slate-200/60">
      <h5 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
        Sources ({citations.length})
      </h5>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {citations.map((citation, index) =>
        <CitationCard key={`${citation.url}-${index}`} citation={citation} />
        )}
      </div>
    </div>);

}