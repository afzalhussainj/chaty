import { BookOpen } from "lucide-react";

import { ScholarStarterPrompts } from "./scholar-starter-prompts";

export function ScholarEmptyState({ onSelectPrompt }: { onSelectPrompt: (prompt: string) => void }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 py-12 md:py-24">
      <div className="mb-6 flex size-16 items-center justify-center rounded-2xl bg-[#1e293b] shadow-lg shadow-slate-200">
        <BookOpen className="size-8 text-[#faf7f2]" aria-hidden />
      </div>

      <h2 className="mb-3 text-center font-display text-2xl font-bold text-[#1e293b] md:text-3xl">
        Your Intelligent Prospectus Assistant
      </h2>

      <p className="mb-8 max-w-md text-center leading-relaxed text-slate-500">
        Smart. Fast. Always Here for You. Ask about admissions, programs, fees, campus life, or
        university rules.
      </p>

      <ScholarStarterPrompts onSelect={onSelectPrompt} />
    </div>
  );
}
