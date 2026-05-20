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
