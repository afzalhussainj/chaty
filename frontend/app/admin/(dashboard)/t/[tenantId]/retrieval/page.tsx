"use client";

import { useParams } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { ErrorAlert } from "@/components/admin/error-alert";
import { PageHeader } from "@/components/admin/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { postRetrievalDebug } from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import type { RetrievalDebugResponse } from "@/types/admin";

export default function RetrievalTestPage() {
  const params = useParams();
  const tenantId = Number(params.tenantId);
  const [query, setQuery] = React.useState("");
  const [topK, setTopK] = React.useState(8);
  const [result, setResult] = React.useState<RetrievalDebugResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);

  async function run() {
    const token = getStoredToken();
    if (!token || !query.trim()) {
      toast.error("Enter a query.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const r = await postRetrievalDebug(token, tenantId, {
        query: query.trim(),
        top_k: topK,
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
        title="Retrieval test"
        description="Admin hybrid search debug (tenant-isolated). Separate from end-user chat."
      />
      <ErrorAlert message={error} />

      <div className="mb-6 max-w-xl space-y-4 rounded-lg border border-neutral-200 bg-white p-4">
        <div className="space-y-2">
          <Label htmlFor="q">Query</Label>
          <Textarea
            id="q"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={3}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="k">Top K</Label>
          <Input
            id="k"
            type="number"
            min={1}
            max={50}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
          />
        </div>
        <Button type="button" disabled={busy} onClick={() => void run()}>
          {busy ? "Searching…" : "Run retrieval"}
        </Button>
      </div>

      {result ? (
        <div className="space-y-4">
          <p className="text-sm text-neutral-600">
            Normalized: <code className="text-xs">{result.query_normalized}</code> ·
            vector pool {result.vector_candidates} · fts {result.fts_candidates} ·
            weights {result.weight_vector.toFixed(2)} / {result.weight_fts.toFixed(2)}
          </p>
          <div className="rounded-lg border border-neutral-200 bg-white">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Score</TableHead>
                  <TableHead>Chunk</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Page</TableHead>
                  <TableHead>Content</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {result.chunks.map((c) => (
                  <TableRow key={c.chunk_id}>
                    <TableCell className="align-top text-xs">
                      {c.score.toFixed(4)}
                    </TableCell>
                    <TableCell className="align-top font-mono text-xs">
                      {c.chunk_id}
                    </TableCell>
                    <TableCell className="align-top text-xs">{c.title ?? "—"}</TableCell>
                    <TableCell className="align-top text-xs">
                      {c.page_number ?? "—"}
                    </TableCell>
                    <TableCell className="max-w-lg align-top text-xs whitespace-pre-wrap">
                      {c.content}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      ) : null}
    </div>
  );
}
