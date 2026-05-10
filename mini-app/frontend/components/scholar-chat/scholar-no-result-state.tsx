import { Headphones, SearchX } from "lucide-react";

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
            The indexed sources may not cover this topic. For help, please contact support using the details below.
          </p>
        </div>
      </div>

      <div className="mt-2 rounded-lg border border-slate-200 bg-slate-50/90 p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-800">
          <Headphones className="size-4 shrink-0 text-slate-600" aria-hidden />
          <span>Support contacts</span>
        </div>
        <ul className="space-y-2 text-sm text-slate-700">
          <li>
            <span className="font-medium text-slate-900">Muhammad Faizan</span>
            <span className="mx-1.5 text-slate-400" aria-hidden>
              ·
            </span>
            <a className="text-[#1e3a5f] underline decoration-slate-300 underline-offset-2" href="tel:+923237984124">
              +92 323 7984124
            </a>
          </li>
          <li>
            <span className="font-medium text-slate-900">Muhammad Talhs</span>
            <span className="mx-1.5 text-slate-400" aria-hidden>
              ·
            </span>
            <a className="text-[#1e3a5f] underline decoration-slate-300 underline-offset-2" href="tel:+923095562445">
              +92 309 5562445
            </a>
          </li>
        </ul>
      </div>
    </div>
  );
}
