import { useSearchParams } from "react-router-dom";
import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  addSymbolToFolder,
  createSymbolSubscriptionFolder,
  fetchSymbolLab,
  fetchSymbolSubscriptionFolders,
  removeSymbolFromFolder,
  setSymbolSubscription,
} from "@/features/symbol/api";
import type { SymbolLabData } from "@/features/symbol/types";
import { SymbolAlertsPanel } from "@/features/symbol/components/SymbolAlertsPanel";
import { SymbolNewsPanel } from "@/features/symbol/components/SymbolNewsPanel";
import { SymbolPositionContext } from "@/features/symbol/components/SymbolPositionContext";
import { SymbolCandlestickChart } from "@/features/symbol/components/SymbolCandlestickChart";
import { SymbolRecentBarsTable } from "@/features/symbol/components/SymbolRecentBarsTable";
import { SymbolSearchPanel } from "@/features/symbol/components/SymbolSearchPanel";
import { SymbolSubscriptionFoldersPanel } from "@/features/symbol/components/SymbolSubscriptionFoldersPanel";
import { SymbolTechnicalSnapshot } from "@/features/symbol/components/SymbolTechnicalSnapshot";
import { SymbolWatchpoints } from "@/features/symbol/components/SymbolWatchpoints";
import { RegimeContextPanel } from "@/features/analysis/components/RegimeContextPanel";
import {
  Badge,
  ConflictsPanel,
  DriversPanel,
  InterpretationPanel,
  JudgmentHeader,
  Panel,
  SafetyCaption,
  SectionHeader,
  WatchpointsPanel,
} from "@/shared/ui";
import type { BadgeTone } from "@/shared/ui";
import "@/pages/market-kernel/market-kernel.css";
import "./symbol-lab.css";

const DEFAULT_TICKER = "TSLA";
const DEFAULT_TIMEFRAME = "1d";

function pendingSymbolLabData(ticker: string, timeframe: string): SymbolLabData {
  return {
    generatedAt: "",
    source: "live",
    systemStatus: { db: "LIVE", mode: "READ_MODE", guardCount: 0 },
    judgment: {
      eyebrow: `SYMBOL JUDGMENT · ${ticker}`,
      title: "Loading",
      accent: "Evidence",
      summary: `${ticker} evidence is being loaded from the API.`,
      confidence: 0,
    },
    drivers: [
      {
        score: "—",
        title: "Stored bars",
        note: "Waiting for chart evidence.",
      },
    ],
    conflicts: [
      {
        title: "Loading state",
        note: "No fallback chart evidence is rendered while the request is pending.",
      },
    ],
    integratedInterpretation: {
      verdict: "Symbol evidence is loading.",
      whyItMatters: "The chart will render only after live data arrives.",
      whatRemainsUncertain: "API response freshness is still pending.",
    },
    reviewWatchpoints: [
      {
        title: "Chart evidence",
        note: "Candles are hidden until the requested symbol/timeframe resolves.",
      },
    ],
    symbolUniverse: [{ symbol: ticker, label: ticker, kind: "FOCUS" }],
    identity: {
      ticker,
      name: ticker,
      logoUrl: null,
      logoSource: "local_fallback",
      avatarText: ticker.replace(/[^A-Z]/g, "").slice(0, 2) || ticker.slice(0, 2),
      brandColor: "#475569",
    },
    subscription: {
      isSubscribed: false,
      canSubscribe: false,
      updateUniverseMember: false,
      lastAction: "none",
    },
    dataState: {
      chartStatus: "MISSING",
      chartEvidence: "missing",
      barCount: 0,
      coverageLevel: "EMPTY",
      evidenceCoveragePercent: 0,
      missingSummary: `${ticker} needs stored bars and indicators.`,
      indicatorStatus: "MISSING",
      logoSource: "local_fallback",
      subscriptionStatus: "unavailable",
      providerNote: null,
    },
    header: {
      ticker,
      timeframe,
      latestClose: null,
      latestTime: null,
      dataStatus: "MISSING",
    },
    technical: {
      rsi14: null,
      ema20: null,
      ema60: null,
      ema120: null,
      bbPosition: null,
      volumeZScore: null,
      momentumScore: null,
      trendState: null,
    },
    recentBars: [],
    position: null,
    alerts: [],
    news: [],
    regime: null,
    watchpoints: ["Waiting for live Symbol Lab evidence."],
    interpretation: "Symbol Lab is waiting for the requested chart evidence.",
    setupHint: null,
    safetyCaption:
      "Symbol interpretation (not trade signal). Stored data only · not prediction.",
  };
}

