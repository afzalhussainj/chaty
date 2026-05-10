import React, { useEffect, useState, useRef } from 'react';
import { Send, Trash2 } from 'lucide-react';
interface ChatInputProps {
  onSend: (message: string) => void;
  onClear: () => void;
  disabled: boolean;
  showClear: boolean;
}
export function ChatInput({
  onSend,
  onClear,
  disabled,
  showClear
}: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };
  useEffect(() => {
    if (!disabled && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [disabled]);
  return (
    <div className="w-full bg-white/80 backdrop-blur-md border-t border-slate-200 p-4 md:p-6 sticky bottom-0 z-20">
      <div className="max-w-4xl mx-auto flex items-end gap-3 relative">
        {showClear &&
        <button
          onClick={onClear}
          disabled={disabled}
          className="p-3 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0 mb-0.5"
          title="Clear chat history">
          
            <Trash2 className="w-5 h-5" />
          </button>
        }

        <div className="flex-1 relative bg-white border border-slate-300 rounded-2xl shadow-sm focus-within:border-[#1e293b] focus-within:ring-1 focus-within:ring-[#1e293b] transition-all overflow-hidden">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Ask about admissions, programs, fees, or policies..."
            className="w-full max-h-[120px] py-3.5 pl-4 pr-12 bg-transparent border-none outline-none resize-none text-slate-800 placeholder:text-slate-400 text-base leading-relaxed"
            rows={1}
            style={{
              minHeight: '52px'
            }} />
          
          <button
            onClick={handleSend}
            disabled={!input.trim() || disabled}
            className="absolute right-2 bottom-2 p-2 bg-[#1e293b] text-white rounded-xl hover:bg-[#0f172a] disabled:bg-slate-200 disabled:text-slate-400 transition-colors">
            
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="max-w-4xl mx-auto text-center mt-2">
        <p className="text-[11px] text-slate-400">
          Answers are generated from indexed university content. Verify
          important information with official departments.
        </p>
      </div>
    </div>);

}