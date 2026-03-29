"use client";

import { useParams } from "next/navigation";
import * as React from "react";

import { ErrorAlert } from "@/components/admin/error-alert";
import { PageHeader } from "@/components/admin/page-header";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listTenantAudit } from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import type { AuditLogEntry } from "@/types/admin";

export default function TenantAuditPage() {
  const params = useParams();
  const tenantId = Number(params.tenantId);
  const [rows, setRows] = React.useState<AuditLogEntry[]>([]);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const token = getStoredToken();
    if (!token) return;
    void (async () => {
      try {
        setRows(await listTenantAudit(token, tenantId));
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load");
      }
    })();
  }, [tenantId]);

  return (
    <div>
      <PageHeader
        title="Tenant audit log"
        description="Privileged actions recorded for this tenant."
      />
      <ErrorAlert message={error} />
      <div className="rounded-lg border border-neutral-200 bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>When</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Resource</TableHead>
              <TableHead>Details</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((r) => (
              <TableRow key={r.id}>
                <TableCell className="whitespace-nowrap text-xs">
                  {new Date(r.created_at).toLocaleString()}
                </TableCell>
                <TableCell>{r.action}</TableCell>
                <TableCell className="max-w-[180px] truncate text-xs">
                  {r.resource_type} #{r.resource_id}
                </TableCell>
                <TableCell className="max-w-md truncate text-xs text-neutral-600">
                  {r.details ? JSON.stringify(r.details) : "—"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
