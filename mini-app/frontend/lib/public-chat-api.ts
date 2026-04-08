import { apiFetch } from "@/lib/api";
import type { ChatQueryResponse, PublicTenantInfo } from "@/types/public-chat";

export async function fetchPublicTenant(slug: string): Promise<PublicTenantInfo> {
  return apiFetch<PublicTenantInfo>(
    `/public/tenants/${encodeURIComponent(slug)}`,
  );
}

export async function postPublicChatQuery(
  slug: string,
  body: {
    message: string;
    session_id?: number | null;
    answer_mode?: "concise" | "detailed";
    stream?: boolean;
  },
): Promise<ChatQueryResponse> {
  return apiFetch<ChatQueryResponse>(
    `/public/tenants/${encodeURIComponent(slug)}/chat/query`,
    {
      method: "POST",
      body: JSON.stringify({
        message: body.message,
        session_id: body.session_id ?? undefined,
        answer_mode: body.answer_mode ?? "concise",
        stream: false,
      }),
    },
  );
}
