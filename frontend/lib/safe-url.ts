/** Allow only http(s) URLs for user-controlled hrefs (citations, etc.). */

export function isSafeHttpUrl(href: string | null | undefined): boolean {
  if (!href || typeof href !== "string") return false;
  try {
    const u = new URL(href);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}
