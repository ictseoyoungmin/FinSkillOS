import { ApiError, getJson } from "@/shared/api/client";
import type {
  AgentProvidersResponse,
  BrokerageSyncResponse,
  ChatMessageVM,
  ChatResponse,
  IngestProposalResponse,
  LLMProviderKind,
  TossHoldingsWarningsResponse,
  TossStocksResponse,
  TradeSyncResponse,
} from "./types";

const apiBase = () => import.meta.env.VITE_API_BASE_URL ?? "/api";

export async function fetchTossStocks(
  symbols: string[],
  signal?: AbortSignal,
): Promise<TossStocksResponse> {
  const q = encodeURIComponent(symbols.join(","));
  const response = await fetch(`${apiBase()}/agent/toss/stocks?symbols=${q}`, {
    credentials: "omit",
    headers: { Accept: "application/json" },
    signal,
  });
  if (!response.ok) {
    throw new ApiError(response.status, `${response.status} ${response.statusText}`);
  }
  return (await response.json()) as TossStocksResponse;
}

export async function fetchTossHoldingsWarnings(
  signal?: AbortSignal,
): Promise<TossHoldingsWarningsResponse> {
  const response = await fetch(`${apiBase()}/agent/toss/holdings-warnings`, {
    credentials: "omit",
    headers: { Accept: "application/json" },
    signal,
  });
  if (!response.ok) {
    throw new ApiError(response.status, `${response.status} ${response.statusText}`);
  }
  return (await response.json()) as TossHoldingsWarningsResponse;
}

export async function syncTossTrades(
  signal?: AbortSignal,
): Promise<TradeSyncResponse> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const response = await fetch(`${base}/agent/sync/trades/apply`, {
    method: "POST",
    credentials: "omit",
    headers: { Accept: "application/json" },
    signal,
  });
  if (!response.ok) {
    throw new ApiError(response.status, `${response.status} ${response.statusText}`);
  }
  return (await response.json()) as TradeSyncResponse;
}

export async function syncTossHoldings(
  signal?: AbortSignal,
): Promise<BrokerageSyncResponse> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const response = await fetch(`${base}/agent/sync/holdings`, {
    method: "POST",
    credentials: "omit",
    headers: { Accept: "application/json" },
    signal,
  });
  if (!response.ok) {
    throw new ApiError(response.status, `${response.status} ${response.statusText}`);
  }
  return (await response.json()) as BrokerageSyncResponse;
}

export async function sendAgentChat(
  messages: ChatMessageVM[],
  signal?: AbortSignal,
): Promise<ChatResponse> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const response = await fetch(`${base}/agent/chat`, {
    method: "POST",
    credentials: "omit",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
    signal,
  });
  if (!response.ok) {
    throw new ApiError(response.status, `${response.status} ${response.statusText}`);
  }
  return (await response.json()) as ChatResponse;
}

export async function ingestPortfolioPaste(
  text: string,
  signal?: AbortSignal,
): Promise<IngestProposalResponse> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const url = `${base}/agent/ingest`;
  const response = await fetch(url, {
    method: "POST",
    credentials: "omit",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ target: "portfolio", text }),
    signal,
  });
  if (!response.ok) {
    throw new ApiError(response.status, `${response.status} ${response.statusText}`);
  }
  return (await response.json()) as IngestProposalResponse;
}

export async function fetchAgentProviders(
  signal?: AbortSignal,
): Promise<AgentProvidersResponse> {
  return await getJson<AgentProvidersResponse>("/agent/providers", { signal });
}

export async function switchAgentProvider(
  kind: LLMProviderKind,
  signal?: AbortSignal,
): Promise<AgentProvidersResponse> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const url = `${base}/agent/providers`;
  const response = await fetch(url, {
    method: "PATCH",
    credentials: "omit",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ kind }),
    signal,
  });
  if (!response.ok) {
    let detail = "Could not switch LLM provider.";
    try {
      const payload = (await response.json()) as { detail?: string };
      if (typeof payload.detail === "string" && payload.detail) {
        detail = payload.detail;
      }
    } catch {
      detail = `${response.status} ${response.statusText}`;
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as AgentProvidersResponse;
}
