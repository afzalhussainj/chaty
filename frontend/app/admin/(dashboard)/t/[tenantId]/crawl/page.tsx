"use client";

import { useParams } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { ErrorAlert } from "@/components/admin/error-alert";
import { PageHeader } from "@/components/admin/page-header";
import {
  createCrawlJob,
  listCrawlConfigs,
  postIncremental,
} from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import type { CrawlConfig } from "@/types/admin";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

function ConfigSelect({
  value,
  onChange,
  configs,
}: {
  value: string;
  onChange: (v: string) => void;
  configs: CrawlConfig[];
}) {
  return (
    <select
      className="flex h-9 w-full rounded-md border border-neutral-200 bg-white px-3 py-1 text-sm shadow-sm"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      {configs.map((c) => (
        <option key={c.id} value={String(c.id)}>
          {c.id} — {c.name}
        </option>
      ))}
    </select>
  );
}

export default function CrawlActionsPage() {
  const params = useParams();
  const tenantId = Number(params.tenantId);
  const [configs, setConfigs] = React.useState<CrawlConfig[]>([]);
  const [configId, setConfigId] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [url, setUrl] = React.useState("");
  const [useSitemap, setUseSitemap] = React.useState(false);
  const [busy, setBusy] = React.useState<string | null>(null);

  React.useEffect(() => {
    const token = getStoredToken();
    if (!token) return;
    void (async () => {
      try {
        const list = await listCrawlConfigs(token, tenantId);
        setConfigs(list);
        if (list[0]) setConfigId(String(list[0].id));
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load configs");
      }
    })();
  }, [tenantId]);

  const cid = Number(configId) || 0;

  async function run(
    label: string,
    fn: (token: string) => Promise<unknown>,
  ) {
    const token = getStoredToken();
    if (!token || !cid) {
      toast.error("Select a crawl configuration.");
      return;
    }
    setBusy(label);
    setError(null);
    try {
      await fn(token);
      toast.success(`${label} queued`);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Request failed";
      setError(msg);
      toast.error(msg);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="Crawl actions"
        description="Queue jobs using a crawl configuration. Operations require tenant admin permissions where applicable."
      />
      <ErrorAlert message={error} />

      <div className="mb-6 max-w-md space-y-2">
        <Label>Crawl configuration</Label>
        <ConfigSelect
          configs={configs}
          value={configId}
          onChange={setConfigId}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Full site recrawl</CardTitle>
            <CardDescription>BFS from the configured base URL.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={useSitemap}
                onChange={(e) => setUseSitemap(e.target.checked)}
              />
              Include sitemap.xml (best-effort)
            </label>
            <Button
              type="button"
              disabled={!!busy || !cid}
              onClick={() =>
                void run("Full recrawl", (t) =>
                  postIncremental(t, tenantId, "full-recrawl", {
                    crawl_config_id: cid,
                    use_sitemap: useSitemap,
                  }),
                )
              }
            >
              {busy === "Full recrawl" ? "Queueing…" : "Start full recrawl"}
            </Button>
            <p className="text-xs text-neutral-500">
              Alternative: generic crawl job API (same worker).
            </p>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={!!busy || !cid}
              onClick={() =>
                void run("Full crawl job", (t) =>
                  createCrawlJob(t, tenantId, {
                    crawl_config_id: cid,
                    job_type: "full_crawl",
                    dry_run: false,
                    use_sitemap: useSitemap,
                  }),
                )
              }
            >
              Queue full_crawl job
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Sync changed sources</CardTitle>
            <CardDescription>Re-extract active sources; index when content changes.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              type="button"
              disabled={!!busy || !cid}
              onClick={() =>
                void run("Sync changed", (t) =>
                  postIncremental(t, tenantId, "sync-changed", {
                    crawl_config_id: cid,
                  }),
                )
              }
            >
              {busy === "Sync changed" ? "Queueing…" : "Run sync"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Single HTML page</CardTitle>
            <CardDescription>Refresh one page by absolute URL.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="url1">URL</Label>
              <Input
                id="url1"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://"
              />
            </div>
            <Button
              type="button"
              disabled={!!busy || !cid || !url}
              onClick={() =>
                void run("Refresh page", (t) =>
                  postIncremental(t, tenantId, "refresh-page", {
                    crawl_config_id: cid,
                    url,
                  }),
                )
              }
            >
              {busy === "Refresh page" ? "Queueing…" : "Crawl page"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Single PDF</CardTitle>
            <CardDescription>Re-fetch a PDF by URL.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="url2">PDF URL</Label>
              <Input
                id="url2"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://"
              />
            </div>
            <Button
              type="button"
              disabled={!!busy || !cid || !url}
              onClick={() =>
                void run("Refresh PDF", (t) =>
                  postIncremental(t, tenantId, "refresh-pdf", {
                    crawl_config_id: cid,
                    url,
                  }),
                )
              }
            >
              {busy === "Refresh PDF" ? "Queueing…" : "Crawl PDF"}
            </Button>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Add manual source URL</CardTitle>
            <CardDescription>
              Register a URL under the crawl config without a full-site crawl.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap items-end gap-3">
            <div className="min-w-[240px] flex-1 space-y-2">
              <Label htmlFor="url3">URL</Label>
              <Input
                id="url3"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
            <Button
              type="button"
              disabled={!!busy || !cid || !url}
              onClick={() =>
                void run("Add source", (t) =>
                  postIncremental(t, tenantId, "add-source", {
                    crawl_config_id: cid,
                    url,
                  }),
                )
              }
            >
              {busy === "Add source" ? "Queueing…" : "Add source"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
