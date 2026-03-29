"use client";

import * as React from "react";
import { toast } from "sonner";

import { ErrorAlert } from "@/components/admin/error-alert";
import { PageHeader } from "@/components/admin/page-header";
import { useAdmin } from "@/components/admin/admin-context";
import { Badge } from "@/components/ui/badge";
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
import { createTenant, listTenants } from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import type { Tenant } from "@/types/admin";

export default function TenantsPage() {
  const { me, loading } = useAdmin();
  const [rows, setRows] = React.useState<Tenant[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [name, setName] = React.useState("");
  const [slug, setSlug] = React.useState("");

  const load = React.useCallback(async () => {
    const token = getStoredToken();
    if (!token) return;
    setError(null);
    try {
      setRows(await listTenants(token));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, []);

  React.useEffect(() => {
    void load();
  }, [load]);

  if (!loading && me?.role !== "super_admin") {
    return (
      <p className="text-sm text-neutral-600">
        Only super administrators can manage tenants.
      </p>
    );
  }

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    const token = getStoredToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      await createTenant(token, {
        name,
        slug,
        status: "active",
        allowed_domains: [],
      });
      toast.success("Tenant created");
      setName("");
      setSlug("");
      await load();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Create failed";
      setError(msg);
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Tenants"
        description="Create and open tenant workspaces."
      />
      <ErrorAlert message={error} />
      <form
        onSubmit={onCreate}
        className="mb-8 grid max-w-lg gap-4 rounded-lg border border-neutral-200 bg-white p-4"
      >
        <div className="grid gap-2 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="slug">Slug</Label>
            <Input
              id="slug"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              placeholder="my-campus"
              required
            />
          </div>
        </div>
        <Button type="submit" disabled={busy} className="w-fit">
          {busy ? "Creating…" : "Create tenant"}
        </Button>
      </form>

      <div className="rounded-lg border border-neutral-200 bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Slug</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Open</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((t) => (
              <TableRow key={t.id}>
                <TableCell>{t.id}</TableCell>
                <TableCell>{t.name}</TableCell>
                <TableCell>{t.slug}</TableCell>
                <TableCell>
                  <Badge variant="secondary">{t.status}</Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Button asChild size="sm" variant="outline">
                    <a href={`/admin/t/${t.id}`}>Workspace</a>
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
