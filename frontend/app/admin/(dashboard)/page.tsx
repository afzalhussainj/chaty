"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";

import { PageHeader } from "@/components/admin/page-header";
import { useAdmin } from "@/components/admin/admin-context";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { listTenants } from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import type { Tenant } from "@/types/admin";

export default function AdminHomePage() {
  const { me, loading } = useAdmin();
  const router = useRouter();
  const [tenants, setTenants] = React.useState<Tenant[]>([]);
  const [err, setErr] = React.useState<string | null>(null);

  React.useEffect(() => {
    const token = getStoredToken();
    if (!token || !me || me.role !== "super_admin") return;
    void (async () => {
      try {
        setTenants(await listTenants(token));
      } catch (e: unknown) {
        setErr(e instanceof Error ? e.message : "Failed to load tenants");
      }
    })();
  }, [me]);

  React.useEffect(() => {
    if (loading || !me) return;
    if (me.role !== "super_admin" && me.tenant_id) {
      router.replace(`/admin/t/${me.tenant_id}`);
    }
  }, [me, loading, router]);

  if (!loading && me?.role !== "super_admin") {
    return (
      <div className="text-sm text-neutral-500">Redirecting to workspace…</div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Choose a tenant workspace or manage platform settings."
      />
      {err ? (
        <p className="mb-4 text-sm text-red-700" role="alert">
          {err}
        </p>
      ) : null}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Tenants</CardTitle>
            <CardDescription>Open crawl, sources, and jobs for a tenant.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            <Button asChild variant="secondary">
              <Link href="/admin/tenants">Manage tenants</Link>
            </Button>
            <div className="mt-2 space-y-1">
              {tenants.slice(0, 8).map((t) => (
                <Button key={t.id} asChild variant="outline" className="w-full justify-start">
                  <Link href={`/admin/t/${t.id}`}>{t.name}</Link>
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Audit</CardTitle>
            <CardDescription>Platform-wide privileged action log (super admin).</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="secondary">
              <Link href="/admin/audit">View global audit log</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
