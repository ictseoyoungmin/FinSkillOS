import { ApiError, getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type {
  CollectionControlData,
  CollectionFlag,
  CollectionFlagPatch,
} from "./types";

const BASE = apiEndpoints.collectionControl;

function apiBase(): string {
  return import.meta.env.VITE_API_BASE_URL ?? "/api";
}

/** Read the full collection-control snapshot (folders + flags + totals). */
export async function fetchCollectionControl(
  signal?: AbortSignal,
): Promise<CollectionControlData> {
  return await getJson<CollectionControlData>(BASE, { signal });
}

async function mutate<TBody>(
  path: string,
  method: "POST" | "PATCH" | "DELETE",
  body?: TBody,
): Promise<CollectionControlData> {
  const url = `${apiBase()}${path}`;
  const response = await fetch(url, {
    method,
    credentials: "omit",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (typeof payload.detail === "string" && payload.detail) {
        detail = payload.detail;
      }
    } catch {
      /* keep status text */
    }
    throw new ApiError(response.status, `${detail} for ${url}`);
  }
  return (await response.json()) as CollectionControlData;
}

export function patchFolderFlags(
  folderId: string,
  patch: CollectionFlagPatch,
): Promise<CollectionControlData> {
  return mutate(`${BASE}/folders/${folderId}`, "PATCH", patch);
}

export function createFolder(
  name: string,
  description?: string,
): Promise<CollectionControlData> {
  return mutate(`${BASE}/folders`, "POST", { name, description });
}

export function deleteFolder(folderId: string): Promise<CollectionControlData> {
  return mutate(`${BASE}/folders/${folderId}`, "DELETE");
}

export function addFolderSymbol(
  folderId: string,
  ticker: string,
): Promise<CollectionControlData> {
  return mutate(`${BASE}/folders/${folderId}/symbols`, "POST", { ticker });
}

export function removeFolderSymbol(
  folderId: string,
  ticker: string,
): Promise<CollectionControlData> {
  return mutate(
    `${BASE}/folders/${folderId}/symbols/${encodeURIComponent(ticker)}`,
    "DELETE",
  );
}

export function globalToggle(
  flag: CollectionFlag,
  value: boolean,
): Promise<CollectionControlData> {
  return mutate(`${BASE}/global-toggle`, "POST", { flag, value });
}