export function SymbolLabPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const ticker = (searchParams.get("ticker") ?? DEFAULT_TICKER).toUpperCase();
  const timeframe = searchParams.get("timeframe") ?? DEFAULT_TIMEFRAME;

  const { data, error, isFetching, isPending, isPlaceholderData, refetch } = useQuery({
    queryKey: ["symbol-lab", ticker, timeframe],
    queryFn: ({ signal }) => fetchSymbolLab(ticker, timeframe, signal),
    placeholderData: keepPreviousData,
  });

  const { data: folderData } = useQuery({
    queryKey: ["symbol-subscription-folders"],
    queryFn: ({ signal }) => fetchSymbolSubscriptionFolders(signal),
    placeholderData: { folders: [] },
  });

  const selectTicker = (next: string) => {
    const params = new URLSearchParams(searchParams);
    params.set("ticker", next);
    setSearchParams(params, { replace: false });
  };

  const selectTimeframe = (next: string) => {
    const params = new URLSearchParams(searchParams);
    params.set("ticker", ticker);
    params.set("timeframe", next);
    setSearchParams(params, { replace: false });
  };

  const subscriptionMutation = useMutation({
    mutationFn: (nextSubscribed: boolean) =>
      setSymbolSubscription(ticker, nextSubscribed, timeframe),
    onSuccess: (nextPayload) => {
      queryClient.setQueryData(["symbol-lab", ticker], nextPayload);
      queryClient.setQueryData(["symbol-lab", ticker, timeframe], nextPayload);
      queryClient.invalidateQueries({ queryKey: ["symbol-lab", ticker] });
      queryClient.invalidateQueries({ queryKey: ["system-status"] });
      queryClient.invalidateQueries({ queryKey: ["symbol-subscription-folders"] });
    },
  });

  const createFolderMutation = useMutation({
    mutationFn: (name: string) => createSymbolSubscriptionFolder(name),
    onSuccess: (nextFolders) => {
      queryClient.setQueryData(["symbol-subscription-folders"], nextFolders);
    },
  });

  const addToFolderMutation = useMutation({
    mutationFn: (folderId: string) => addSymbolToFolder(folderId, ticker),
    onSuccess: (nextFolders) => {
      queryClient.setQueryData(["symbol-subscription-folders"], nextFolders);
    },
  });

  const removeFromFolderMutation = useMutation({
    mutationFn: (folderId: string) => removeSymbolFromFolder(folderId, ticker),
    onSuccess: (nextFolders) => {
      queryClient.setQueryData(["symbol-subscription-folders"], nextFolders);
    },
  });

  const payload = data ?? pendingSymbolLabData(ticker, timeframe);
  const initialRequestPending = !data && isPending;
  const initialRequestError = !data && Boolean(error);
  const chartRequestPending =
    initialRequestPending ||
    isPlaceholderData ||
    (isFetching &&
      (payload.header.ticker !== ticker || payload.header.timeframe !== timeframe));
  const chartRequestError = initialRequestError || Boolean(error && data);
  const folderMutationBusy =
    createFolderMutation.isPending ||
    addToFolderMutation.isPending ||
    removeFromFolderMutation.isPending;

  return (
    <div className="fso-symbol-lab" data-testid="symbol-lab-page">
      <SectionHeader eyebrow="FinSkillOS · Module" title="Symbol Lab" />
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
      <SymbolSearchPanel
        currentTicker={ticker}
        universe={payload.symbolUniverse}
        onSelect={selectTicker}
      />
      <SymbolDataStateBand payload={payload} />
      {payload.setupHint ? (
        <div className="fso-symbol-inline-state" data-testid="symbol-lab-setup-hint">
          <strong>Limited data available</strong>
          <span>{payload.setupHint}</span>
        </div>
      ) : null}
      <div className="fso-symbol-lab-grid">
        <div className="fso-symbol-lab-main">
          <div data-testid="symbol-technical-snapshot">
            <SymbolTechnicalSnapshot
              identity={payload.identity}
              header={payload.header}
              indicators={payload.technical}
              subscription={payload.subscription}
              subscriptionBusy={subscriptionMutation.isPending}
              onToggleSubscription={() =>
                subscriptionMutation.mutate(!payload.subscription.isSubscribed)
              }
            />
          </div>
          {chartRequestPending ? (
            <SymbolLabChartRequestPanel
              ticker={ticker}
              timeframe={timeframe}
              status="loading"
            />
          ) : chartRequestError ? (
            <SymbolLabChartRequestPanel
              ticker={ticker}
              timeframe={timeframe}
              status="error"
              message={
                error instanceof Error
                  ? error.message
                  : "Symbol Lab chart data could not be loaded."
              }
              onRetry={() => void refetch()}
            />
          ) : (
            <SymbolCandlestickChart
              header={payload.header}
              bars={payload.recentBars}
              selectedTimeframe={timeframe}
              onTimeframeChange={selectTimeframe}
            />
          )}
          <SymbolRecentBarsTable bars={payload.recentBars} />
          <SymbolWatchpoints
            watchpoints={payload.watchpoints}
            interpretation={payload.interpretation}
            safetyCaption={payload.safetyCaption}
          />
          {/* v3 Phase 8 (182): integrated interpretation + review watchpoints flow
              in the main column to fill space beside the taller context rail. */}
          <InterpretationPanel
            bullets={[
              payload.integratedInterpretation.verdict,
              payload.integratedInterpretation.whyItMatters,
              payload.integratedInterpretation.whatRemainsUncertain,
            ]}
          />
          <WatchpointsPanel
            watchpoints={payload.reviewWatchpoints.map((watchpoint) => ({
              label: watchpoint.title,
              description: watchpoint.note,
            }))}
          />
        </div>
        <aside className="fso-symbol-lab-side" aria-label="Position + Risk context">
          <div data-testid="symbol-position-context">
            <SymbolPositionContext
              position={payload.position}
              ticker={payload.header.ticker}
            />
          </div>
          <SymbolAlertsPanel alerts={payload.alerts} />
          <SymbolSubscriptionFoldersPanel
            currentTicker={ticker}
            folders={folderData ?? { folders: [] }}
            subscription={payload.subscription}
            busy={folderMutationBusy}
            onAddToFolder={(folderId) => addToFolderMutation.mutate(folderId)}
            onCreateFolder={(name) => createFolderMutation.mutate(name)}
            onRemoveFromFolder={(folderId) =>
              removeFromFolderMutation.mutate(folderId)
            }
          />
          <SymbolNewsPanel news={payload.news} />
          <RegimeContextPanel regime={payload.regime} />
        </aside>
      </div>
      <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
    </div>
  );
}

