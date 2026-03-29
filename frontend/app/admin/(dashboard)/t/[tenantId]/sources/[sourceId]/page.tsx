"use client";

import { useParams, useRouter } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { ErrorAlert } from "@/components/admin/error-alert";
import { PageHeader } from "@/components/admin/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  getSourceExtraction,
  postRetryExtraction,
  type SourceExtractionInspect,
} from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import { jobStatusVariant } from "@/lib/job-ui";

export default function SourceInspectPage() {
  const params = useParams();
  const router = useRouter();
  const tenantId = Number(params.tenantId);
  const sourceId = Number(params.sourceId);
  const [data, setData] = React.useState<SourceExtractionInspect | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [offset, setOffset] = React.useState(0);
  const [retrying, setRetrying] = React.useState(false);

  const load = React.useCallback(async () => {
    const token = getStoredToken();
    if (!token) return;
    setError(null);
    try {
      setData(await getSourceExtraction(token, tenantId, sourceId, offset));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, [tenantId, sourceId, offset]);

  React.useEffect(() => {
    void load();
  }, [load]);

  async function retry() {
    const token = getStoredToken();
    if (!token) return;
    setRetrying(true);
    try {
      await postRetryExtraction(token, tenantId, sourceId);
      toast.success("Extraction re-run queued");
      await load();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Retry failed");
    } finally {
      setRetrying(false);
    }
  }

  const s = data?.source;
  const failed = s?.status === "failed" || s?.status === "extraction_failed";

  return (
    <div>
      <PageHeader
        title={s?.title ?? `Source ${sourceId}`}
        description="Extracted document preview and indexed chunks."
      >
        <Button variant="outline" size="sm" onClick={() => router.back()}>
          Back
        </Button>
        {(s?.source_type === "html_page" || s?.source_type === "pdf") && (
          <Button
            type="button"
            size="sm"
            disabled={retrying}
            onClick={() => void retry()}
          >
            {retrying ? "Retrying…" : "Re-run extraction"}
          </Button>
        )}
      </PageHeader>
      <ErrorAlert message={error} />
      {failed ? (
        <p className="mb-4 text-sm text-amber-800">
          This source is in a failed state. Use re-run extraction after fixing upstream
          issues, or check crawl logs.
        </p>
      ) : null}

      {s ? (
        <div className="mb-6 space-y-2 text-sm">
          <p>
            <span className="text-neutral-500">Type:</span> {s.source_type}{" "}
            <Badge className="ml-2" variant={jobStatusVariant(s.status)}>
              {s.status}
            </Badge>
          </p>
          <p className="break-all text-neutral-700">{s.url}</p>
        </div>
      ) : null}

      {data?.document ? (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">Extracted document</CardTitle>
            <CardDescription>
              Doc #{data.document.id} · snapshot #{data.document.source_snapshot_id}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>Language: {data.document.language ?? "—"}</p>
            {data.document.page_count != null ? (
              <p>Pages: {data.document.page_count}</p>
            ) : null}
            {data.document.full_text_preview ? (
              <ScrollArea className="h-48 rounded-md border border-neutral-200 p-3 text-xs">
                <pre className="whitespace-pre-wrap font-sans">
                  {data.document.full_text_preview}
                </pre>
              </ScrollArea>
            ) : null}
          </CardContent>
        </Card>
      ) : (
        <p className="mb-6 text-sm text-neutral-500">No extraction on file yet.</p>
      )}

      <div className="rounded-lg border border-neutral-200 bg-white">
        <div className="flex items-center justify-between border-b border-neutral-200 px-4 py-2 text-sm text-neutral-600">
          <span>
            Chunks {data ? data.chunk_offset + 1 : 0}–
            {data ? data.chunk_offset + data.chunks.length : 0} of {data?.chunk_total ?? 0}
          </span>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={offset <= 0}
              onClick={() => setOffset((o) => Math.max(0, o - 100))}
            >
              Previous
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={
                !data || data.chunk_offset + data.chunks.length >= data.chunk_total
              }
              onClick={() => setOffset((o) => o + 100)}
            >
              Next
            </Button>
          </div>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>#</TableHead>
              <TableHead>Page</TableHead>
              <TableHead>Heading</TableHead>
              <TableHead>Content</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.chunks.map((c) => (
              <TableRow key={c.id}>
                <TableCell className="align-top text-xs">{c.chunk_index}</TableCell>
                <TableCell className="align-top text-xs">{c.page_number ?? "—"}</TableCell>
                <TableCell className="max-w-[140px] align-top text-xs">
                  {c.heading ?? "—"}
                </TableCell>
                <TableCell className="max-w-xl align-top text-xs whitespace-pre-wrap">
                  {c.content}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
