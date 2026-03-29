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
import { listCrawlJobs } from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import { jobStatusVariant } from "@/lib/job-ui";
import type { CrawlJob } from "@/types/admin";

export default function CrawlJobsPage() {
  const params = useParams();
  const tenantId = Number(params.tenantId);
  const [rows, setRows] = React.useState<CrawlJob[]>([]);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const token = getStoredToken();
    if (!token) return;
    void (async () => {
      try {
        setRows(await listCrawlJobs(token, tenantId));
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load");
      }
    })();
  }, [tenantId]);

  return (
    <div>
      <PageHeader
        title="Crawl jobs"
        description="Recent crawl runs for this tenant (newest first)."
      />
      <ErrorAlert message={error} />
      <div className="rounded-lg border border-neutral-200 bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Config</TableHead>
              <TableHead>Started</TableHead>
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
                <TableCell>{j.crawl_config_id ?? "—"}</TableCell>
                <TableCell className="whitespace-nowrap text-xs">
                  {j.started_at
                    ? new Date(j.started_at).toLocaleString()
                    : "—"}
                </TableCell>
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
