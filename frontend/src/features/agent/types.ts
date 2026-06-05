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
