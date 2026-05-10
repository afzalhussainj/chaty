import { Info, SearchX } from "lucide-react";

export function ScholarNoResultState() {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded-md bg-slate-100 p-1.5">
          <SearchX className="size-5 text-slate-500" aria-hidden />
        </div>
        <div>
          <p className="font-medium text-slate-800">Sorry, I couldn&apos;t find a clear answer for that yet.</p>
          <p className="mt-1 text-sm text-slate-600">
            Try asking in a different way, or use the keywords you see on the university website.
          </p>
        </div>
      </div>

      <div className="mt-2 rounded-lg border border-blue-100 bg-blue-50/50 p-4">
        <div className="mb-2 flex items-center gap-2 text-sm font-medium text-blue-800">
          <Info className="size-4 shrink-0" aria-hidden />
          <span>You can ask about:</span>
        </div>
        <ul className="ml-1 list-inside list-disc space-y-1 text-sm text-blue-900/80">
          <li>Admissions, courses, or departments</li>
          <li>Tuition fees and scholarships</li>
          <li>Application dates and requirements</li>
          <li>Campus rules and student handbooks</li>
        </ul>
      </div>
    </div>
  );
}
