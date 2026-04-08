const API_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api")
    : (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api");

export const AUTH_TOKEN_KEY = "chaty_admin_token";

export class ApiError extends Error {
  readonly requestId?: string;
  readonly errorCode?: string;

  constructor(
    public status: number,
    message: string,
    public body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
    if (body && typeof body === "object" && "error" in body) {
      const inner = (body as { error?: { request_id?: string; code?: string } }).error;
      if (inner?.request_id) this.requestId = inner.request_id;
      if (inner?.code) this.errorCode = inner.code;
    }
  }
}

function envelopeMessage(data: unknown): string | null {
  if (data && typeof data === "object" && "error" in data) {
    const inner = (data as { error?: { message?: string } }).error;
    if (inner && typeof inner.message === "string") {
      return inner.message;
    }
  }
  return null;
}

function detailMessage(data: unknown, fallback: string): string {
  const env = envelopeMessage(data);
  if (env) return env;
  if (data && typeof data === "object" && "detail" in data) {
    const d = (data as { detail: unknown }).detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) return JSON.stringify(d);
  }
  return fallback;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { token?: string | null } = {},
): Promise<T> {
  const { token, ...init } = options;
  const headers = new Headers(init.headers);
  if (init.body !== undefined && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const res = await fetch(url, { ...init, headers });
  const text = await res.text();
  let data: unknown;
  if (text) {
    try {
      data = JSON.parse(text) as unknown;
    } catch {
      data = text;
    }
  }
  if (!res.ok) {
    throw new ApiError(
      res.status,
      detailMessage(data, res.statusText),
      data,
    );
  }
  return data as T;
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setStoredToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token === null) localStorage.removeItem(AUTH_TOKEN_KEY);
  else localStorage.setItem(AUTH_TOKEN_KEY, token);
}
