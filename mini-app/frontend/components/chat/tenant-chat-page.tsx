"use client";

import * as React from "react";

import { ScholarChatInput } from "@/components/scholar-chat/scholar-chat-input";
import { ScholarEmptyState } from "@/components/scholar-chat/scholar-empty-state";
import { ScholarHeader } from "@/components/scholar-chat/scholar-header";
import { ScholarMessageList } from "@/components/scholar-chat/scholar-message-list";
import { ApiError } from "@/lib/api";
import { messagesStorageKey, sessionStorageKey, tenantPrimaryCss } from "@/lib/branding";
import { fetchPublicTenant, postPublicChatQuery } from "@/lib/public-chat-api";
import type { PublicTenantInfo } from "@/types/public-chat";
import type { ScholarMessage } from "@/types/scholar-chat";

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function makeGreetingMessage(): ScholarMessage {
  return {
    id: newId(),
    role: "assistant",
    content:
      "Welcome to UniBot, UET's admissions assistant. I am here to help you make confident decisions with clear, reliable answers from our knowledge base, each reply includes citations you can review. How may I assist you today?",
  };
}

function toPersistableMessages(messages: ScholarMessage[]): ScholarMessage[] {
  return messages
    .filter((m) => !m.isLoading)
    .map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      citations: m.citations,
      support: m.support,
      isError: m.isError,
      errorMessage: m.errorMessage,
      noResult: m.noResult,
    }));
}

function parseStoredMessages(raw: string | null): ScholarMessage[] {
  if (!raw) return [];
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (x): x is ScholarMessage =>
        typeof x === "object" &&
        x !== null &&
        ("role" in x && ((x as { role?: unknown }).role === "user" || (x as { role?: unknown }).role === "assistant")) &&
        "content" in x &&
        typeof (x as { content?: unknown }).content === "string",
    );
  } catch {
    return [];
  }
}

