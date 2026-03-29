/**
 * Shared helpers (e.g. `cn` for classnames once shadcn/ui is added).
 */
export function cn(...classes: Array<string | undefined | false>): string {
  return classes.filter(Boolean).join(" ");
}
