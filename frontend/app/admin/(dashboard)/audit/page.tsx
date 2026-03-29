"use client";

import * as React from "react";

import { ErrorAlert } from "@/components/admin/error-alert";
import { PageHeader } from "@/components/admin/page-header";
import { useAdmin } from "@/components/admin/admin-context";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listGlobalAudit } from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import type { AuditLogEntry } from "@/types/admin";

export default function GlobalAuditPage() {
  const { me, loading } = useAdmin();
  const [rows, setRows] = React.useState<AuditLogEntry[]>([]);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const token = getStoredToken();
    if (!token || !me || me.role !== "super_admin") return;
    void (async () => {
      try {
        setRows(await listGlobalAudit(token));
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load");
      }
    })();
  }, [me]);

  if (!loading && me?.role !== "super_admin") {
    return (
      <p className="text-sm text-neutral-600">Super admin access required.</p>
    );
  }

  return (
    <div>
      <PageHeader
        title="Audit log"
        description="Recent privileged actions across the platform."
      />
      <ErrorAlert message={error} />
      <div className="rounded-lg border border-neutral-200 bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>When</TableHead>
              <TableHead>Tenant</TableHead>
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
                <TableCell>{r.tenant_id ?? "—"}</TableCell>
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
