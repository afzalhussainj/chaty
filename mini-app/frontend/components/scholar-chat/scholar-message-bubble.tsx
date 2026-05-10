import { BookOpen, User } from "lucide-react";

import { SupportBadge } from "@/components/chat/support-badge";
import type { ScholarMessage } from "@/types/scholar-chat";

import { ScholarCitationList } from "./scholar-citation-list";
import { ScholarErrorState } from "./scholar-error-state";
import { ScholarLoadingIndicator } from "./scholar-loading-indicator";
import { ScholarNoResultState } from "./scholar-no-result-state";

export function ScholarMessageBubble({ message }: { message: ScholarMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`mb-6 flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`flex max-w-[85%] gap-3 md:max-w-[75%] ${isUser ? "flex-row-reverse" : "flex-row"}`}
      >
        <div
          className={`mt-1 flex size-8 shrink-0 items-center justify-center rounded-full ${
            isUser ? "bg-[#1e293b] text-white" : "border border-slate-200 bg-white text-[#1e293b] shadow-sm"
          }`}
        >
          {isUser ? <User className="size-4" aria-hidden /> : <BookOpen className="size-4" aria-hidden />}
        </div>

        <div className={`flex min-w-0 flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}>
          <div
            className={`rounded-2xl px-4 py-3 shadow-sm ${
              isUser
                ? "rounded-tr-sm bg-[#1e293b] text-white"
                : "rounded-tl-sm border border-slate-200/60 bg-white text-slate-800"
            }`}
          >
            {message.isLoading ? (
              <ScholarLoadingIndicator />
            ) : message.isError ? (
              <ScholarErrorState message={message.errorMessage} />
            ) : message.noResult ? (
              <ScholarNoResultState />
            ) : (
              <>
                {!isUser && message.support ? (
                  <div className="mb-3">
                    <SupportBadge support={message.support} />
                  </div>
                ) : null}
                <div className="max-w-none text-sm leading-relaxed md:text-base">
                  {message.content.split("\n").map((paragraph, i) => (
                    <p key={i} className={i === 0 ? "mt-0" : "mt-3"}>
                      {paragraph}
                    </p>
                  ))}
                </div>
                {!isUser &&
                !message.isLoading &&
                !message.isError &&
                !message.noResult &&
                message.citations &&
                message.citations.length > 0 ? (
                  <ScholarCitationList citations={message.citations} />
                ) : null}
              </>
            )}
          </div>

          <span className="px-1 text-[10px] text-slate-400">
            {isUser ? "You" : "University assistant"}
          </span>
        </div>
      </div>
    </div>
  );
}