export function TenantChatPage({ slug }: { slug: string }) {
  const [tenant, setTenant] = React.useState<PublicTenantInfo | null>(null);
  const [loadError, setLoadError] = React.useState<string | null>(null);
  const [loadingTenant, setLoadingTenant] = React.useState(true);

  const [messages, setMessages] = React.useState<ScholarMessage[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [detailedMode, setDetailedMode] = React.useState(false);

  const displayTitle =
    tenant?.branding?.app_title?.trim() || tenant?.name || "UniBot";

  React.useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = parseStoredMessages(localStorage.getItem(messagesStorageKey(slug)));
    setMessages(stored.length > 0 ? stored : [makeGreetingMessage()]);
  }, [slug]);

  React.useEffect(() => {
    if (typeof window === "undefined") return;
    const persistable = toPersistableMessages(messages);
    if (persistable.length === 0) {
      localStorage.removeItem(messagesStorageKey(slug));
      return;
    }
    localStorage.setItem(messagesStorageKey(slug), JSON.stringify(persistable));
  }, [messages, slug]);

  React.useEffect(() => {
    let cancelled = false;
    setLoadingTenant(true);
    setLoadError(null);
    void (async () => {
      try {
        const t = await fetchPublicTenant(slug);
        if (!cancelled) setTenant(t);
      } catch (e) {
        if (!cancelled) {
          const msg =
            e instanceof ApiError && e.status === 404
              ? "This assistant is not available right now, or the link is incorrect."
              : e instanceof Error
                ? e.message
                : "We could not load campus details right now.";
          setLoadError(msg);
          setTenant(null);
        }
      } finally {
        if (!cancelled) setLoadingTenant(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [slug]);

  const handleSendMessage = React.useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading || !tenant) return;

      const readSessionId = (): number | undefined => {
        if (typeof window === "undefined") return undefined;
        const raw = sessionStorage.getItem(sessionStorageKey(slug));
        if (!raw) return undefined;
        const n = Number(raw);
        return Number.isFinite(n) ? n : undefined;
      };
      const saveSessionId = (id: number) => {
        sessionStorage.setItem(sessionStorageKey(slug), String(id));
      };

      const userMessage: ScholarMessage = {
        id: newId(),
        role: "user",
        content: content.trim(),
      };
      const assistantMessageId = newId();
      const loadingMessage: ScholarMessage = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        isLoading: true,
      };
      setMessages((prev) => [...prev, userMessage, loadingMessage]);
      setIsLoading(true);

      try {
        const sid = readSessionId();
        const res = await postPublicChatQuery(slug, {
          message: content.trim(),
          session_id: sid,
          answer_mode: detailedMode ? "detailed" : "concise",
          stream: false,
        });
        saveSessionId(res.session_id);

        const noResult = res.support === "none" && (!res.citations || res.citations.length === 0);

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  isLoading: false,
                  content: res.answer,
                  citations: res.citations,
                  support: res.support,
                  noResult,
                }
              : msg,
          ),
        );
      } catch (e) {
        const msg = e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Something went wrong.";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessageId
              ? {
                  ...m,
                  isLoading: false,
                  isError: true,
                  errorMessage: msg,
                  content: "",
                }
              : m,
          ),
        );
      } finally {
        setIsLoading(false);
      }
    },
    [detailedMode, isLoading, slug, tenant],
  );

  const handleClearChat = React.useCallback(() => {
    setMessages([makeGreetingMessage()]);
    if (typeof window !== "undefined") {
      sessionStorage.removeItem(sessionStorageKey(slug));
      localStorage.removeItem(messagesStorageKey(slug));
    }
  }, [slug]);

  const primary = tenantPrimaryCss(tenant?.branding?.primary_color ?? null);

  if (loadingTenant) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-[#faf7f2] px-4 py-16 text-slate-500">
        <div
          className="size-8 animate-pulse rounded-full"
          style={{ backgroundColor: `${primary}33` }}
        />
        <p className="text-sm">Getting things ready…</p>
      </div>
    );
  }

  if (loadError || !tenant) {
    return (
      <div className="mx-auto min-h-screen max-w-lg bg-[#faf7f2] px-4 py-16 text-center">
        <p className="text-slate-700">{loadError ?? "Unavailable."}</p>
        <p className="mt-2 text-sm text-slate-500">
          Please check the link and try again. If this continues, contact your university support team.
        </p>
      </div>
    );
  }

  return (
    <div
      className="flex h-screen w-full flex-col overflow-hidden bg-[#faf7f2] font-sans text-slate-900 antialiased"
      style={{ "--tenant-primary": primary } as React.CSSProperties}
    >
      <ScholarHeader displayTitle={displayTitle} />
      <main className="relative flex min-h-0 flex-1 flex-col">
        <div className="relative isolate min-h-0 flex-1 overflow-hidden">
          {/* Soft watermark behind scrollable chat; does not capture pointer events */}
          <div
            className="pointer-events-none absolute inset-0 z-0 overflow-hidden select-none"
            aria-hidden
          >
            {/* Background-image paints more reliably than a blurred <img> at very low opacity */}
            <div
              className="absolute left-1/2 top-1/2 h-[min(52vh,460px)] w-[min(92vw,480px)] -translate-x-1/2 -translate-y-1/2 bg-contain bg-center bg-no-repeat opacity-[0.22] [filter:blur(2.5px)]"
              style={{ backgroundImage: "url(/uet-logo.svg)" }}
            />
          </div>
          <div className="relative z-10 flex min-h-0 flex-1 flex-col">
            {messages.length === 0 ? (
              <div className="min-h-0 flex-1 overflow-y-auto">
                <ScholarEmptyState onSelectPrompt={handleSendMessage} />
              </div>
            ) : (
              <ScholarMessageList messages={messages} />
            )}
          </div>
        </div>
        <ScholarChatInput
          onSend={handleSendMessage}
          onClear={handleClearChat}
          disabled={isLoading}
          showClear={messages.length > 0}
          detailedMode={detailedMode}
          onDetailedModeChange={setDetailedMode}
        />
      </main>
    </div>
  );
}
