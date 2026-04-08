import { AlertTriangle, CheckCircle2, HelpCircle } from "lucide-react";

import { cn } from "@/lib/utils";

export function SupportBadge({ support }: { support: string | undefined }) {
  const s = (support ?? "none").toLowerCase();
  if (s === "high") {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-900",
        )}
      >
        <CheckCircle2 className="size-3.5" aria-hidden />
        Grounded in indexed content
      </span>
    );
  }
  if (s === "partial") {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-950",
        )}
      >
        <HelpCircle className="size-3.5" aria-hidden />
        Partial match — verify with sources
      </span>
    );
  }
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border border-neutral-200 bg-neutral-100 px-2 py-0.5 text-xs font-medium text-neutral-700",
      )}
    >
      <AlertTriangle className="size-3.5" aria-hidden />
      Limited indexed content for this question
    </span>
  );
}
