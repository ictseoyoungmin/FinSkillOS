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

export interface ProposedActionVM {
  kind: "portfolio_import";
  summary: string;
  normalizedCsv: string;
  rowCount: number;
  warnings: string[];
  applyEndpoint: string;
}

export interface ChatResponse {
  reply: string;
  provider: string;
  ready: boolean;
  proposedAction: ProposedActionVM | null;
  boundary: string;
}
