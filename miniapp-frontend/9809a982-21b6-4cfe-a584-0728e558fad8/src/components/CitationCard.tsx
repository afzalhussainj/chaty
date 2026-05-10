import React from 'react';
import { Globe, FileText, ExternalLink } from 'lucide-react';
import { Citation } from '../types';
interface CitationCardProps {
  citation: Citation;
}
function formatUrl(url: string): string {
  try {
    const parsed = new URL(url);
    return parsed.hostname + parsed.pathname;
  } catch {
    return url;
  }
}
export function CitationCard({ citation }: CitationCardProps) {
  const isPdf = citation.source_type === 'pdf';
  const borderColor = isPdf ? 'border-l-amber-400' : 'border-l-blue-500';
  const Icon = isPdf ? FileText : Globe;
  const iconColor = isPdf ? 'text-amber-500' : 'text-blue-500';
  const label = isPdf ? 'PDF Document' : 'Web Page';
  return (
    <a
      href={citation.url}
      target="_blank"
      rel="noopener noreferrer"
      className={`block bg-white border border-slate-200 border-l-4 ${borderColor} rounded-md p-3 shadow-sm hover:shadow-md transition-shadow duration-200 group relative overflow-hidden`}>
      
      <div className="flex items-start gap-3">
        <div
          className={`mt-0.5 ${iconColor} bg-slate-50 p-1.5 rounded-md border border-slate-100`}>
          
          <Icon className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h4 className="text-sm font-semibold text-slate-800 truncate pr-4 group-hover:text-slate-900 transition-colors">
              {citation.title}
            </h4>
            <ExternalLink className="w-3.5 h-3.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity absolute right-3 top-3" />
          </div>

          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
              {label}
            </span>
            {isPdf && citation.page_number &&
            <span className="text-[10px] uppercase tracking-wider font-semibold text-amber-600 bg-amber-50 border border-amber-100 px-1.5 py-0.5 rounded">
                Page {citation.page_number}
              </span>
            }
          </div>

          <p className="text-xs text-slate-400 mt-1.5 truncate max-w-[90%] font-mono">
            {formatUrl(citation.url)}
          </p>
        </div>
      </div>
    </a>);

}