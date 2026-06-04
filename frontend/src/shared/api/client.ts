/**
 * Tiny fetch-based JSON client. Avoids axios; React Query handles
 * caching / retries. The base URL defaults to `/api` so the Vite dev
 * proxy can route to the FastAPI container.
 */

const DEFAULT_BASE = "/api";

export type FetchOptions = RequestInit & { signal?: AbortSignal };

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export async function getJson<T>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const base = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE;
  const url = `${base}${path}`;
  const response = await fetch(url, {
    credentials: "omit",
    headers: { Accept: "application/json", ...(options.headers ?? {}) },
    ...options,
  });
  if (!response.ok) {
    throw new ApiError(
      response.status,
      `${response.status} ${response.statusText} for ${url}`,
    );
  }
  return (await response.json()) as T;
}

/**
 * Send a JSON body via a mutating method (POST / PUT / PATCH / DELETE).
 * Used by the descriptive portfolio editor (Slice 158); the API stays
 * read-only except for these idempotent holdings-management endpoints.
 */
export async function sendJson<T>(
  path: string,
  method: "POST" | "PUT" | "PATCH" | "DELETE",
  body?: unknown,
  options: FetchOptions = {},
): Promise<T> {
  const base = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE;
  const url = `${base}${path}`;
  const response = await fetch(url, {
    method,
    credentials: "omit",
    headers: {
      Accept: "application/json",
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(options.headers ?? {}),
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    ...options,
  });
  if (!response.ok) {
    let detail = "";
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload?.detail ? `: ${payload.detail}` : "";
    } catch {
      detail = "";
    }
    throw new ApiError(
      response.status,
      `${response.status} ${response.statusText} for ${url}${detail}`,
    );
  }
  return (await response.json()) as T;
}
