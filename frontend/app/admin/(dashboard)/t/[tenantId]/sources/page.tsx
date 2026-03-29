"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import * as React from "react";

import { ErrorAlert } from "@/components/admin/error-alert";
import { PageHeader } from "@/components/admin/page-header";
import { Badge } from "@/components/ui/badge";
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
import { listSources } from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import { jobStatusVariant } from "@/lib/job-ui";
import type { SourceSummary } from "@/types/admin";

const SOURCE_TYPES = ["", "html_page", "pdf", "manual_text"];
const STATUSES = [
  "",
  "pending",
  "discovered",
  "fetching",
  "fetched",
  "extraction_failed",
  "ready_to_index",
  "indexing",
  "indexed",
  "failed",
  "stale",
];

export default function SourcesPage() {
  const params = useParams();
  const tenantId = Number(params.tenantId);
  const [rows, setRows] = React.useState<SourceSummary[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [sourceType, setSourceType] = React.useState("");
  const [status, setStatus] = React.useState("");
  const [active, setActive] = React.useState<string>("");

  const load = React.useCallback(async () => {
    const token = getStoredToken();
    if (!token) return;
    setError(null);
    try {
      const list = await listSources(token, tenantId, {
        source_type: sourceType || undefined,
        status: status || undefined,
        is_active:
          active === ""
            ? undefined
            : active === "true"
              ? "true"
              : active === "false"
                ? "false"
                : undefined,
      });
      setRows(list);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, [tenantId, sourceType, status, active]);

  React.useEffect(() => {
    void load();
  }, [load]);

  return (
    <div>
      <PageHeader
        title="Sources"
        description="Filter by type and status. Open a row to inspect extraction and chunks."
      />
      <ErrorAlert message={error} />

      <div className="mb-6 flex flex-wrap items-end gap-4 rounded-lg border border-neutral-200 bg-white p-4">
        <div className="space-y-1">
          <Label>Type</Label>
          <select
            className="flex h-9 rounded-md border border-neutral-200 bg-white px-2 text-sm"
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
          >
            {SOURCE_TYPES.map((v) => (
              <option key={v || "all"} value={v}>
                {v || "All types"}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <Label>Status</Label>
          <select
            className="flex h-9 rounded-md border border-neutral-200 bg-white px-2 text-sm"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            {STATUSES.map((v) => (
              <option key={v || "all"} value={v}>
                {v || "All statuses"}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <Label>Active</Label>
          <select
            className="flex h-9 rounded-md border border-neutral-200 bg-white px-2 text-sm"
            value={active}
            onChange={(e) => setActive(e.target.value)}
          >
            <option value="">Any</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
        <Button type="button" variant="secondary" size="sm" onClick={() => void load()}>
          Apply
        </Button>
      </div>

      <div className="rounded-lg border border-neutral-200 bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Title</TableHead>
              <TableHead className="max-w-[200px]">URL</TableHead>
              <TableHead className="text-right">Inspect</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((s) => (
              <TableRow key={s.id}>
                <TableCell>{s.id}</TableCell>
                <TableCell>{s.source_type}</TableCell>
                <TableCell>
                  <Badge variant={jobStatusVariant(s.status)}>{s.status}</Badge>
                </TableCell>
                <TableCell className="max-w-[160px] truncate text-xs">
                  {s.title ?? "—"}
                </TableCell>
                <TableCell className="max-w-[200px] truncate text-xs">
                  {s.url}
                </TableCell>
                <TableCell className="text-right">
                  <Button asChild size="sm" variant="outline">
                    <Link href={`/admin/t/${tenantId}/sources/${s.id}`}>View</Link>
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
