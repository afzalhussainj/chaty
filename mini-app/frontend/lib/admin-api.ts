import { apiFetch } from "@/lib/api";
import type {
  AdminMe,
  AuditLogEntry,
  ChatQueryResponse,
  CrawlConfig,
  CrawlJob,
  IndexJob,
  RetrievalDebugResponse,
  SourceSummary,
  Tenant,
  TokenResponse,
} from "@/types/admin";

export async function postLogin(
  email: string,
  password: string,
): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe(token: string): Promise<AdminMe> {
  return apiFetch<AdminMe>("/auth/me", { token });
}

export async function listTenants(token: string): Promise<Tenant[]> {
  return apiFetch<Tenant[]>("/admin/tenants", { token });
}

export async function createTenant(
  token: string,
  body: Record<string, unknown>,
): Promise<Tenant> {
  return apiFetch<Tenant>("/admin/tenants", {
    method: "POST",
    body: JSON.stringify(body),
    token,
  });
}

export async function getTenant(
  token: string,
  tenantId: number,
): Promise<Tenant> {
  return apiFetch<Tenant>(`/admin/tenants/${tenantId}`, { token });
}

export async function listCrawlConfigs(
  token: string,
  tenantId: number,
): Promise<CrawlConfig[]> {
  return apiFetch<CrawlConfig[]>(
    `/admin/tenants/${tenantId}/crawl-configs`,
    { token },
  );
}

export async function createCrawlConfig(
  token: string,
  tenantId: number,
  body: Record<string, unknown>,
): Promise<CrawlConfig> {
  return apiFetch<CrawlConfig>(
    `/admin/tenants/${tenantId}/crawl-configs`,
    { method: "POST", body: JSON.stringify(body), token },
  );
}

export async function updateCrawlConfig(
  token: string,
  tenantId: number,
  configId: number,
  body: Record<string, unknown>,
): Promise<CrawlConfig> {
  return apiFetch<CrawlConfig>(
    `/admin/tenants/${tenantId}/crawl-configs/${configId}`,
    { method: "PATCH", body: JSON.stringify(body), token },
  );
}

export async function deleteCrawlConfig(
  token: string,
  tenantId: number,
  configId: number,
): Promise<void> {
  await apiFetch<unknown>(
    `/admin/tenants/${tenantId}/crawl-configs/${configId}`,
    { method: "DELETE", token },
  );
}

export async function createCrawlJob(
  token: string,
  tenantId: number,
  body: Record<string, unknown>,
): Promise<CrawlJob> {
  return apiFetch<CrawlJob>(`/admin/tenants/${tenantId}/crawl-jobs`, {
    method: "POST",
    body: JSON.stringify(body),
    token,
  });
}

export async function listCrawlJobs(
  token: string,
  tenantId: number,
): Promise<CrawlJob[]> {
  return apiFetch<CrawlJob[]>(
    `/admin/tenants/${tenantId}/crawl-jobs?limit=100`,
    { token },
  );
}

export async function getCrawlJob(
  token: string,
  tenantId: number,
  jobId: number,
): Promise<CrawlJob> {
  return apiFetch<CrawlJob>(
    `/admin/tenants/${tenantId}/crawl-jobs/${jobId}`,
    { token },
  );
}

export async function listIndexJobs(
  token: string,
  tenantId: number,
): Promise<IndexJob[]> {
  return apiFetch<IndexJob[]>(
    `/admin/tenants/${tenantId}/index-jobs?limit=100`,
    { token },
  );
}

export async function postIncremental(
  token: string,
  tenantId: number,
  path:
    | "refresh-page"
    | "refresh-pdf"
    | "add-source"
    | "sync-changed"
    | "full-recrawl",
  body: Record<string, unknown>,
): Promise<CrawlJob> {
  return apiFetch<CrawlJob>(
    `/admin/tenants/${tenantId}/incremental/${path}`,
    { method: "POST", body: JSON.stringify(body), token },
  );
}

export async function listSources(
  token: string,
  tenantId: number,
  params: Record<string, string | undefined>,
): Promise<SourceSummary[]> {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") q.set(k, v);
  }
  const qs = q.toString();
  return apiFetch<SourceSummary[]>(
    `/admin/tenants/${tenantId}/sources${qs ? `?${qs}` : ""}`,
    { token },
  );
}

export interface SourceExtractionInspect {
  source: SourceSummary;
  document: {
    id: number;
    source_id: number;
    source_snapshot_id: number;
    title: string | null;
    language: string | null;
    page_count: number | null;
    extraction_hash: string | null;
    indexed_extraction_hash: string | null;
    indexed_at: string | null;
    full_text_preview: string | null;
    extraction_metadata: Record<string, unknown> | null;
  } | null;
  chunks: Array<{
    id: number;
    chunk_index: number;
    heading: string | null;
    page_number: number | null;
    content: string;
  }>;
  chunk_total: number;
  chunk_limit: number;
  chunk_offset: number;
}

export async function getSourceExtraction(
  token: string,
  tenantId: number,
  sourceId: number,
  chunkOffset = 0,
): Promise<SourceExtractionInspect> {
  return apiFetch<SourceExtractionInspect>(
    `/admin/tenants/${tenantId}/sources/${sourceId}/extraction?chunk_limit=100&chunk_offset=${chunkOffset}`,
    { token },
  );
}

export async function postRetryExtraction(
  token: string,
  tenantId: number,
  sourceId: number,
): Promise<{ ok: boolean; source_type: string; extracted_document_id: number }> {
  return apiFetch(
    `/admin/tenants/${tenantId}/sources/${sourceId}/retry-extraction`,
    { method: "POST", token },
  );
}

export async function postRetrievalDebug(
  token: string,
  tenantId: number,
  body: Record<string, unknown>,
): Promise<RetrievalDebugResponse> {
  return apiFetch<RetrievalDebugResponse>(
    `/admin/tenants/${tenantId}/retrieval/debug`,
    { method: "POST", body: JSON.stringify(body), token },
  );
}

export async function postChatQuery(
  token: string,
  tenantId: number,
  body: Record<string, unknown>,
): Promise<ChatQueryResponse> {
  return apiFetch<ChatQueryResponse>(
    `/tenants/${tenantId}/chat/query`,
    { method: "POST", body: JSON.stringify(body), token },
  );
}

export async function listTenantAudit(
  token: string,
  tenantId: number,
): Promise<AuditLogEntry[]> {
  return apiFetch<AuditLogEntry[]>(
    `/admin/tenants/${tenantId}/audit-logs?limit=100`,
    { token },
  );
}

export async function listGlobalAudit(
  token: string,
  tenantId?: number,
): Promise<AuditLogEntry[]> {
  const q = new URLSearchParams({ limit: "100" });
  if (tenantId !== undefined) q.set("tenant_id", String(tenantId));
  return apiFetch<AuditLogEntry[]>(`/admin/audit-logs?${q}`, { token });
}