function SymbolDataStateBand({ payload }: { payload: SymbolLabData }) {
  const state = payload.dataState;
  const sourceTone: BadgeTone = payload.source === "live" ? "success" : "warning";
  const coverageTone = coverageToneFor(state.coverageLevel);
  const indicatorTone = indicatorStatusTone(state.indicatorStatus);
  const logoTone = state.logoSource === "provider_cache" ? "success" : "neutral";
  const subscriptionTone = subscriptionStatusTone(state.subscriptionStatus);
  const coverageDetail =
    state.chartEvidence === "provider_preview"
      ? `${state.barCount} preview bars · ${state.evidenceCoveragePercent}% evidence`
      : state.chartEvidence === "stored"
        ? `${state.barCount} stored bars · ${state.evidenceCoveragePercent}% evidence`
        : state.providerNote ?? "No chart bars available";

  return (
    <div className="fso-symbol-state-band" data-testid="symbol-data-state">
      <SymbolStateItem
        label="Source"
        value={payload.source.toUpperCase()}
        detail={
          payload.source === "live"
            ? "DB-backed symbol context"
            : "Deterministic sample"
        }
        tone={sourceTone}
      />
      <SymbolStateItem
        label="Coverage"
        value={state.coverageLevel}
        detail={coverageDetail}
        tone={coverageTone}
      />
      <SymbolStateItem
        label="Indicators"
        value={state.indicatorStatus}
        detail={
          state.indicatorStatus === "AVAILABLE"
            ? (payload.header.latestTime ?? "No indicator timestamp")
            : state.missingSummary
        }
        tone={indicatorTone}
      />
      <SymbolStateItem
        label="Logo"
        value={state.logoSource.replace("_", " ")}
        detail={payload.identity.name}
        tone={logoTone}
      />
      <SymbolStateItem
        label="Universe"
        value={state.subscriptionStatus.replace("_", " ")}
        detail={payload.subscription.lastAction}
        tone={subscriptionTone}
      />
    </div>
  );
}

