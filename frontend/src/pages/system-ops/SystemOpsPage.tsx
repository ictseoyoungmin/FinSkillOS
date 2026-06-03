import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchSystemOps,
  fetchSystemStatus,
  fetchRuntimeSettings,
  runSystemOpsProtocol,
  updateRuntimeSettings,
  resetRuntimeSettings as resetRuntimeOverridesApi,
  setWorkerLiveMode,
  retryWorkerJob,
} from "@/features/system-ops/api";
import { CollectionControlPanel } from "@/features/collection-control/components/CollectionControlPanel";
import { DataInvariantPanel } from "@/features/system-ops/components/DataInvariantPanel";
import { DataProvenancePanel } from "@/features/system-ops/components/DataProvenancePanel";
import { DataRepairPanel } from "@/features/system-ops/components/DataRepairPanel";
import { FeedCoveragePanel } from "@/features/system-ops/components/FeedCoveragePanel";
import { DataSourceStrip } from "@/features/system-ops/components/DataSourceStrip";
import { ProtocolCardItem } from "@/features/system-ops/components/ProtocolCardItem";
import { deriveProtocolEvidence } from "@/features/system-ops/detailEvidence";
import type {
  DataCompleteness,
  RuntimeSettingChange,
  SystemOpsRuntimeSettingsPayload,
  SystemStatusData,
  SystemStatusSource,
  WorkerCadenceStatus,
  WorkerCycleRecord,
  WorkerStatusSummary,
} from "@/features/system-ops/types";
import { systemOpsFixture } from "@/mocks/fixtures/systemOps.fixture";
import {
  ConflictsPanel,
  DriversPanel,
  EmptyState,
  InterpretationPanel,
  JudgmentHeader,
  Panel,
  SafetyCaption,
  SectionHeader,
  StatusPill,
  WatchpointsPanel,
} from "@/shared/ui";
import "./system-ops.css";

type RuntimeSettingKind = "text" | "number" | "boolean" | "select";

interface RuntimeSettingField {
  key: string;
  label: string;
  section: string;
  type: RuntimeSettingKind;
  hint: string;
  placeholder?: string;
  options?: string[];
  /** Minimum for number inputs (clamped server-side too). */
  min?: number;
}

const MARKET_ADAPTER_KEY = "FINSKILLOS_MARKET_REFRESH_ADAPTER";

const RUNTIME_SETTING_FIELDS: RuntimeSettingField[] = [
  {
    key: "FINSKILLOS_WORKER_INTERVAL_SECONDS",
    label: "Worker interval (seconds)",
    section: "Worker",
    type: "number",
    hint: "How often automatic refresh-all should be enqueued.",
    placeholder: "86400",
  },
  {
    key: "FINSKILLOS_WORKER_POLL_SECONDS",
    label: "Worker poll interval (seconds)",
    section: "Worker",
    type: "number",
    hint: "Queue-drain polling frequency used by the worker process.",
    placeholder: "5",
  },
  {
    key: "FINSKILLOS_WORKER_STALE_GRACE_SECONDS",
    label: "Worker stale grace (seconds)",
    section: "Worker",
    type: "number",
    hint: "Grace period added after expected cadence before stale is flagged.",
    placeholder: "43200",
  },
  {
    key: "FINSKILLOS_WORKER_RUN_ON_START",
    label: "Run on start",
    section: "Worker",
    type: "boolean",
    hint: "Queue an initial full refresh when the worker starts.",
  },
  {
    key: "FINSKILLOS_WORKER_MARKET_ENABLED",
    label: "Market refresh enabled",
    section: "Worker",
    type: "boolean",
    hint: "Allow market-bar refresh during worker jobs.",
  },
  {
    key: "FINSKILLOS_WORKER_NEWS_ENABLED",
    label: "News refresh enabled",
    section: "Worker",
    type: "boolean",
    hint: "Allow news metadata refresh during worker jobs.",
  },
  {
    key: "FINSKILLOS_WORKER_INDICATOR_ENABLED",
    label: "Indicator refresh enabled",
    section: "Worker",
    type: "boolean",
    hint: "Allow descriptive indicator computation during worker jobs.",
  },
  {
    key: "FINSKILLOS_WORKER_REGIME_ENABLED",
    label: "Regime recompute enabled",
    section: "Worker",
    type: "boolean",
    hint: "Recompute the market regime after indicators so it stays fresh.",
  },
  {
    key: "FINSKILLOS_WORKER_PERSIST_INDICATOR_HISTORY",
    label: "Keep indicator snapshots",
    section: "Worker",
    type: "boolean",
    hint: "Persist historical indicator snapshots (off to only keep latest).",
  },
  {
    key: MARKET_ADAPTER_KEY,
    label: "Market adapter",
    section: "Market",
    type: "select",
    options: ["yahoo", "mock"],
    hint: "yahoo = real data (production). mock = offline synthetic data.",
  },
  // Market/indicator ticker universes are no longer hand-typed here — they are
  // managed in the Collection Control tab (folder-driven, Slice W-4).
  {
    key: "FINSKILLOS_MARKET_REFRESH_TIMEFRAME",
    label: "Market timeframe",
    section: "Market",
    type: "text",
    hint: "Market timeframe passed to bar refresh and indicator compute.",
    placeholder: "1d",
  },
  {
    key: "FINSKILLOS_REFRESH_FOLDER_NAMES",
    label: "Refresh folders",
    section: "Market",
    type: "text",
    hint: "Optional folder names (comma-separated) for scoped refresh.",
    placeholder: "Growth,Value",
  },
  {
    key: "FINSKILLOS_NEWS_REFRESH_ADAPTER",
    label: "News adapter",
    section: "News",
    type: "text",
    hint: "Currently supports rss for production-ready policy.",
    placeholder: "rss",
  },
  {
    key: "FINSKILLOS_NEWS_RSS_FEEDS",
    label: "News RSS feeds",
    section: "News",
    type: "text",
    hint: "Optional explicit RSS feed URLs (comma-separated).",
    placeholder: "https://news.example/rss",
  },
  {
    key: "FINSKILLOS_NEWS_RSS_TICKERS",
    label: "News ticker symbols",
    section: "News",
    type: "text",
    hint: "Fallback ticker filters when explicit feeds are not provided.",
    placeholder: "AAPL,MSFT,NVDA,TSLA",
  },
  {
    key: "FINSKILLOS_NEWS_RSS_SOURCE",
    label: "News RSS source",
    section: "News",
    type: "text",
    hint: "Optional custom source for request metadata.",
    placeholder: "",
  },
  {
    key: "FINSKILLOS_NEWS_RSS_LANGUAGE",
    label: "News RSS language",
    section: "News",
    type: "text",
    hint: "Language tag forwarded to generated RSS requests.",
    placeholder: "en-US",
  },
];

