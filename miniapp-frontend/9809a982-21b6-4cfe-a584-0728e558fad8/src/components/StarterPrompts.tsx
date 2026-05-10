import React from 'react';
import {
  Lightbulb,
  FileText,
  GraduationCap,
  DollarSign,
  Phone,
  Book } from
'lucide-react';
interface StarterPromptsProps {
  onSelect: (prompt: string) => void;
}
const PROMPTS = [
{
  text: 'What are the admission requirements?',
  icon: GraduationCap,
  color: 'text-blue-600',
  bg: 'bg-blue-50'
},
{
  text: 'Where can I find the fee structure?',
  icon: DollarSign,
  color: 'text-emerald-600',
  bg: 'bg-emerald-50'
},
{
  text: 'Show me the student handbook rules',
  icon: Book,
  color: 'text-amber-600',
  bg: 'bg-amber-50'
},
{
  text: 'What scholarships are available?',
  icon: Lightbulb,
  color: 'text-purple-600',
  bg: 'bg-purple-50'
},
{
  text: 'How do I contact the admissions office?',
  icon: Phone,
  color: 'text-rose-600',
  bg: 'bg-rose-50'
},
{
  text: 'What programs does the university offer?',
  icon: FileText,
  color: 'text-indigo-600',
  bg: 'bg-indigo-50'
}];

export function StarterPrompts({ onSelect }: StarterPromptsProps) {
  return (
    <div className="w-full max-w-3xl mx-auto mt-8">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {PROMPTS.map((prompt, index) => {
          const Icon = prompt.icon;
          return (
            <button
              key={index}
              onClick={() => onSelect(prompt.text)}
              className="flex items-start gap-3 p-4 bg-white border border-slate-200 rounded-xl hover:border-[#1e293b] hover:shadow-md transition-all text-left group">
              
              <div
                className={`p-2 rounded-lg ${prompt.bg} ${prompt.color} group-hover:scale-110 transition-transform`}>
                
                <Icon className="w-4 h-4" />
              </div>
              <span className="text-sm text-slate-700 font-medium leading-snug group-hover:text-[#1e293b]">
                {prompt.text}
              </span>
            </button>);

        })}
      </div>
    </div>);

}