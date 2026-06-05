export type LLMProviderKind = "echo" | "claude_code" | "gemini" | "local";

export interface LLMProviderVM {
  kind: LLMProviderKind;
  label: string;
  description: string;
  defaultModel: string;
  requires: string[];
  needsNetwork: boolean;
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
