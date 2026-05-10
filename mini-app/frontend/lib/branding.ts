/**
 * Normalize tenant primary color for CSS (hex only; fallback if invalid).
 */
export function tenantPrimaryCss(color: string | null | undefined): string {
  if (!color || typeof color !== "string") return "#1e3a5f";
  const t = color.trim();
  if (/^#[0-9A-Fa-f]{6}$/.test(t)) return t;
  if (/^#[0-9A-Fa-f]{3}$/.test(t)) {
    return `#${t[1]}${t[1]}${t[2]}${t[2]}${t[3]}${t[3]}`;
  }
  return "#1e3a5f";
}

export function sessionStorageKey(slug: string): string {
  return `chaty_public_session_${slug}`;
}

export function messagesStorageKey(slug: string): string {
  return `chaty_public_messages_${slug}`;
}
