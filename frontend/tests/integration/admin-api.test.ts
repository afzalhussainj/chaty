/**
 * Contract tests: ensure admin client calls the expected API paths (no UI).
 * Uses a stubbed global fetch — no backend required.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

import {
  createCrawlJob,
  createTenant,
  listSources,
  postIncremental,
  postLogin,
} from "@/lib/admin-api";

const API = "http://localhost:8000/api";

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("admin-api", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() => jsonResponse({})),
    );
  });

  it("postLogin targets /auth/login with JSON body", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        access_token: "t",
        token_type: "bearer",
        expires_in: 3600,
      }),
    );

    await postLogin("admin@example.com", "secret");

    expect(fetchMock).toHaveBeenCalledWith(
      `${API}/auth/login`,
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          email: "admin@example.com",
          password: "secret",
        }),
      }),
    );
  });

  it("createTenant POSTs /admin/tenants", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        id: 1,
        name: "T",
        slug: "t",
        status: "active",
        base_url: null,
        allowed_domains: [],
        default_crawl_config_id: null,
      }),
    );

    await createTenant("tok", { name: "T", slug: "t", status: "active" });

    expect(fetchMock).toHaveBeenCalledWith(
      `${API}/admin/tenants`,
      expect.objectContaining({
        method: "POST",
        headers: expect.any(Headers),
      }),
    );
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.headers).toBeDefined();
    const h = init.headers as Headers;
    expect(h.get("Authorization")).toBe("Bearer tok");
  });

  it("createCrawlJob POSTs crawl-jobs under tenant", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        id: 9,
        tenant_id: 5,
        status: "queued",
        job_type: "full_recrawl",
        crawl_config_id: 2,
        started_at: null,
        completed_at: null,
        error_message: null,
        stats: {},
      }),
    );

    await createCrawlJob("tok", 5, {
      job_type: "full_recrawl",
      crawl_config_id: 2,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      `${API}/admin/tenants/5/crawl-jobs`,
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("postIncremental hits incremental subpath", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        id: 1,
        tenant_id: 4,
        status: "queued",
        job_type: "incremental_url",
        crawl_config_id: 3,
        started_at: null,
        completed_at: null,
        error_message: null,
        stats: {},
      }),
    );

    await postIncremental("tok", 4, "refresh-page", {
      crawl_config_id: 3,
      url: "https://ex.edu/a",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      `${API}/admin/tenants/4/incremental/refresh-page`,
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("listSources builds query string for inspect filters", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(jsonResponse([]));

    await listSources("tok", 8, { status: "indexed", q: "tuition" });

    expect(fetchMock).toHaveBeenCalledWith(
      `${API}/admin/tenants/8/sources?status=indexed&q=tuition`,
      expect.objectContaining({
        headers: expect.any(Headers),
      }),
    );
  });
});