const BOOL_TRUE_VALUES = new Set(["1", "true", "yes", "on", "enabled", "y"]);

function runtimeInputBooleanValue(raw: string | undefined): string {
  if (!raw) {
    return "0";
  }
  return BOOL_TRUE_VALUES.has(raw.trim().toLowerCase()) ? "1" : "0";
}

function toBooleanPatchValue(raw: string): boolean {
  return raw === "1";
}

function buildRuntimeDraftSource(values: Record<string, string>): Record<string, string> {
  const output: Record<string, string> = {};
  for (const field of RUNTIME_SETTING_FIELDS) {
    const sourceValue = values[field.key] ?? "";
    output[field.key] =
      field.type === "boolean"
        ? runtimeInputBooleanValue(sourceValue)
        : sourceValue;
  }
  return output;
}

function buildRuntimePatchPayload(
  draft: Record<string, string>,
  baseline: Record<string, string>,
): SystemOpsRuntimeSettingsPayload["values"] {
  const payload: SystemOpsRuntimeSettingsPayload["values"] = {};

  for (const field of RUNTIME_SETTING_FIELDS) {
    const nextRaw = (draft[field.key] ?? "").trim();
    const current = (baseline[field.key] ?? "").trim();
    const currentInput =
      field.type === "boolean" ? runtimeInputBooleanValue(current) : current;

    if (nextRaw === currentInput) {
      continue;
    }

    if (field.type === "boolean") {
      payload[field.key] = toBooleanPatchValue(nextRaw);
      continue;
    }

    if (nextRaw === "") {
      payload[field.key] = null;
      continue;
    }

    if (field.type === "number") {
      const parsed = Number(nextRaw);
      payload[field.key] = Number.isFinite(parsed) ? parsed : nextRaw;
      continue;
    }

    payload[field.key] = nextRaw;
  }

  return payload;
}

function runtimeDiffExists(
  draft: Record<string, string>,
  baseline: Record<string, string>,
): boolean {
  return (
    Object.keys(buildRuntimePatchPayload(draft, baseline)).length > 0
  );
}

function sectionedRuntimeSettings(fields: RuntimeSettingField[]) {
  const grouped: Record<string, RuntimeSettingField[]> = {};
  for (const field of fields) {
    const list = grouped[field.section] ?? [];
    list.push(field);
    grouped[field.section] = list;
  }
  return grouped;
}

