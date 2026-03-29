/** Public chat (tenant slug) — mirrors backend chat responses. */

export interface PublicTenantInfo {
  id: number;
  name: string;
  slug: string;
  branding: {
    logo_url: string | null;
    primary_color: string | null;
    app_title: string | null;
  } | null;
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

export interface ChatTurn {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: ChatCitation[];
  support?: string;
  error?: boolean;
}
