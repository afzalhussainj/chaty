import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
export function ErrorState() {
  return (
    <div className="flex flex-col items-start gap-3 text-red-700 bg-red-50 border border-red-100 p-4 rounded-lg">
      <div className="flex items-center gap-2">
        <AlertCircle className="w-5 h-5 text-red-500" />
        <span className="font-medium">
          Something went wrong. Please try again.
        </span>
      </div>
      <p className="text-sm text-red-600/80 max-w-md">
        There was an issue connecting to the university knowledge base. Ensure
        you have a stable connection.
      </p>
    </div>);

}