/** UI message model for the public scholar chat (Magic Pattern layout). */

import type { ChatCitation } from "@/types/public-chat";

export type ScholarMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: ChatCitation[];
  support?: string;
  isLoading?: boolean;
  isError?: boolean;
  /** When `isError`, optional detail from API */
  errorMessage?: string;
  /** Force “no indexed match” UX (optional; can be derived from support + citations) */
  noResult?: boolean;
};