export function SystemOpsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<
    "overview" | "collection" | "runtime" | "worker"
  >("overview");
  const [runtimeDraft, setRuntimeDraft] = useState<Record<string, string>>({});
  const [runtimeNotice, setRuntimeNotice] = useState<string | null>(null);
  const { data, error, failureReason } = useQuery({
    queryKey: ["system-ops"],
    queryFn: ({ signal }) => fetchSystemOps(signal),
    placeholderData: systemOpsFixture,
  });
  const liveFailed = Boolean(error ?? failureReason);
  const { data: statusData } = useQuery({
    queryKey: ["system-status"],
    queryFn: ({ signal }) => fetchSystemStatus(signal),
  });

  const payload = data ?? systemOpsFixture;
  const runtimeSettingsQuery = useQuery({
    queryKey: ["system-ops-runtime-settings"],
    queryFn: ({ signal }) => fetchRuntimeSettings(signal),
    placeholderData: payload.runtimeSettings,
  });
  const runtimeSettings = runtimeSettingsQuery.data ?? payload.runtimeSettings;
  const runtimeBaselineSource = useMemo(
    () => buildRuntimeDraftSource(runtimeSettings.values),
    [runtimeSettings],
  );
  const runtimeSections = useMemo(
    () => sectionedRuntimeSettings(RUNTIME_SETTING_FIELDS),
    [],
  );
  const hasRuntimeChanges = runtimeDiffExists(runtimeDraft, runtimeBaselineSource);

  const runtimeMutation = useMutation({
    mutationFn: (values: SystemOpsRuntimeSettingsPayload["values"]) =>
      updateRuntimeSettings(values),
    onSuccess: (updated) => {
      queryClient.setQueryData(
        ["system-ops-runtime-settings"],
        updated,
      );
      queryClient.invalidateQueries({ queryKey: ["system-ops"] });
      setRuntimeNotice("Runtime settings saved.");
    },
    onError: () => {
      setRuntimeNotice("Failed to save runtime settings.");
    },
  });

  const handleRuntimeFieldChange = (key: string, value: string): void => {
    setRuntimeDraft((prev) => ({ ...prev, [key]: value }));
  };

  const resetRuntimeSettings = (): void => {
    setRuntimeDraft(runtimeBaselineSource);
    setRuntimeNotice("Runtime settings reset to saved values.");
  };

  const saveRuntimeSettings = (): void => {
    const payloadValues = buildRuntimePatchPayload(
      runtimeDraft,
      runtimeBaselineSource,
    );
    if (Object.keys(payloadValues).length === 0) {
      setRuntimeNotice("No changes to save.");
      return;
    }
    runtimeMutation.mutate(payloadValues);
  };

  const resetOverridesMutation = useMutation({
    mutationFn: () => resetRuntimeOverridesApi(),
    onSuccess: (updated) => {
      queryClient.setQueryData(["system-ops-runtime-settings"], updated);
      queryClient.invalidateQueries({ queryKey: ["system-ops"] });
      setRuntimeNotice("All overrides reverted to .env defaults.");
    },
    onError: () => setRuntimeNotice("Failed to reset overrides."),
  });

  useEffect(() => {
    setRuntimeDraft(runtimeBaselineSource);
    setRuntimeNotice(null);
  }, [runtimeBaselineSource]);

  if (error && !data) {
    return (
      <EmptyState
        testId="system-ops-error"
        title="System Ops is unavailable"
        message={
          "The API is unreachable and no fixture is cached. " +
          "Check the FastAPI container and reload."
        }
      />
    );
  }

  const dbBadgeTone = statusData?.dbStatus === "LIVE" ? "success" : "danger";
  const staleSummary = statusData
    ? summarizeStaleFlags(statusData.staleFlags)
    : {
        badge: "loading",
        tone: "info" as const,
        text: "Status endpoint loading.",
      };

  return (
    <div className="fso-system-ops" data-testid="system-ops-page">
      {liveFailed ? (
        <StatusPill
          label="Live data unavailable — showing sample shape, not live data"
          tone="warning"
          testId="system-ops-live-failed"
        />
      ) : null}
      <SectionHeader eyebrow="FinSkillOS · Module" title="System Ops" />
      <div
        className="fso-system-ops-tabs"
        role="tablist"
        aria-label="System Ops sections"
      >
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "overview"}
          className={activeTab === "overview" ? "active" : ""}
          data-testid="system-ops-tab-overview"
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "collection"}
          className={activeTab === "collection" ? "active" : ""}
          data-testid="system-ops-tab-collection"
          onClick={() => setActiveTab("collection")}
        >
          Collection Control
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "runtime"}
          className={activeTab === "runtime" ? "active" : ""}
          data-testid="system-ops-tab-runtime"
          onClick={() => setActiveTab("runtime")}
        >
          Runtime Settings
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "worker"}
          className={activeTab === "worker" ? "active" : ""}
          data-testid="system-ops-tab-worker"
          onClick={() => setActiveTab("worker")}
        >
          Worker Status
        </button>
      </div>
      {activeTab === "overview" ? (
        <>
          <div className="fso-v42-topline">
            <JudgmentHeader judgment={payload.judgment} />
            <DriversPanel
              drivers={payload.drivers.map((driver) => ({
                label: driver.title,
                value: driver.score,
                detail: driver.note,
              }))}
            />
            <ConflictsPanel
              conflicts={payload.conflicts.map((conflict) => ({
                label: conflict.title,
                description: conflict.note,
              }))}
            />
          </div>
          <div className="fso-system-ops-evidence-row">
            <Panel
              title="System Health"
              badge={statusData?.dbStatus ?? payload.systemStatus.db}
              badgeTone={dbBadgeTone}
              testId="system-health"
            >
              <SystemHealthSummary
                mode={statusData?.mode ?? payload.systemStatus.mode}
                apiStatus={statusData?.apiStatus ?? "LIVE"}
                dbStatus={statusData?.dbStatus ?? payload.systemStatus.db}
                source={statusData?.source ?? payload.source}
                completeness={statusData?.dataCompleteness ?? "missing"}
              />
            </Panel>
            <Panel
              title="Freshness Status"
              badge={staleSummary.badge}
              badgeTone={staleSummary.tone}
              testId="migration-status"
            >
              <FreshnessSummary
                status={statusData}
                staleText={staleSummary.text}
              />
            </Panel>
          </div>
          <div data-testid="system-ops-data-sources">
            <DataSourceStrip pills={payload.dataSources} />
          </div>
          <div data-testid="system-ops-protocols">
            <Panel
              title="Operational Protocols"
              badge="Safe"
              badgeTone="info"
              testId="protocol-cards"
            >
              <div className="fso-system-ops-protocol-list">
                {payload.protocols.map((protocol) => (
                  <ProtocolCardItem
                    key={protocol.key}
                    protocol={protocol}
                    onRun={() => runSystemOpsProtocol(protocol.key)}
                  />
                ))}
              </div>
              {payload.recentProtocolRuns.length > 0 ? (
                <div
                  className="fso-system-ops-history"
                  data-testid="recent-protocol-runs"
                >
                  {payload.recentProtocolRuns.map((run) => {
                    const evidence = deriveProtocolEvidence(run);
                    const runTestId = run.protocol.replace(/_/g, "-");
                    return (
                      <div
                        className="fso-system-ops-history-run"
                        key={`${run.protocol}-${run.ranAt}`}
                      >
                        <p className="fso-system-ops-history-summary">
                          {run.ranAt} · {run.protocol} · {run.status} ·{" "}
                          {run.dbStatus}
                        </p>
                        {evidence.length > 0 ? (
                          <dl
                            className="fso-system-ops-history-evidence"
                            data-testid={`recent-protocol-run-evidence-${runTestId}`}
                          >
                            {evidence.map((item) => (
                              <div
                                className="fso-system-ops-history-chip"
                                key={`${item.key}-${item.value}`}
                              >
                                <dt>{item.key}</dt>
                                <dd>{item.value}</dd>
                              </div>
                            ))}
                          </dl>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              ) : null}
            </Panel>
          </div>
          <p
            className="fso-system-ops-caption"
            data-testid="system-ops-safety-caption"
          >
            {payload.safetyCaption}
          </p>
          <InterpretationPanel
            bullets={[
              payload.interpretation.verdict,
              payload.interpretation.whyItMatters,
              payload.interpretation.whatRemainsUncertain,
            ]}
          />
          <WatchpointsPanel
            watchpoints={payload.watchpoints.map((watchpoint) => ({
              label: watchpoint.title,
              description: watchpoint.note,
            }))}
          />
          <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
        </>
      ) : activeTab === "collection" ? (
        <CollectionControlPanel />
      ) : activeTab === "runtime" ? (
        <RuntimeSettingsDashboard
          draft={runtimeDraft}
          sections={runtimeSections}
          hasChanges={hasRuntimeChanges}
          isSaving={runtimeMutation.isPending}
          notice={runtimeNotice}
          isLoading={runtimeSettingsQuery.isLoading}
          hasError={runtimeSettingsQuery.isError}
          onFieldChange={handleRuntimeFieldChange}
          onReset={resetRuntimeSettings}
          onSave={saveRuntimeSettings}
          saveError={runtimeMutation.error?.message ?? null}
          updatedAt={runtimeSettings.updatedAt ?? null}
          updatedBy={runtimeSettings.updatedBy ?? null}
          overrideCount={Object.keys(runtimeSettings.overrides ?? {}).length}
          history={runtimeSettings.history ?? []}
          onResetOverrides={() => resetOverridesMutation.mutate()}
          isResetting={resetOverridesMutation.isPending}
        />
      ) : (
        <WorkerStatusDashboard workerStatus={payload.workerStatus} />
      )}
    </div>
  );
}

function RuntimeSettingsDashboard({
  draft,
  sections,
  hasChanges,
  isSaving,
  notice,
  isLoading,
  hasError,
  onFieldChange,
  onReset,
  onSave,
  saveError,
  updatedAt,
  updatedBy,
  overrideCount,
  history,
  onResetOverrides,
  isResetting,
}: {
  draft: Record<string, string>;
  sections: Record<string, RuntimeSettingField[]>;
  hasChanges: boolean;
  isSaving: boolean;
  notice: string | null;
  isLoading: boolean;
  hasError: boolean;
  onFieldChange: (key: string, value: string) => void;
  onReset: () => void;
  onSave: () => void;
  saveError: string | null;
  updatedAt: string | null;
  updatedBy: string | null;
  overrideCount: number;
  history: RuntimeSettingChange[];
  onResetOverrides: () => void;
  isResetting: boolean;
}) {
  const orderedSections = Object.entries(sections);
  const lastChangedLabel =
    overrideCount > 0 && updatedAt
      ? `${overrideCount} override${overrideCount === 1 ? "" : "s"} active · last changed ${new Date(updatedAt).toLocaleString()}${updatedBy ? ` by ${updatedBy}` : ""}`
      : "No overrides — all settings use .env defaults.";

  return (
    <Panel
      title="Runtime Settings"
      badge="Runtime Overlay"
      badgeTone="info"
      testId="system-ops-runtime-settings"
    >
      <div className="fso-runtime-audit-row">
        <p
          className="fso-runtime-audit"
          data-testid="system-ops-runtime-audit"
          data-has-overrides={overrideCount > 0 ? "true" : "false"}
        >
          {lastChangedLabel}
        </p>
        {overrideCount > 0 ? (
          <button
            type="button"
            className="fso-runtime-reset-all"
            disabled={isResetting}
            data-testid="system-ops-runtime-reset-all"
            title="Revert every override back to its .env default."
            onClick={onResetOverrides}
          >
            {isResetting ? "Resetting…" : "Reset all to defaults"}
          </button>
        ) : null}
      </div>
      <div className="fso-runtime-settings">
        {orderedSections.map(([section, fields]) => (
          <section className="fso-runtime-section" key={section}>
            <header className="fso-runtime-section-header">
              <h3>{section}</h3>
              <small>Applied as startup overlay over .env values.</small>
            </header>
            <div className="fso-runtime-fields">
              {fields.map((field) => {
                const value = draft[field.key] ?? "";
                const isBoolean = field.type === "boolean";
                return (
                  <label className="fso-runtime-field" key={field.key}>
                    <span className="fso-runtime-label">
                      {field.label}
                    </span>
                    {isBoolean ? (
                      <div className="fso-runtime-checkbox">
                        <input
                          type="checkbox"
                          checked={value === "1"}
                          onChange={(event) =>
                            onFieldChange(field.key, event.target.checked ? "1" : "0")
                          }
                          disabled={isSaving}
                          aria-label={`Toggle ${field.label}`}
                        />
                        <span>Enabled</span>
                      </div>
                    ) : field.type === "select" ? (
                      <select
                        className="fso-runtime-input"
                        value={value || (field.options?.[0] ?? "")}
                        onChange={(event) =>
                          onFieldChange(field.key, event.currentTarget.value)
                        }
                        disabled={isSaving}
                      >
                        {(field.options ?? []).map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        className="fso-runtime-input"
                        type={field.type}
                        value={value}
                        placeholder={field.placeholder}
                        min={field.type === "number" ? (field.min ?? 1) : undefined}
                        onChange={(event) =>
                          onFieldChange(field.key, event.currentTarget.value)
                        }
                        disabled={isSaving}
                      />
                    )}
                    <small>{field.hint}</small>
                    {field.key === MARKET_ADAPTER_KEY && value === "mock" ? (
                      <small
                        className="fso-runtime-warning"
                        data-testid="runtime-market-adapter-warning"
                      >
                        ⚠ Mock writes synthetic bars that can desync the live chart.
                        Use yahoo for real data.
                      </small>
                    ) : null}
                  </label>
                );
              })}
            </div>
          </section>
        ))}
      </div>
      <div className="fso-runtime-actions">
        <button
          type="button"
          className="fso-runtime-button"
          onClick={onReset}
          disabled={isSaving || isLoading || !hasChanges}
          data-testid="runtime-settings-reset"
        >
          Reset
        </button>
        <button
          type="button"
          className="fso-runtime-button primary"
          onClick={onSave}
          disabled={isSaving || isLoading || !hasChanges}
          data-testid="runtime-settings-save"
        >
          {isSaving ? "Saving…" : "Save"}
        </button>
        <span
          className="fso-runtime-action-note"
          data-testid="runtime-settings-notice"
          data-tone={
            saveError
              ? "error"
              : notice?.toLowerCase().includes("fail")
                ? "error"
                : notice?.toLowerCase().includes("saved")
                  ? "success"
                  : "info"
          }
        >
          {saveError ??
            notice ??
            (hasError
              ? "Runtime settings from the dedicated endpoint are unavailable."
              : "")}
        </span>
      </div>
      {history.length > 0 ? (
        <div className="fso-runtime-history" data-testid="system-ops-runtime-history">
          <h3>Change history</h3>
          <ul>
            {history.slice(0, 10).map((change, index) => (
              <li key={`${change.key}-${change.changedAt}-${index}`}>
                <code>{change.key}</code>{" "}
                <span className="fso-runtime-history-change">
                  {formatOverrideValue(change.oldValue)} →{" "}
                  {formatOverrideValue(change.newValue)}
                </span>
                <span className="fso-runtime-history-meta">
                  {change.changedAt
                    ? new Date(change.changedAt).toLocaleString()
                    : ""}{" "}
                  · {change.updatedBy}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </Panel>
  );
}

function formatOverrideValue(value: string | null): string {
  return value === null ? "default" : value;
}

function SystemHealthSummary({
  mode,
  apiStatus,
  dbStatus,
  source,
  completeness,
}: {
  mode: string;
  apiStatus: string;
  dbStatus: string;
  source: SystemStatusSource | "fixture" | "live";
  completeness: DataCompleteness | "missing";
}) {
  return (
    <div className="fso-health-summary" data-testid="system-status-summary">
      <HealthMetric label="API" value={apiStatus} tone="success" />
      <HealthMetric
        label="DB"
        value={dbStatus}
        tone={dbStatus === "LIVE" ? "success" : "danger"}
      />
      <HealthMetric label="Mode" value={mode} tone="info" />
      <HealthMetric
        label="Source"
        value={source.toUpperCase()}
        tone={source === "live" ? "success" : "warning"}
      />
      <HealthMetric
        label="Completeness"
        value={completeness.toUpperCase()}
        tone={completeness === "complete" ? "success" : "warning"}
      />
    </div>
  );
}

function HealthMetric({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "success" | "warning" | "danger" | "info";
}) {
  return (
    <div className="fso-health-metric" data-tone={tone}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function FreshnessSummary({
  status,
  staleText,
}: {
  status: SystemStatusData | undefined;
  staleText: string;
}) {
  const items: Array<[string, string | null]> = status
    ? [
        ["Portfolio", status.latestPortfolioSnapshotAt],
        ["Market", status.latestMarketBarAt],
        ["Indicators", status.latestIndicatorAt],
        ["Regime", status.latestRegimeAt],
        ["News", status.latestNewsAt],
        ["Events", status.latestEventAt],
      ]
    : [
        ["Portfolio", null],
        ["Market", null],
        ["Indicators", null],
        ["Regime", null],
        ["News", null],
        ["Events", null],
      ];

  return (
    <div className="fso-freshness-summary">
      <p className="fso-freshness-note" data-testid="system-freshness-status">
        {staleText}
      </p>
      <div className="fso-freshness-grid">
        {items.map(([label, value]) => (
          <div
            className="fso-freshness-item"
            data-state={value ? "available" : "missing"}
            key={label}
            title={value ?? "missing"}
          >
            <span>{label}</span>
            <strong>{formatFreshnessValue(value)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function WorkerStatusDashboard({
  workerStatus,
}: {
  workerStatus: WorkerStatusSummary;
}) {
  const queryClient = useQueryClient();
  const liveModeMutation = useMutation({
    mutationFn: (enabled: boolean) => setWorkerLiveMode(enabled),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["system-ops"] }),
  });
  const retryMutation = useMutation({
    mutationFn: (jobId: string) => retryWorkerJob(jobId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["system-ops"] }),
  });
  const liveMode = workerStatus.liveMode;
  const latest = workerStatus.recentCycles[0] ?? null;
  const components = latest
    ? [
        {
          label: "Market",
          status: latest.marketStatus,
          scope: latest.marketScope,
          value: "Bars",
        },
        {
          label: "News",
          status: latest.newsStatus,
          scope: latest.newsScope,
          value: "Feeds",
        },
        {
          label: "Indicators",
          status: latest.indicatorStatus,
          scope: latest.indicatorScope,
          value: "Signals",
        },
      ]
    : [
        { label: "Market", status: "MISSING", scope: "unknown", value: "Bars" },
        { label: "News", status: "MISSING", scope: "unknown", value: "Feeds" },
        {
          label: "Indicators",
          status: "MISSING",
          scope: "unknown",
          value: "Signals",
        },
      ];

  return (
    <div className="fso-worker-tab" data-testid="worker-status-dashboard">
      <Panel
        title="Worker Status"
        badge={workerStatus.cadenceStatus.toLowerCase()}
        badgeTone={workerCadenceBadgeTone(workerStatus.cadenceStatus)}
      >
        <div className="fso-worker-hero">
          <div
            className="fso-worker-status-orb"
            data-status={workerStatus.status}
            aria-hidden
          />
          <div className="fso-worker-hero-copy">
            <span>Latest cycle</span>
            <strong>{workerStatus.status}</strong>
            {latest?.outcome ? (
              <small
                className="fso-worker-outcome"
                data-testid="worker-latest-outcome"
              >
                {latest.outcome}
              </small>
            ) : null}
            <small>{workerStatus.latestDetail}</small>
            <small>{workerStatus.cadenceDetail}</small>
            <div
              className="fso-worker-livemode"
              data-testid="worker-live-mode"
              data-live={liveMode}
            >
              <span className="fso-worker-livemode-label">
                Live mode · {liveMode ? "ON" : "OFF"}
              </span>
              <button
                type="button"
                className="fso-worker-livemode-toggle"
                onClick={() => liveModeMutation.mutate(!liveMode)}
                disabled={liveModeMutation.isPending}
                data-testid="worker-live-mode-toggle"
              >
                {liveModeMutation.isPending
                  ? "Updating…"
                  : liveMode
                    ? "Turn off"
                    : "Turn on"}
              </button>
            </div>
            <small className="fso-worker-livemode-hint">
              {liveMode
                ? "Worker auto-refreshes on its interval. Manual refresh always works."
                : "Auto-refresh paused. Use a System Ops refresh to update on demand."}
            </small>
          </div>
          <div className="fso-worker-metrics">
            <WorkerMetric
              label="Started"
              value={workerStatus.latestStartedAt ?? "No cycle"}
            />
            <WorkerMetric
              label="Finished"
              value={workerStatus.latestFinishedAt ?? "No cycle"}
            />
            <WorkerMetric
              label="Cadence"
              value={workerStatus.cadenceStatus}
            />
            <WorkerMetric
              label="Next due"
              value={workerStatus.expectedNextCycleAt ?? "Unknown"}
            />
            <WorkerMetric
              label="Recent"
              value={`${workerStatus.recentCycles.length} cycles`}
            />
          </div>
        </div>
      </Panel>

      <div className="fso-worker-grid">
        <Panel title="Cycle Components" badge="Read model" badgeTone="info">
          <div className="fso-worker-components">
            {components.map((component) => (
              <div
                className="fso-worker-component"
                data-status={component.status}
                key={component.label}
              >
                <span>{component.label}</span>
                <strong>{component.status}</strong>
                <small>{component.value} · {component.scope}</small>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Recent Cycle Trace" badge="5 latest" badgeTone="neutral">
          {workerStatus.recentCycles.length > 0 ? (
            <div className="fso-worker-trace" data-testid="worker-cycle-trace">
              {workerStatus.recentCycles.map((cycle) => (
                <WorkerCycleRow
                  key={`${cycle.startedAt}-${cycle.finishedAt}`}
                  cycle={cycle}
                />
              ))}
            </div>
          ) : (
            <div className="fso-worker-empty">
              No worker cycle has been recorded.
            </div>
          )}
        </Panel>

        <Panel
          title="Provider Health"
          badge={workerStatus.providerHealth.status.toLowerCase()}
          badgeTone={providerHealthTone(workerStatus.providerHealth.status)}
        >
          <p
            className="fso-provider-detail"
            data-status={workerStatus.providerHealth.status}
            data-testid="provider-health-detail"
          >
            {workerStatus.providerHealth.detail}
          </p>
          <div className="fso-provider-meta">
            <WorkerMetric
              label="Last clean"
              value={formatTimeAgo(workerStatus.providerHealth.lastSuccessAt)}
            />
            <WorkerMetric
              label="Last failure"
              value={formatTimeAgo(workerStatus.providerHealth.lastFailureAt)}
            />
            <WorkerMetric
              label="Failing cycles"
              value={`${workerStatus.providerHealth.consecutiveFailureCycles}`}
            />
          </div>
          {workerStatus.providerHealth.affectedTickers.length > 0 ? (
            <div className="fso-provider-tickers" data-testid="provider-health-tickers">
              {workerStatus.providerHealth.affectedTickers.map((t) => (
                <span
                  key={t.ticker}
                  className="fso-provider-ticker"
                  title={t.error}
                >
                  {t.ticker}
                </span>
              ))}
            </div>
          ) : null}
        </Panel>

        <DataProvenancePanel />

        <DataInvariantPanel />

        <FeedCoveragePanel />

        <DataRepairPanel />

        <Panel
          title="Job Queue"
          badge={formatJobCounts(workerStatus.jobCounts)}
          badgeTone="neutral"
        >
          {workerStatus.recentJobs.length > 0 ? (
            <div className="fso-worker-jobs" data-testid="worker-job-queue">
              {workerStatus.recentJobs.map((job) => (
                <div
                  className="fso-worker-job-row"
                  key={job.id}
                  data-status={job.status}
                  data-testid={`worker-job-${job.id}`}
                >
                  <div className="fso-worker-job-main">
                    <span className="fso-worker-job-status" data-status={job.status}>
                      {job.status}
                    </span>
                    <strong>{job.jobType}</strong>
                    {job.folderId ? (
                      <span className="fso-worker-job-scope">folder-scoped</span>
                    ) : null}
                    <span className="fso-worker-job-by">· {job.requestedBy}</span>
                  </div>
                  <div className="fso-worker-job-meta">
                    <span>{job.finishedAt ?? job.createdAt ?? ""}</span>
                    {job.error ? (
                      <span className="fso-worker-job-error" title={job.error}>
                        {job.error}
                      </span>
                    ) : null}
                  </div>
                  {job.retryable ? (
                    <button
                      type="button"
                      className="fso-worker-job-retry"
                      disabled={retryMutation.isPending}
                      data-testid={`worker-job-retry-${job.id}`}
                      onClick={() => retryMutation.mutate(job.id)}
                    >
                      {job.status === "ERROR" ? "Retry" : "Re-run"}
                    </button>
                  ) : null}
                </div>
              ))}
            </div>
          ) : (
            <div className="fso-worker-empty">No worker jobs have been queued.</div>
          )}
          {retryMutation.isError ? (
            <p className="fso-worker-job-notice" data-tone="error" role="status">
              Could not re-enqueue the job.
            </p>
          ) : null}
        </Panel>
      </div>
    </div>
  );
}

function formatJobCounts(counts: Record<string, number>): string {
  const order = ["QUEUED", "RUNNING", "DONE", "ERROR"];
  const parts = order
    .filter((status) => counts[status])
    .map((status) => `${counts[status]} ${status.toLowerCase()}`);
  return parts.length > 0 ? parts.join(" · ") : "no jobs";
}

function providerHealthTone(
  status: WorkerStatusSummary["providerHealth"]["status"],
): "success" | "warning" | "danger" | "neutral" {
  if (status === "HEALTHY") return "success";
  if (status === "DEGRADED") return "warning";
  if (status === "FAILING") return "danger";
  return "neutral";
}

function formatTimeAgo(iso: string | null): string {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const seconds = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

function WorkerMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="fso-worker-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function WorkerCycleRow({ cycle }: { cycle: WorkerCycleRecord }) {
  return (
    <div className="fso-worker-cycle-row" data-status={cycle.status}>
      <div className="fso-worker-cycle-time">
        <strong>{cycle.status}</strong>
        <span>{cycle.startedAt}</span>
      </div>
      <div className="fso-worker-cycle-bars" aria-label="Cycle component status">
        <span data-status={cycle.marketStatus}>Market</span>
        <span data-status={cycle.newsStatus}>News</span>
        <span data-status={cycle.indicatorStatus}>Indicators</span>
      </div>
      {cycle.outcome ? (
        <p className="fso-worker-cycle-outcome">{cycle.outcome}</p>
      ) : null}
      <div className="fso-worker-cycle-meta">
        <span>{formatDuration(cycle.startedAt, cycle.finishedAt)}</span>
        <span>{cycle.timeframe}</span>
        <span>{cycle.marketScope}</span>
      </div>
    </div>
  );
}

function workerCadenceBadgeTone(
  status: WorkerCadenceStatus,
): "info" | "success" | "warning" | "danger" {
  if (status === "FRESH") {
    return "success";
  }
  if (status === "STALE") {
    return "warning";
  }
  if (status === "ERROR") {
    return "danger";
  }
  return "info";
}

function formatDuration(start: string | null, finish: string | null): string {
  if (!start || !finish) {
    return "Pending";
  }
  const startedAt = Date.parse(start);
  const finishedAt = Date.parse(finish);
  if (Number.isNaN(startedAt) || Number.isNaN(finishedAt)) {
    return "Unknown";
  }
  const seconds = Math.max(0, Math.round((finishedAt - startedAt) / 1000));
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

function formatFreshnessValue(value: string | null): string {
  if (!value) {
    return "Missing";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function summarizeStaleFlags(flags: string[]): {
  badge: string;
  tone: "info" | "success" | "warning";
  text: string;
} {
  if (flags.length === 0) {
    return {
      badge: "fresh",
      tone: "success",
      text: "No stale data flags reported by the operations contract.",
    };
  }
  return {
    badge: `${flags.length} stale`,
    tone: "warning",
    text: `Stale flags: ${flags.slice(0, 3).join(", ")}${
      flags.length > 3 ? " ..." : ""
    }`,
  };
}
