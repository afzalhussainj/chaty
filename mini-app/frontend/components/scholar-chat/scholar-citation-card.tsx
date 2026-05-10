import { ExternalLink, FileText, Globe } from "lucide-react";

import type { ChatCitation } from "@/types/public-chat";

function formatUrl(url: string): string {
  try {
    const parsed = new URL(url);
    return parsed.hostname + parsed.pathname;
  } catch {
    return url;
  }
}

export function ScholarCitationCard({ citation }: { citation: ChatCitation }) {
  const isPdf = citation.source_type === "pdf";
  const borderColor = isPdf ? "border-l-amber-400" : "border-l-blue-500";
  const Icon = isPdf ? FileText : Globe;
  const iconColor = isPdf ? "text-amber-500" : "text-blue-500";
  const label = isPdf ? "PDF document" : "Web page";
  const title = citation.title?.trim() || "Untitled source";
  const url = citation.url?.trim();

  const inner = (
    <div className="flex items-start gap-3">
      <div
        className={`mt-0.5 rounded-md border border-slate-100 bg-slate-50 p-1.5 ${iconColor}`}
      >
        <Icon className="size-4" aria-hidden />
      </div>
      <div className="min-w-0 flex-1">
        <div className="relative flex items-center justify-between gap-2 pr-6">
          <h4 className="truncate pr-2 text-sm font-semibold text-slate-800 transition-colors group-hover:text-slate-900">
            {title}
          </h4>
          {url ? (
            <ExternalLink className="absolute right-0 top-0 size-3.5 text-slate-400 opacity-0 transition-opacity group-hover:opacity-100" />
          ) : null}
        </div>

        <div className="mt-1.5 flex flex-wrap items-center gap-2">
          <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            {label}
          </span>
          {isPdf && citation.page_number != null ? (
            <span className="rounded border border-amber-100 bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-600">
              Page {citation.page_number}
            </span>
          ) : null}
        </div>

        {url ? (
          <p className="mt-1.5 max-w-[90%] truncate font-mono text-xs text-slate-400">
            {formatUrl(url)}
          </p>
        ) : (
          <p className="mt-1.5 text-xs text-slate-400">URL not available</p>
        )}
      </div>
    </div>
  );

  const cardClass = `group relative block overflow-hidden rounded-md border border-slate-200 border-l-4 ${borderColor} bg-white p-3 shadow-sm transition-shadow duration-200 hover:shadow-md`;

  if (!url) {
    return <div className={cardClass}>{inner}</div>;
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={cardClass}
    >
      {inner}
    </a>
  );
}
