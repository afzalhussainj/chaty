import { ExternalLink, FileText, Globe } from "lucide-react";
import * as React from "react";

import type { ChatCitation } from "@/types/public-chat";
import { isSafeHttpUrl } from "@/lib/safe-url";
import { cn } from "@/lib/utils";

function sourceIcon(type: string) {
  if (type === "pdf") return <FileText className="size-3.5 shrink-0" aria-hidden />;
  return <Globe className="size-3.5 shrink-0" aria-hidden />;
}

export function CitationList({
  citations,
  primaryColor,
}: {
  citations: ChatCitation[];
  primaryColor: string;
}) {
  if (!citations.length) return null;

  return (
    <div className="mt-4 border-t border-neutral-200/80 pt-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
        Sources
      </p>
      <ol className="space-y-2">
        {citations.map((c, i) => (
          <li
            key={`${c.chunk_id}-${i}`}
            className="flex gap-2 text-sm text-neutral-800"
          >
            <span
              className="flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-medium text-white"
              style={{ backgroundColor: primaryColor }}
            >
              {i + 1}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-neutral-500">{sourceIcon(c.source_type)}</span>
                <span className="font-medium leading-snug">
                  {c.title?.trim() || "Untitled page"}
                </span>
                {c.page_number != null ? (
                  <span className="text-xs text-neutral-500">· p.{c.page_number}</span>
                ) : null}
              </div>
              {c.url && isSafeHttpUrl(c.url) ? (
                <a
                  href={c.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(
                    "mt-0.5 inline-flex max-w-full items-center gap-1 break-all text-xs font-medium underline underline-offset-2",
                    "decoration-neutral-400 hover:decoration-current",
                  )}
                  style={{ color: primaryColor }}
                >
                  {c.url}
                  <ExternalLink className="size-3 shrink-0 opacity-70" aria-hidden />
                  <span className="sr-only">(opens in new tab)</span>
                </a>
              ) : c.url ? (
                <p className="mt-0.5 break-all text-xs text-neutral-600">{c.url}</p>
              ) : (
                <p className="mt-0.5 text-xs text-neutral-500">No public link available.</p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
