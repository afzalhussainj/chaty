/** Mirrors backend Pydantic models (subset for admin UI). */

export type AdminRole = "super_admin" | "tenant_admin" | "tenant_viewer";

export interface AdminMe {
  id: number;
  email: string;
  full_name: string | null;
  role: AdminRole;
  tenant_id: number | null;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface Tenant {
  id: number;
  name: string;
  slug: string;
  status: string;
  base_url: string | null;
  allowed_domains: string[];
  default_crawl_config_id: number | null;
}

export interface CrawlConfig {
  id: number;
  tenant_id: number;
  name: string;
  base_url: string;
  is_active: boolean;
  max_depth: number | null;
  max_pages: number | null;
  respect_robots_txt: boolean;
  user_agent: string | null;
  allow_pdf_crawling: boolean;
  allow_js_rendering: boolean;
  crawl_frequency: string;
  allowed_hosts: string[];
  include_path_rules: string[];
  exclude_path_rules: string[];
  extras: Record<string, unknown> | null;
}

export interface CrawlJob {
  id: number;
  tenant_id: number;
  crawl_config_id: number | null;
  job_type: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  stats: Record<string, unknown> | null;
  workflow?: string | null;
}

export interface IndexJob {
  id: number;
  tenant_id: number;
  source_id: number | null;
  extracted_document_id: number | null;
  job_type: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  stats: Record<string, unknown> | null;
}

export interface SourceSummary {
  id: number;
  tenant_id: number;
  crawl_config_id: number | null;
  url: string;
  canonical_url: string;
  title: string | null;
  source_type: string;
  status: string;
  is_active: boolean;
  content_hash: string | null;
  last_crawled_at: string | null;
  last_indexed_at: string | null;
}

export interface AuditLogEntry {
  id: number;
  tenant_id: number | null;
  admin_user_id: number | null;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface RetrievedChunk {
  chunk_id: number;
  score: number;
  vector_score_norm: number;
  fts_score_norm: number;
  content: string;
  source_id: number;
  source_type: string;
  extracted_document_id: number;
  title: string | null;
  heading: string | null;
  page_number: number | null;
  source_url: string | null;
  content_hash: string;
  indexed_at: string | null;
}

export interface RetrievalDebugResponse {
  query_normalized: string;
  vector_candidates: number;
  fts_candidates: number;
  weight_vector: number;
  weight_fts: number;
  chunks: RetrievedChunk[];
}

export interface ChatCitation {
  chunk_id: number;
  source_id: number;
  title: string | null;
  url: string | null;
  source_type: string;
  page_number: number | null;
  score: number;
}

export interface ChatQueryResponse {
  answer: string;
  citations: ChatCitation[];
  support: string;
  session_id: number;
  retrieval: Record<string, unknown>;
}
