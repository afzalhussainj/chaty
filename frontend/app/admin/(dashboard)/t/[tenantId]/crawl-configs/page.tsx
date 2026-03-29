"use client";

import { useParams } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { ErrorAlert } from "@/components/admin/error-alert";
import { PageHeader } from "@/components/admin/page-header";
import {
  createCrawlConfig,
  deleteCrawlConfig,
  listCrawlConfigs,
} from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import type { CrawlConfig } from "@/types/admin";
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

export default function CrawlConfigsPage() {
  const params = useParams();
  const tenantId = Number(params.tenantId);
  const [rows, setRows] = React.useState<CrawlConfig[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [name, setName] = React.useState("");
  const [baseUrl, setBaseUrl] = React.useState("https://example.edu");

  const load = React.useCallback(async () => {
    const token = getStoredToken();
    if (!token) return;
    setError(null);
    try {
      setRows(await listCrawlConfigs(token, tenantId));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, [tenantId]);

  React.useEffect(() => {
    void load();
  }, [load]);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    const token = getStoredToken();
    if (!token) return;
    setBusy(true);
    try {
      await createCrawlConfig(token, tenantId, {
        name,
        base_url: baseUrl,
        is_active: true,
        respect_robots_txt: true,
        allow_pdf_crawling: true,
        allow_js_rendering: false,
        crawl_frequency: "manual",
        allowed_hosts: [],
        include_path_rules: [],
        exclude_path_rules: [],
      });
      toast.success("Crawl config created");
      setName("");
      await load();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Create failed";
      setError(msg);
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id: number) {
    if (!window.confirm("Delete this crawl configuration?")) return;
    const token = getStoredToken();
    if (!token) return;
    try {
      await deleteCrawlConfig(token, tenantId, id);
      toast.success("Deleted");
      await load();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Delete failed");
    }
  }

  return (
    <div>
      <PageHeader
        title="Crawl configurations"
        description="Each config defines scope and policy for crawls."
      />
      <ErrorAlert message={error} />
      <form
        onSubmit={onCreate}
        className="mb-8 grid max-w-2xl gap-4 rounded-lg border border-neutral-200 bg-white p-4"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="cname">Name</Label>
            <Input
              id="cname"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="base">Base URL</Label>
            <Input
              id="base"
              type="url"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              required
            />
          </div>
        </div>
        <Button type="submit" disabled={busy} className="w-fit">
          {busy ? "Saving…" : "Add configuration"}
        </Button>
      </form>

      <div className="rounded-lg border border-neutral-200 bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Base URL</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((c) => (
              <TableRow key={c.id}>
                <TableCell>{c.id}</TableCell>
                <TableCell>{c.name}</TableCell>
                <TableCell className="max-w-xs truncate text-xs">{c.base_url}</TableCell>
                <TableCell className="text-right">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => void onDelete(c.id)}
                  >
                    Delete
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
