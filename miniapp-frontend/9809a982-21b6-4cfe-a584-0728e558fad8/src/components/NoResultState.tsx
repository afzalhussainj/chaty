import React from 'react';
import { SearchX, Info } from 'lucide-react';
export function NoResultState() {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 bg-slate-100 p-1.5 rounded-md">
          <SearchX className="w-5 h-5 text-slate-500" />
        </div>
        <div>
          <p className="text-slate-800 font-medium">
            I couldn't find information about this in the indexed university
            content.
          </p>
          <p className="text-slate-600 text-sm mt-1">
            I only answer based on official university web pages and PDF
            documents.
          </p>
        </div>
      </div>

      <div className="bg-blue-50/50 border border-blue-100 rounded-lg p-4 mt-2">
        <div className="flex items-center gap-2 mb-2 text-blue-800 font-medium text-sm">
          <Info className="w-4 h-4" />
          <span>Try asking about:</span>
        </div>
        <ul className="text-sm text-blue-900/80 list-disc list-inside space-y-1 ml-1">
          <li>Admissions, courses, or departments</li>
          <li>Tuition fees and financial aid</li>
          <li>Application deadlines and requirements</li>
          <li>Campus policies or student handbook rules</li>
        </ul>
      </div>
    </div>);

}