"use client";

import { useParams } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { ErrorAlert } from "@/components/admin/error-alert";
import { PageHeader } from "@/components/admin/page-header";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { postChatQuery } from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import type { ChatQueryResponse } from "@/types/admin";
import { Badge } from "@/components/ui/badge";

export default function ChatTestPage() {
  const params = useParams();
  const tenantId = Number(params.tenantId);
  const [message, setMessage] = React.useState("");
  const [mode, setMode] = React.useState<"concise" | "detailed">("concise");
  const [result, setResult] = React.useState<ChatQueryResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);

  async function send() {
    const token = getStoredToken();
    if (!token || !message.trim()) {
      toast.error("Enter a message.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const r = await postChatQuery(token, tenantId, {
        message: message.trim(),
        answer_mode: mode,
        stream: false,
      });
      setResult(r);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Request failed";
      setError(msg);
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Chat test"
        description="Grounded RAG answers with citations (same API as the public chatbot)."
      />
      <ErrorAlert message={error} />

      <div className="mb-6 max-w-xl space-y-4 rounded-lg border border-neutral-200 bg-white p-4">
        <div className="flex gap-2">
          <Button
            type="button"
            size="sm"
            variant={mode === "concise" ? "default" : "outline"}
            onClick={() => setMode("concise")}
          >
            Concise
          </Button>
          <Button
            type="button"
            size="sm"
            variant={mode === "detailed" ? "default" : "outline"}
            onClick={() => setMode("detailed")}
          >
            Detailed
          </Button>
        </div>
        <div className="space-y-2">
          <Label htmlFor="msg">Message</Label>
          <Textarea
            id="msg"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={4}
          />
        </div>
        <Button type="button" disabled={busy} onClick={() => void send()}>
          {busy ? "Sending…" : "Send"}
        </Button>
      </div>

      {result ? (
        <div className="space-y-6">
          <div className="rounded-lg border border-neutral-200 bg-white p-4">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium text-neutral-700">Support</span>
              <Badge variant="secondary">{result.support}</Badge>
              <span className="text-xs text-neutral-500">
                session {result.session_id}
              </span>
            </div>
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{result.answer}</p>
          </div>

          <div>
            <h2 className="mb-2 text-sm font-semibold text-neutral-800">Citations</h2>
            <div className="rounded-lg border border-neutral-200 bg-white">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>URL</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Page</TableHead>
                    <TableHead>Score</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {result.citations.map((c, i) => (
                    <TableRow key={`${c.chunk_id}-${i}`}>
                      <TableCell className="max-w-[200px] text-xs">
                        {c.title ?? "—"}
                      </TableCell>
                      <TableCell className="max-w-xs truncate text-xs">
                        {c.url ? (
                          <a
                            href={c.url}
                            className="text-blue-700 underline"
                            target="_blank"
                            rel="noreferrer"
                          >
                            {c.url}
                          </a>
                        ) : (
                          "—"
                        )}
                      </TableCell>
                      <TableCell className="text-xs">{c.source_type}</TableCell>
                      <TableCell className="text-xs">{c.page_number ?? "—"}</TableCell>
                      <TableCell className="text-xs">{c.score.toFixed(4)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>

          <details className="text-xs text-neutral-500">
            <summary className="cursor-pointer">Retrieval metadata (no prompts)</summary>
            <pre className="mt-2 overflow-auto rounded bg-neutral-100 p-2">
              {JSON.stringify(result.retrieval, null, 2)}
            </pre>
          </details>
        </div>
      ) : null}
    </div>
  );
}
