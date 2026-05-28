import { useQuery } from "@tanstack/react-query";
import { fetchAnalysisWorkspace } from "@/features/analysis/api";
import { IndexUniverseTable } from "@/features/analysis/components/IndexUniverseTable";
import { TapeStrengthCards } from "@/features/analysis/components/TapeStrengthCards";
import { RegimeContextPanel } from "@/features/analysis/components/RegimeContextPanel";
import { MissingDataPanel } from "@/features/analysis/components/MissingDataPanel";
import { analysisWorkspaceFixture } from "@/mocks/fixtures/analysisWorkspace.fixture";
import {
  Badge,
  ConflictsPanel,
  DriversPanel,
  EmptyState,
  InterpretationPanel,
  JudgmentHeader,
  SafetyCaption,
  SectionHeader,
  WatchpointsPanel,
} from "@/shared/ui";
import type { BadgeTone } from "@/shared/ui/Badge";
import type { AnalysisWorkspaceData } from "@/features/analysis/types";
import "./analysis-workspace.css";

export function AnalysisWorkspacePage() {
  const { data, error } = useQuery({
    queryKey: ["analysis-workspace"],
    queryFn: ({ signal }) => fetchAnalysisWorkspace(signal),
    placeholderData: analysisWorkspaceFixture,
  });

  if (error && !data) {
    return (
      <EmptyState
        testId="analysis-workspace-error"
        title="Analysis Workspace is unavailable"
        message={
          "The API is unreachable and no fixture is cached. " +
          "Check the FastAPI container and reload."
        }
      />
    );
  }

  const payload = data ?? analysisWorkspaceFixture;

  return (
    <div
      className="fso-analysis-workspace"
      data-testid="analysis-workspace-page"
    >
      <SectionHeader
        eyebrow="FinSkillOS · Module"
        title="Analysis Workspace"
      />
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
      <AnalysisDataStateBand payload={payload} />
      <div className="fso-analysis-grid">
        <div className="fso-analysis-main">
          <div data-testid="analysis-workspace-universe-table">
            <IndexUniverseTable rows={payload.universe} />
          </div>
          <div data-testid="analysis-workspace-strongest">
            <TapeStrengthCards
              strongest={payload.strongest}
              weakest={payload.weakest}
            />
          </div>
        </div>
        <aside className="fso-analysis-side" aria-label="Regime context">
          <div data-testid="analysis-workspace-regime">
            <RegimeContextPanel regime={payload.regime} />
          </div>
          <MissingDataPanel
            tickers={payload.missingData}
            setupHint={payload.setupHint}
          />
        </aside>
      </div>
      <p
        className="fso-analysis-safety"
        data-testid="analysis-workspace-safety-caption"
      >
        {payload.safetyCaption} Stored data only.
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
    </div>
  );
}

function AnalysisDataStateBand({ payload }: { payload: AnalysisWorkspaceData }) {
  const state = payload.dataState;
  const sourceLabel = state.universeSource === "live" ? "LIVE" : "FIXTURE";
  const sourceTone: BadgeTone =
    state.universeSource === "live" ? "success" : "warning";
  const latestLabel = state.latestSnapshotAt
    ? state.latestSnapshotAt.slice(0, 10)
    : "No snapshot";

  return (
    <div
      className="fso-analysis-state-band"
      data-testid="analysis-workspace-data-state"
    >
      <AnalysisStateItem
        label="Universe source"
        value={sourceLabel}
        detail={state.sourceNote}
        tone={sourceTone}
      />
      <AnalysisStateItem
        label="Coverage"
        value={state.coverageLevel}
        detail={`${state.okCount}/${state.universeCount} complete · ${state.evidenceCoveragePercent}% evidence`}
        tone={coverageTone(state.coverageLevel)}
      />
      <AnalysisStateItem
        label="Ranked tape"
        value={state.rankedStatus}
        detail={`${state.rankedCount} ranked rows · ${latestLabel}`}
        tone={state.rankedStatus === "READY" ? "info" : "neutral"}
      />
      <AnalysisStateItem
        label="Gap focus"
        value={state.missingCount > 0 ? `${state.missingCount}` : "NONE"}
        detail={state.missingSummary}
        tone={state.missingCount > 0 ? "warning" : "success"}
      />
      <AnalysisStateItem
        label="Regime"
        value={state.regimeStatus}
        detail={state.refreshNote}
        tone={state.regimeStatus === "AVAILABLE" ? "success" : "neutral"}
      />
    </div>
  );
}

function coverageTone(
  level: AnalysisWorkspaceData["dataState"]["coverageLevel"],
): BadgeTone {
  if (level === "COMPLETE") {
    return "success";
  }
  if (level === "PARTIAL" || level === "SPARSE") {
    return "warning";
  }
  return "neutral";
}

interface AnalysisStateItemProps {
  label: string;
  value: string;
  detail: string;
  tone: BadgeTone;
}

function AnalysisStateItem({
  label,
  value,
  detail,
  tone,
}: AnalysisStateItemProps) {
  return (
    <div className="fso-analysis-state-item">
      <span>{label}</span>
      <Badge tone={tone}>{value}</Badge>
      <small>{detail}</small>
    </div>
  );
}
