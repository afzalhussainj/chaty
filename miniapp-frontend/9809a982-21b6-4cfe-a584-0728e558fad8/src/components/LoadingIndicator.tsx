import React from 'react';
export function LoadingIndicator() {
  return (
    <div className="flex items-center gap-1.5 py-2 px-1">
      <div
        className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
        style={{
          animationDelay: '0ms'
        }}>
      </div>
      <div
        className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
        style={{
          animationDelay: '150ms'
        }}>
      </div>
      <div
        className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
        style={{
          animationDelay: '300ms'
        }}>
      </div>
    </div>);

}