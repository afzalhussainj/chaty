import { ShieldCheck } from "lucide-react";

type ScholarHeaderProps = {
  displayTitle: string;
};

export function ScholarHeader({ displayTitle }: ScholarHeaderProps) {
  return (
    <header className="relative z-10 w-full bg-[#0f2a57] px-4 py-6 text-[#faf7f2] shadow-md md:px-8">
      <div className="mx-auto flex max-w-4xl flex-col items-start justify-between gap-4 md:flex-row md:items-center">
        <div className="flex items-center gap-3">
          <div className="size-20 shrink-0 overflow-hidden rounded-xl border border-[#f2c94c]/60 bg-[#faf7f2] p-1 shadow-inner">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/unibot-mark.svg"
              alt="UniBot logo"
              className="h-full w-full object-contain"
            />
          </div>
          <div>
            <h1 className="font-display text-xl font-bold tracking-tight md:text-2xl">{displayTitle}</h1>
            <p className="mt-1 max-w-md text-xs font-semibold uppercase tracking-wide text-[#f2c94c]">
              Your Intelligent Prospectus Assistant
            </p>
            <p className="mt-1 max-w-md text-sm leading-snug text-slate-300">
              Smart. Fast. Always Here for You.
            </p>
          </div>
        </div>

        <div className="flex max-w-[260px] items-center gap-2 rounded-md border border-[#f2c94c]/35 bg-[#0f172a]/35 px-3 py-2 text-xs text-slate-300 sm:max-w-none">
          <ShieldCheck className="size-4 shrink-0 text-emerald-400" aria-hidden />
          <span>Based on official university pages and documents</span>
        </div>
      </div>
    </header>
  );
}
