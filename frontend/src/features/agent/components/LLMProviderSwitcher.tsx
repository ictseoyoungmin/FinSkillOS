import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { OriginTag, Panel } from "@/shared/ui";
import { fetchAgentProviders, switchAgentProvider } from "../api";
import type { AgentProvidersResponse, LLMProviderKind } from "../types";
import "./llm-provider-switcher.css";

/**
 * Ops LLM provider switcher (v3 Phase 10 / Slice 188). Lists the provider
 * catalogue with config-derived readiness and switches the active narrator
 * backend. Provider switching changes only the backend — the descriptive-only
 * output boundary is enforced regardless.
 */
export function LLMProviderSwitcher() {
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["agent-providers"],
    queryFn: ({ signal }) => fetchAgentProviders(signal),
  });

  const mutation = useMutation({
    mutationFn: (kind: LLMProviderKind) => switchAgentProvider(kind),
    onSuccess: (next: AgentProvidersResponse) => {
      queryClient.setQueryData(["agent-providers"], next);
    },
  });

  return (
    <Panel
      title="LLM Provider"
      badge={data ? data.active : "—"}
      badgeTone="info"
      testId="llm-provider-switcher"
    >
      {isLoading ? (
        <p className="fso-llm-provider-note">Loading providers…</p>
      ) : isError || !data ? (
        <p className="fso-llm-provider-note">Provider catalogue unavailable.</p>
      ) : (
        <>
          <ul className="fso-llm-provider-list">
            {data.providers.map((provider) => {
              const active = provider.kind === data.active;
              return (
                <li
                  key={provider.kind}
                  className={`fso-llm-provider-row${
                    active ? " fso-llm-provider-row--active" : ""
                  }`}
                  data-testid={`llm-provider-${provider.kind}`}
                >
                  <div className="fso-llm-provider-head">
                    <span className="fso-llm-provider-label">
                      {provider.label}
                    </span>
                    <OriginTag
                      origin={provider.ready ? "live" : "empty"}
                      label={provider.ready ? "Ready" : "Not ready"}
                    />
                    {active ? (
                      <span className="fso-llm-provider-active-pill">Active</span>
                    ) : null}
                  </div>
                  <p className="fso-llm-provider-desc">{provider.description}</p>
                  <p className="fso-llm-provider-reason">{provider.reason}</p>
                  <button
                    type="button"
                    className="fso-llm-provider-select"
                    disabled={active || mutation.isPending}
                    onClick={() => mutation.mutate(provider.kind)}
                    data-testid={`llm-provider-select-${provider.kind}`}
                  >
                    {active ? "Selected" : "Use this provider"}
                  </button>
                </li>
              );
            })}
          </ul>
          <p className="fso-llm-provider-boundary">{data.boundary}</p>
          {mutation.isError ? (
            <p className="fso-llm-provider-note">
              Could not switch provider (DB write required).
            </p>
          ) : null}
        </>
      )}
    </Panel>
  );
}
