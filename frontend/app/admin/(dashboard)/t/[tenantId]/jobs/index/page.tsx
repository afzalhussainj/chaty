"use client";

import { useParams } from "next/navigation";
import * as React from "react";

import { ErrorAlert } from "@/components/admin/error-alert";
import { PageHeader } from "@/components/admin/page-header";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listIndexJobs } from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import { jobStatusVariant } from "@/lib/job-ui";
import type { IndexJob } from "@/types/admin";

export default function IndexJobsPage() {
  const params = useParams();
  const tenantId = Number(params.tenantId);
  const [rows, setRows] = React.useState<IndexJob[]>([]);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const token = getStoredToken();
    if (!token) return;
    void (async () => {
      try {
        setRows(await listIndexJobs(token, tenantId));
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load");
      }
    })();
  }, [tenantId]);

  return (
    <div>
      <PageHeader
        title="Index jobs"
        description="Embedding and indexing pipeline runs."
      />
      <ErrorAlert message={error} />
      <div className="rounded-lg border border-neutral-200 bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Source</TableHead>
              <TableHead>Document</TableHead>
              <TableHead>Error</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((j) => (
              <TableRow key={j.id}>
                <TableCell className="font-mono text-xs">{j.id}</TableCell>
                <TableCell className="text-xs">{j.job_type}</TableCell>
                <TableCell>
                  <Badge variant={jobStatusVariant(j.status)}>{j.status}</Badge>
                </TableCell>
                <TableCell>{j.source_id ?? "—"}</TableCell>
                <TableCell>{j.extracted_document_id ?? "—"}</TableCell>
                <TableCell className="max-w-xs truncate text-xs text-red-700">
                  {j.error_message ?? "—"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
