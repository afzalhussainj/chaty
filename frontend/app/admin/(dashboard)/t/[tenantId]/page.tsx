"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import * as React from "react";

import { PageHeader } from "@/components/admin/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getTenant } from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import type { Tenant } from "@/types/admin";

export default function TenantOverviewPage() {
  const params = useParams();
  const tenantId = Number(params.tenantId);
  const [tenant, setTenant] = React.useState<Tenant | null>(null);
  const [err, setErr] = React.useState<string | null>(null);

  React.useEffect(() => {
    const token = getStoredToken();
    if (!token) return;
    void (async () => {
      try {
        setTenant(await getTenant(token, tenantId));
      } catch (e: unknown) {
        setErr(e instanceof Error ? e.message : "Failed to load tenant");
      }
    })();
  }, [tenantId]);

  const base = `/admin/t/${tenantId}`;

  return (
    <div>
      <PageHeader
        title={tenant?.name ?? `Tenant ${tenantId}`}
        description={tenant?.slug ? `Slug: ${tenant.slug}` : "Workspace overview"}
      />
      {err ? (
        <p className="mb-4 text-sm text-red-700">{err}</p>
      ) : null}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Crawl</CardTitle>
            <CardDescription>Configs and crawl actions</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            <Button asChild variant="secondary" size="sm">
              <Link href={`${base}/crawl-configs`}>Crawl configs</Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href={`${base}/crawl`}>Run crawls</Link>
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Content</CardTitle>
            <CardDescription>Sources and extraction</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            <Button asChild variant="secondary" size="sm">
              <Link href={`${base}/sources`}>Sources</Link>
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Quality</CardTitle>
            <CardDescription>Retrieval and chat tests</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            <Button asChild variant="secondary" size="sm">
              <Link href={`${base}/retrieval`}>Retrieval test</Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href={`${base}/chat`}>Chat test</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
