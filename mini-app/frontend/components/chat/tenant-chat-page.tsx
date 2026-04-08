"use client";

import { Building2, Send } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { tenantPrimaryCss, sessionStorageKey } from "@/lib/branding";
import { fetchPublicTenant, postPublicChatQuery } from "@/lib/public-chat-api";
import { ApiError } from "@/lib/api";
import type { ChatTurn, PublicTenantInfo } from "@/types/public-chat";

import { CitationList } from "./citation-list";
import { SupportBadge } from "./support-badge";

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function TenantChatPage({ slug }: { slug: string }) {
  const [tenant, setTenant] = React.useState<PublicTenantInfo | null>(null);
  const [loadError, setLoadError] = React.useState<string | null>(null);
  const [loadingTenant, setLoadingTenant] = React.useState(true);

  const [turns, setTurns] = React.useState<ChatTurn[]>([]);
  const [input, setInput] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const [detailMode, setDetailMode] = React.useState(false);

  const scrollRef = React.useRef<HTMLDivElement>(null);
  const bottomRef = React.useRef<HTMLDivElement>(null);

  const primary = tenantPrimaryCss(tenant?.branding?.primary_color ?? null);
  const displayTitle =
    tenant?.branding?.app_title?.trim() || tenant?.name || "Campus assistant";

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
              ? "This campus assistant is not available or the link is incorrect."
              : e instanceof Error
                ? e.message
                : "Could not load campus information.";
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

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, sending]);

  function readSessionId(): number | undefined {
    if (typeof window === "undefined") return undefined;
    const raw = sessionStorage.getItem(sessionStorageKey(slug));
    if (!raw) return undefined;
    const n = Number(raw);
    return Number.isFinite(n) ? n : undefined;
  }

  function saveSessionId(id: number) {
    sessionStorage.setItem(sessionStorageKey(slug), String(id));
  }

  async function sendMessage() {
    const text = input.trim();
    if (!text || sending || !tenant) return;

    setInput("");
    const userTurn: ChatTurn = {
      id: newId(),
      role: "user",
      content: text,
    };
    setTurns((prev) => [...prev, userTurn]);
    setSending(true);

    try {
      const sid = readSessionId();
      const res = await postPublicChatQuery(slug, {
        message: text,
        session_id: sid,
        answer_mode: detailMode ? "detailed" : "concise",
        stream: false,
      });
      saveSessionId(res.session_id);

      setTurns((prev) => [
        ...prev,
        {
          id: newId(),
          role: "assistant",
          content: res.answer,
          citations: res.citations,
          support: res.support,
        },
      ]);
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? e.message
          : e instanceof Error
            ? e.message
            : "Something went wrong.";
      setTurns((prev) => [
        ...prev,
        {
          id: newId(),
          role: "assistant",
          content: msg,
          error: true,
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  if (loadingTenant) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 px-4 py-16 text-neutral-500">
        <div
          className="size-8 animate-pulse rounded-full"
          style={{ backgroundColor: `${primary}33` }}
        />
        <p className="text-sm">Loading assistant…</p>
      </div>
    );
  }

  if (loadError || !tenant) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-neutral-700">{loadError ?? "Unavailable."}</p>
        <p className="mt-2 text-sm text-neutral-500">
          Check the link or contact your institution if this problem continues.
        </p>
      </div>
    );
  }

  return (
    <div
      className="flex min-h-0 flex-1 flex-col"
      style={
        {
          "--tenant-primary": primary,
        } as React.CSSProperties
      }
    >
      <header
        className="shrink-0 border-b border-neutral-200/90 bg-white/95 px-4 py-4 backdrop-blur-sm sm:px-6"
      >
        <div className="mx-auto flex max-w-3xl items-center gap-3">
          {tenant.branding?.logo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={tenant.branding.logo_url}
              alt=""
              className="h-10 w-auto max-w-[160px] object-contain object-left"
            />
          ) : (
            <div
              className="flex size-10 shrink-0 items-center justify-center rounded-xl text-white shadow-sm"
              style={{ backgroundColor: primary }}
              aria-hidden
            >
              <Building2 className="size-5" />
            </div>
          )}
          <div className="min-w-0">
            <h1 className="truncate text-lg font-semibold tracking-tight text-neutral-900">
              {displayTitle}
            </h1>
            <p className="truncate text-sm text-neutral-500">{tenant.name}</p>
          </div>
        </div>
      </header>

      <div
        ref={scrollRef}
        className="min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-6"
      >
        <div className="mx-auto max-w-3xl space-y-4 pb-4">
          <aside
            className="rounded-lg border border-neutral-200 bg-neutral-50/90 px-4 py-3 text-sm leading-relaxed text-neutral-700"
            role="note"
          >
            <strong className="font-medium text-neutral-900">How this works:</strong>{" "}
            Answers are drawn only from your university&apos;s indexed website and document
            content — not from general web knowledge. Always confirm critical details (deadlines,
            fees, requirements) on official pages.
          </aside>

          {turns.length === 0 ? (
            <div className="rounded-xl border border-dashed border-neutral-200 bg-white px-4 py-10 text-center">
              <p className="text-neutral-700">
                Ask about policies, programs, services, or other topics covered on indexed
                pages.
              </p>
              <p className="mt-2 text-sm text-neutral-500">
                Responses include source links so you can verify information.
              </p>
            </div>
          ) : null}

          {turns.map((t) =>
            t.role === "user" ? (
              <div key={t.id} className="flex justify-end">
                <div
                  className="max-w-[min(100%,32rem)] rounded-2xl px-4 py-3 text-sm leading-relaxed text-white shadow-sm"
                  style={{ backgroundColor: primary }}
                >
                  {t.content}
                </div>
              </div>
            ) : (
              <div
                key={t.id}
                className="flex justify-start"
              >
                <div
                  className={`max-w-[min(100%,40rem)] rounded-2xl border px-4 py-3 text-sm leading-relaxed shadow-sm ${
                    t.error
                      ? "border-red-200 bg-red-50 text-red-900"
                      : "border-neutral-200 bg-white text-neutral-900"
                  }`}
                >
                  {!t.error && t.support ? (
                    <div className="mb-3">
                      <SupportBadge support={t.support} />
                    </div>
                  ) : null}
                  <div className="whitespace-pre-wrap">{t.content}</div>
                  {!t.error && t.citations && t.citations.length > 0 ? (
                    <CitationList citations={t.citations} primaryColor={primary} />
                  ) : null}
                </div>
              </div>
            ),
          )}

          {sending ? (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-neutral-200 bg-white px-4 py-3 text-sm text-neutral-500">
                Reading indexed content…
              </div>
            </div>
          ) : null}

          <div ref={bottomRef} />
        </div>
      </div>

      <footer className="shrink-0 border-t border-neutral-200 bg-white px-4 py-3 sm:px-6">
        <div className="mx-auto flex max-w-3xl flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-neutral-500">
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                checked={detailMode}
                onChange={(e) => setDetailMode(e.target.checked)}
                className="rounded border-neutral-300"
              />
              More detailed answers
            </label>
            <span className="hidden sm:inline">
              Streaming is not available yet — answers arrive in one step.
            </span>
          </div>
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your question…"
              rows={2}
              className="min-h-[52px] flex-1 resize-none text-base sm:text-sm"
              disabled={sending}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void sendMessage();
                }
              }}
            />
            <Button
              type="button"
              size="icon"
              className="h-[52px] w-12 shrink-0 text-white"
              style={{ backgroundColor: primary }}
              disabled={sending || !input.trim()}
              onClick={() => void sendMessage()}
              aria-label="Send message"
            >
              <Send className="size-5" />
            </Button>
          </div>
        </div>
      </footer>
    </div>
  );
}