function coverageToneFor(
  level: SymbolLabData["dataState"]["coverageLevel"],
): BadgeTone {
  if (level === "COMPLETE") return "success";
  if (level === "PARTIAL" || level === "SPARSE") return "warning";
  return "neutral";
}

function indicatorStatusTone(
  status: SymbolLabData["dataState"]["indicatorStatus"],
): BadgeTone {
  if (status === "AVAILABLE") return "success";
  if (status === "PARTIAL") return "warning";
  return "neutral";
}

function subscriptionStatusTone(
  status: SymbolLabData["dataState"]["subscriptionStatus"],
): BadgeTone {
  if (status === "subscribed") return "success";
  if (status === "unavailable") return "neutral";
  return "info";
}

function SymbolStateItem({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  tone: BadgeTone;
}) {
  return (
    <div className="fso-symbol-state-item">
      <span>{label}</span>
      <Badge tone={tone}>{value}</Badge>
      <small>{detail}</small>
    </div>
  );
}

interface SymbolLabChartRequestPanelProps {
  ticker: string;
  timeframe: string;
  status: "loading" | "error";
  message?: string;
  onRetry?: () => void;
}

function SymbolLabChartRequestPanel({
  ticker,
  timeframe,
  status,
  message,
  onRetry,
}: SymbolLabChartRequestPanelProps) {
  const isLoading = status === "loading";

  return (
    <Panel
      title={`Candles · ${ticker}`}
      badge={timeframe.toUpperCase()}
      badgeTone={isLoading ? "info" : "danger"}
      className="fso-symbol-chart-request-panel"
      testId={isLoading ? "symbol-lab-loading" : "symbol-lab-error"}
    >
      <div
        className="fso-symbol-request-state"
        role={isLoading ? "status" : "alert"}
        aria-live="polite"
      >
        <div className={isLoading ? "fso-symbol-loader" : "fso-symbol-loader--error"}>
          {isLoading ? <span aria-hidden /> : "!"}
        </div>
        <div>
          <strong>
            {isLoading
              ? `Loading ${ticker} ${timeframe} chart`
              : `Could not load ${ticker} ${timeframe} chart`}
          </strong>
          <span>
            {isLoading
              ? "Fetching live Symbol Lab evidence before rendering the chart."
              : (message ?? "Check the API connection and try again.")}
          </span>
        </div>
        {!isLoading && onRetry ? (
          <button type="button" className="fso-symbol-chip" onClick={onRetry}>
            Retry
          </button>
        ) : null}
      </div>
    </Panel>
  );
}
