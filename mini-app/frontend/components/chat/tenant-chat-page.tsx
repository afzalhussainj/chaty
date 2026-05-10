"use client";

import * as React from "react";

import { ScholarChatInput } from "@/components/scholar-chat/scholar-chat-input";
import { ScholarEmptyState } from "@/components/scholar-chat/scholar-empty-state";
import { ScholarHeader } from "@/components/scholar-chat/scholar-header";
import { ScholarMessageList } from "@/components/scholar-chat/scholar-message-list";
import { ApiError } from "@/lib/api";
import { tenantPrimaryCss, sessionStorageKey } from "@/lib/branding";
import { fetchPublicTenant, postPublicChatQuery } from "@/lib/public-chat-api";
import type { PublicTenantInfo } from "@/types/public-chat";
import type { ScholarMessage } from "@/types/scholar-chat";

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
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
    setMessages([]);
    if (typeof window !== "undefined") {
      sessionStorage.removeItem(sessionStorageKey(slug));
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
        {messages.length === 0 ? (
          <div className="min-h-0 flex-1 overflow-y-auto">
            <ScholarEmptyState onSelectPrompt={handleSendMessage} />
          </div>
        ) : (
          <ScholarMessageList messages={messages} />
        )}
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
