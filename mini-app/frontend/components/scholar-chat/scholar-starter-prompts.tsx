import { Book, DollarSign, FileText, GraduationCap, Lightbulb, Phone } from "lucide-react";

const PROMPTS = [
  { text: "What are the admission requirements?", icon: GraduationCap, color: "text-blue-600", bg: "bg-blue-50" },
  { text: "Where can I find the fee structure?", icon: DollarSign, color: "text-emerald-600", bg: "bg-emerald-50" },
  { text: "Show me the student handbook rules", icon: Book, color: "text-amber-600", bg: "bg-amber-50" },
  { text: "What scholarships are available?", icon: Lightbulb, color: "text-purple-600", bg: "bg-purple-50" },
  { text: "How do I contact the admissions office?", icon: Phone, color: "text-rose-600", bg: "bg-rose-50" },
  { text: "What programs does the university offer?", icon: FileText, color: "text-indigo-600", bg: "bg-indigo-50" },
] as const;

export function ScholarStarterPrompts({ onSelect }: { onSelect: (prompt: string) => void }) {
  return (
    <div className="mx-auto mt-8 w-full max-w-3xl">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {PROMPTS.map((prompt) => {
          const Icon = prompt.icon;
          return (
            <button
              key={prompt.text}
              type="button"
              onClick={() => onSelect(prompt.text)}
              className="group flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 text-left transition-all hover:border-[#f2c94c] hover:shadow-md"
            >
              <div
                className={`rounded-lg p-2 ${prompt.bg} ${prompt.color} transition-transform group-hover:scale-110`}
              >
                <Icon className="size-4" aria-hidden />
              </div>
              <span className="text-sm font-medium leading-snug text-slate-700 group-hover:text-[#0f2a57]">
                {prompt.text}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
