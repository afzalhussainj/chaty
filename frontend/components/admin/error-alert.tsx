import { ApiError } from "@/lib/api";

export function ErrorAlert({
  message,
  error,
  requestId,
  code,
}: {
  message?: string | null;
  error?: unknown;
  requestId?: string | null;
  code?: string | null;
}) {
  let msg = message ?? null;
  let rid = requestId;
  let c = code;
  if (error instanceof ApiError) {
    msg = msg ?? error.message;
    rid = rid ?? error.requestId;
    c = c ?? error.errorCode;
  } else if (error instanceof Error && !msg) {
    msg = error.message;
  }
  if (!msg) return null;
  return (
    <div
      className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900"
      role="alert"
    >
      <p>{msg}</p>
      {(c || rid) && (
        <p className="mt-2 font-mono text-xs text-red-800/90">
          {c ? `${c}` : null}
          {c && rid ? " · " : null}
          {rid ? `request ${rid}` : null}
        </p>
      )}
    </div>
  );
}
