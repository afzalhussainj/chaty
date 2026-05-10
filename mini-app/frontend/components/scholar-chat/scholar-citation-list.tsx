import type { ChatCitation } from "@/types/public-chat";

import { ScholarCitationCard } from "./scholar-citation-card";

export function ScholarCitationList({ citations }: { citations: ChatCitation[] }) {
  if (!citations?.length) return null;
  return (
    <div className="mt-4 border-t border-slate-200/60 pt-4">
      <h5 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Sources ({citations.length})
      </h5>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {citations.map((citation) => (
          <ScholarCitationCard key={`${citation.chunk_id}-${citation.source_id}`} citation={citation} />
        ))}
      </div>
    </div>
  );
}
