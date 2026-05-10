import React from 'react';
import { BookOpen, ShieldCheck } from 'lucide-react';
export function Header() {
  return (
    <header className="w-full bg-[#1e293b] text-[#faf7f2] py-6 px-4 md:px-8 shadow-md relative z-10">
      <div className="max-w-4xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="bg-[#0f172a] p-2 rounded-lg border border-slate-700">
            <BookOpen className="w-6 h-6 text-[#faf7f2]" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold font-serif tracking-tight">
              University Assistant
            </h1>
            <p className="text-sm text-slate-300 max-w-md mt-1 leading-snug">
              Ask questions about admissions, programs, policies, fees, and more
              — powered by indexed university website content.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-[#0f172a]/50 px-3 py-2 rounded-md border border-slate-700/50 text-xs text-slate-300 whitespace-nowrap">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Answers sourced from official pages & PDFs</span>
        </div>
      </div>
    </header>);

}