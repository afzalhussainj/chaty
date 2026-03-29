export type StatusBadgeVariant =
  | "default"
  | "secondary"
  | "outline"
  | "success"
  | "warning"
  | "danger";

export function jobStatusVariant(status: string): StatusBadgeVariant {
  switch (status) {
    case "succeeded":
    case "indexed":
      return "success";
    case "failed":
      return "danger";
    case "running":
    case "retrying":
    case "indexing":
    case "fetching":
      return "warning";
    case "queued":
    case "pending":
    case "discovered":
      return "secondary";
    default:
      return "outline";
  }
}
