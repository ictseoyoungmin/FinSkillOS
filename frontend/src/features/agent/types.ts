export type LLMProviderKind = "echo" | "claude_code" | "gemini" | "local";

export interface LLMProviderVM {
  kind: LLMProviderKind;
  label: string;
  description: string;
  defaultModel: string;
  requires: string[];
  needsNetwork: boolean;
  vision: boolean;
  ready: boolean;
  reason: string;
}

export interface AgentProvidersResponse {
  active: LLMProviderKind;
  providers: LLMProviderVM[];
  boundary: string;
}

export interface IngestRowVM {
  ticker: string;
  quantity: string;
  marketValue: string;
  averageCost: string | null;
  sector: string | null;
  theme: string | null;
  strategyType: string;
}

export interface IngestProposalResponse {
  target: "portfolio";
  rowCount: number;
  rows: IngestRowVM[];
  warnings: string[];
  normalizedCsv: string;
  applyEndpoint: string;
  boundary: string;
}

export interface ChatMessageVM {
  role: "user" | "assistant";
  content: string;
  images?: string[];
}

export interface WatchlistOpVM {
  add: string[];
  remove: string[];
  folder: string;
}

export interface ProposedActionVM {
  kind:
    | "portfolio_import"
    | "trades_import"
    | "watch_update"
    | "run_protocol"
    | "open_simulation";
  summary: string;
  normalizedCsv: string;
  rowCount: number;
  warnings: string[];
  applyEndpoint: string;
  watchlist?: WatchlistOpVM | null;
  protocol?: string | null;
  navPath?: string | null;
}

export interface BrokerageSyncResponse {
  available: boolean;
  source: string;
  rowCount: number;
  rows: IngestRowVM[];
  warnings: string[];
  normalizedCsv: string;
  note: string;
  applyEndpoint: string;
  boundary: string;
}

export interface WorkStep {
  type: "step";
  key: string;
  label: string;
  status: "running" | "done";
  elapsedMs: number;
  tool?: string;
}

export interface TossStock {
  symbol: string;
  name: string | null;
  englishName: string | null;
  market: string | null;
  currency: string | null;
  securityType: string | null;
  status: string | null;
  tradingSuspended: boolean;
  liquidationTrading: boolean;
}

export interface TossStocksResponse {
  available: boolean;
  stocks: TossStock[];
  note: string;
}

export interface TossHoldingWarning {
  symbol: string;
  name: string | null;
  severity: "INFO" | "WATCH" | "RISK";
  flags: string[];
}

export interface TossHoldingsWarningsResponse {
  available: boolean;
  warnings: TossHoldingWarning[];
  note: string;
}

export interface TradeSyncResponse {
  status: "APPLIED" | "SKIPPED" | "PENDING_TOSS" | "ERROR";
  added: number;
  skipped: number;
  note: string;
}

export interface ChatSimMarker {
  index: number;
  kind: "ENTER" | "EXIT";
}

export interface ChatSimPreview {
  ticker: string;
  strategyName: string;
  navPath: string;
  closes: number[];
  exposures: boolean[];
  markers: ChatSimMarker[];
  barCount: number;
  exposurePct: number;
  totalReturn: number | null;
  sharpe: number | null;
  maxDrawdown: number | null;
}

export interface ChatResponse {
  reply: string;
  provider: string;
  ready: boolean;
  proposedActions: ProposedActionVM[];
  proposedAction: ProposedActionVM | null;
  boundary: string;
  simulation?: ChatSimPreview | null;
}
