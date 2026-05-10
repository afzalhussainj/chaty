"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Trash2 } from "lucide-react";

type ScholarChatInputProps = {
  onSend: (message: string) => void;
  onClear: () => void;
  disabled: boolean;
  showClear: boolean;
  detailedMode: boolean;
  onDetailedModeChange: (v: boolean) => void;
};

export function ScholarChatInput({
  onSend,
  onClear,
  disabled,
  showClear,
  detailedMode,
  onDetailedModeChange,
}: ScholarChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  useEffect(() => {
    if (!disabled && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [disabled]);

  return (
    <div className="sticky bottom-0 z-20 w-full border-t border-slate-200 bg-white/80 p-4 backdrop-blur-md md:p-6">
      <div className="mx-auto mb-2 flex max-w-4xl flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500">
        <label className="flex cursor-pointer items-center gap-2">
          <input
            type="checkbox"
            checked={detailedMode}
            onChange={(e) => onDetailedModeChange(e.target.checked)}
            className="rounded border-slate-300"
          />
          Longer answers
        </label>
        <span className="hidden sm:inline">Replies appear after a short pause.</span>
      </div>
      <div className="mx-auto flex max-w-4xl items-end gap-3">
        {showClear ? (
          <button
            type="button"
            onClick={onClear}
            disabled={disabled}
            className="mb-0.5 flex-shrink-0 rounded-xl p-3 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500 disabled:cursor-not-allowed disabled:opacity-50"
            title="Start a new chat"
          >
            <Trash2 className="size-5" aria-hidden />
          </button>
        ) : null}

        <div className="relative flex-1 overflow-hidden rounded-2xl border border-slate-300 bg-white shadow-sm transition-all focus-within:border-[#0f2a57] focus-within:ring-1 focus-within:ring-[#0f2a57]">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Ask your question here…"
            className="w-full resize-none border-none bg-transparent py-3.5 pl-4 pr-12 text-base leading-relaxed text-slate-800 outline-none placeholder:text-slate-400"
            rows={1}
            style={{ minHeight: "52px", maxHeight: "120px" }}
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!input.trim() || disabled}
            className="absolute bottom-2 right-2 rounded-xl bg-[#f2c94c] p-2 text-[#0f2a57] transition-colors hover:bg-[#e0b52f] disabled:bg-slate-200 disabled:text-slate-400"
            aria-label="Send message"
          >
            <Send className="size-4" aria-hidden />
          </button>
        </div>
      </div>
      <div className="mx-auto mt-2 max-w-4xl text-center">
        <p className="text-[11px] text-slate-400">
          Answers are based on university sources. For important matters, please confirm on the official website.
        </p>
      </div>
    </div>
  );
}
