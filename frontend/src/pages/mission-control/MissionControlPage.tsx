import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchMissionControl } from "@/features/portfolio/api";
import { AgentIngestPanel } from "@/features/agent/components/AgentIngestPanel";
import { CapitalMapPanel } from "@/features/portfolio/components/CapitalMapPanel";
import { ConstraintSummaryPanel } from "@/features/portfolio/components/ConstraintSummaryPanel";
import { MilestoneTimeline } from "@/features/portfolio/components/MilestoneTimeline";
import { MissionAssetChart } from "@/features/portfolio/components/MissionAssetChart";
import { AllocationPie } from "@/features/portfolio/components/AllocationPie";
import { MissionGoalTracker } from "@/features/portfolio/components/MissionGoalTracker";
import { PortfolioEditorPanel } from "@/features/portfolio/components/PortfolioEditorPanel";
import { PortfolioSnapshotPanel } from "@/features/portfolio/components/PortfolioSnapshotPanel";
import { TossHoldingsPanel } from "@/features/portfolio/components/TossHoldingsPanel";
import { missionControlFixture } from "@/mocks/fixtures/missionControl.fixture";
import { formatKrw, formatPct } from "@/shared/lib/format";
import {
  Badge,
  EmptyState,
  JudgmentHeader,
  Panel,
  SectionHeader,
  StatusPill,
} from "@/shared/ui";
import type { BadgeTone } from "@/shared/ui/Badge";
import type { MissionControlData } from "@/features/portfolio/types";
import "./mission-control.css";

export function MissionControlPage() {
  const queryClient = useQueryClient();
  const { data, error, failureReason } = useQuery({
    queryKey: ["mission-control"],
    queryFn: ({ signal }) => fetchMissionControl(signal),
    placeholderData: missionControlFixture,
  });
  const liveFailed = Boolean(error ?? failureReason);

  if (error && !data) {
    return (
      <EmptyState
        testId="mission-control-error"
        title="Mission Control is unavailable"
        message={
          "The API is unreachable and no fixture is cached. " +
          "Check the FastAPI container and reload."
        }
      />
    );
  }

  const payload = data ?? missionControlFixture;
  const state = buildMissionControlState(payload);
  const generatedLabel = payload.generatedAt.slice(0, 16).replace("T", " ");
  const largestLabel = payload.portfolio.largestPositionTicker
    ? `${payload.portfolio.largestPositionTicker} · ${formatPct(
        payload.portfolio.largestPositionWeightPct,
      )}`
    : "—";

  return (
    <div className="fso-mission-control" data-testid="mission-control-page">
      {liveFailed ? (
        <StatusPill
          label="Live data unavailable — showing sample shape, not live data"
          tone="warning"
          testId="mission-control-live-failed"
        />
      ) : null}
      <SectionHeader eyebrow="FinSkillOS · Module" title="Mission Control" />
      <div className="fso-mission-top-row" data-testid="mission-top-row">
        <MissionAssetChart
          equitySeries={payload.equitySeries}
          realizedSeries={payload.realizedSeries}
        />
        <AllocationPie allocation={payload.allocation} />
      </div>
      <div className="fso-mission-control-command-row">
        <div className="fso-mission-control-judgment">
          <JudgmentHeader judgment={payload.judgment} />
        </div>
        <div className="fso-mission-control-brief" data-testid="mission-live-brief">
          <div>
            <span>Source</span>
            <strong>{state.sourceLabel}</strong>
            <small>
              {state.sourceDetail} · {generatedLabel}
            </small>
          </div>
          <div>
            <span>Total</span>
            <strong>{formatKrw(payload.portfolio.totalValue)}</strong>
            <small>Cash {formatKrw(payload.portfolio.cashValue)}</small>
          </div>
          <div>
            <span>Largest</span>
            <strong>{largestLabel}</strong>
            <small>{payload.portfolio.positionCount} positions</small>
          </div>
          <div>
            <span>Guards</span>
            <strong>{payload.systemStatus.guardCount}</strong>
            <small>{payload.goal.goalMode}</small>
          </div>
        </div>
        <div className="fso-mission-control-primary">
          <div data-testid="mission-goal-tracker">
            <MissionGoalTracker goal={payload.goal} />
          </div>
        </div>
      </div>
      <div className="fso-mission-control-state-band" data-testid="mission-state-band">
        <StateItem
          label="Source"
          value={state.sourceLabel}
          detail={state.sourceDetail}
          tone={state.sourceTone}
        />
        <StateItem
          label="Database"
          value={state.dbLabel}
          detail={state.dbDetail}
          tone={state.dbTone}
        />
        <StateItem
          label="Sector exposure"
          value={state.capitalLabel}
          detail={state.capitalDetail}
          tone={state.capitalTone}
        />
        <StateItem
          label="Theme exposure"
          value={state.themeLabel}
          detail={state.themeDetail}
          tone={state.themeTone}
        />
      </div>
      <div className="fso-mission-control-main-grid">
        <div className="fso-mission-control-stack">
          <div data-testid="mission-portfolio-snapshot">
            <PortfolioSnapshotPanel
              snapshot={payload.portfolio}
              reconciliation={payload.reconciliation}
              markDerived={payload.source === "live"}
            />
          </div>
          {payload.constraints && payload.constraints.length > 0 ? (
            <div data-testid="mission-constraint-summary">
              <ConstraintSummaryPanel constraints={payload.constraints} />
            </div>
          ) : null}
        </div>
        <div className="fso-mission-control-stack">
          <div data-testid="mission-milestone-timeline">
            <MilestoneTimeline milestones={payload.milestones} />
          </div>
        </div>
        <div className="fso-mission-control-stack">
          {payload.goal.earlyStopTriggered ? (
            <Panel
              title="Challenge Complete"
              badge="Early-Stop"
              badgeTone="success"
              testId="mission-challenge-complete"
            >
              <p>
                Challenge complete · early-stop state triggered. Continue
                in reflection-only mode.
              </p>
            </Panel>
          ) : null}
          <div
            className="fso-mission-control-exposure-grid"
            data-testid="mission-exposure-grid"
          >
            <div data-testid="mission-capital-map-sector">
              <CapitalMapPanel
                title="Sector Exposure"
                badge={state.capitalLabel}
                slices={payload.capitalMap}
                testId="capital-map"
              />
            </div>
            <div data-testid="mission-capital-map-theme-shell">
              <CapitalMapPanel
                title="Theme Exposure"
                badge={state.themeLabel}
                slices={payload.themeMap}
                testId="mission-capital-map-theme"
              />
            </div>
          </div>
        </div>
      </div>
      {/* v3 Phase 8 (183): the portfolio editor is a wide full-width row (a
          2-column form internally) instead of a tall narrow column that left the
          right half of the grid empty. */}
      <div
        className="fso-mission-control-editor-row"
        data-testid="mission-portfolio-editor"
      >
        <PortfolioEditorPanel
          positions={payload.positions ?? []}
          reconciliation={payload.reconciliation}
          totalValue={payload.portfolio.totalValue}
          cashValue={payload.portfolio.cashValue}
          editable={
            payload.source === "live" &&
            payload.systemStatus.db.toUpperCase() === "LIVE"
          }
          onMutated={(next) =>
            queryClient.setQueryData(["mission-control"], next)
          }
        />
        {/* v4 (229): Toss enrichment — names + descriptive risk flags on holdings. */}
        <TossHoldingsPanel
          tickers={(payload.positions ?? []).map((p) => p.ticker)}
        />
        {/* v3 Phase 11 (190): agent paste-import sits beside the editor. */}
        <AgentIngestPanel
          editable={
            payload.source === "live" &&
            payload.systemStatus.db.toUpperCase() === "LIVE"
          }
          onApplied={(next) =>
            queryClient.setQueryData(["mission-control"], next)
          }
        />
      </div>
      <div className="fso-mission-control-caption-row">
        <p
          className="fso-mission-control-caption"
          data-testid="mission-control-caption"
        >
          {payload.challengeStatusCaption}
        </p>
        <p
          className="fso-mission-control-safety"
          data-testid="mission-control-safety-caption"
        >
          {payload.safetyCaption}
        </p>
      </div>
      <MissionEvidenceDigest payload={payload} />
    </div>
  );
}

interface MissionControlState {
  sourceLabel: string;
  sourceDetail: string;
  sourceTone: BadgeTone;
  dbLabel: string;
  dbDetail: string;
  dbTone: BadgeTone;
  capitalLabel: string;
  capitalDetail: string;
  capitalTone: BadgeTone;
  themeLabel: string;
  themeDetail: string;
  themeTone: BadgeTone;
}

function buildMissionControlState(payload: MissionControlData): MissionControlState {
  const isLive = payload.source === "live";
  const dbLive = payload.systemStatus.db.toUpperCase() === "LIVE";
  const accountReady = payload.portfolio.positionCount > 0;
  const capitalCount = payload.capitalMap.length;
  const themeCount = payload.themeMap.length;

  return {
    sourceLabel: isLive ? "LIVE" : "FIXTURE",
    sourceDetail: isLive ? "DB-backed mission snapshot" : "Deterministic sample",
    sourceTone: isLive ? "success" : "warning",
    dbLabel: payload.systemStatus.db.toUpperCase(),
    dbDetail: dbLive ? "Session active" : "Fixture fallback",
    dbTone: dbLive ? "success" : "warning",
    capitalLabel: capitalCount > 0 ? `${capitalCount} rows` : "No rows",
    capitalDetail: accountReady
      ? "Sector map read from current holdings"
      : "Waiting for account holdings",
    capitalTone: capitalCount > 0 ? "info" : "neutral",
    themeLabel: themeCount > 0 ? `${themeCount} rows` : "No rows",
    themeDetail: accountReady
      ? "Theme map read from current holdings"
      : "Waiting for account holdings",
    themeTone: themeCount > 0 ? "info" : "neutral",
  };
}

interface StateItemProps {
  label: string;
  value: string;
  detail: string;
  tone: BadgeTone;
}

function StateItem({ label, value, detail, tone }: StateItemProps) {
  return (
    <div className="fso-mission-control-state-item">
      <span>{label}</span>
      <Badge tone={tone}>{value}</Badge>
      <small>{detail}</small>
    </div>
  );
}

function MissionEvidenceDigest({ payload }: { payload: MissionControlData }) {
  const firstDriver = payload.drivers[0];
  const firstConflict = payload.conflicts[0];
  const firstWatchpoint = payload.watchpoints[0];

  return (
    <section
      className="fso-mission-control-evidence-digest"
      data-testid="mission-evidence-digest"
      aria-label="Mission evidence digest"
    >
      <div className="fso-mission-control-digest-lead">
        <div>
          <span>Evidence Digest</span>
          <strong>{payload.interpretation.verdict}</strong>
        </div>
        <Badge tone="info">READ MODEL</Badge>
      </div>
      <div className="fso-mission-control-digest-grid">
        <EvidenceDigestItem
          label="Drivers"
          value={`${payload.drivers.length}`}
          title={firstDriver?.title ?? "No active drivers"}
          detail={
            firstDriver
              ? `${firstDriver.score} · ${firstDriver.note}`
              : "Awaiting evidence rows"
          }
          tone="info"
        />
        <EvidenceDigestItem
          label="Uncertainty"
          value={`${payload.conflicts.length}`}
          title={firstConflict?.title ?? "No conflicts logged"}
          detail={
            firstConflict?.note ?? payload.interpretation.whatRemainsUncertain
          }
          tone={payload.conflicts.length > 0 ? "warning" : "success"}
        />
        <EvidenceDigestItem
          label="Review"
          value={`${payload.watchpoints.length}`}
          title={firstWatchpoint?.title ?? "No watchpoints logged"}
          detail={firstWatchpoint?.note ?? payload.interpretation.whyItMatters}
          tone="info"
        />
      </div>
      <p className="fso-mission-control-digest-context">
        {payload.interpretation.whyItMatters}
      </p>
    </section>
  );
}

interface EvidenceDigestItemProps {
  label: string;
  value: string;
  title: string;
  detail: string;
  tone: BadgeTone;
}

function EvidenceDigestItem({
  label,
  value,
  title,
  detail,
  tone,
}: EvidenceDigestItemProps) {
  return (
    <article className="fso-mission-control-digest-item">
      <div className="fso-mission-control-digest-item-heading">
        <span>{label}</span>
        <Badge tone={tone}>{value}</Badge>
      </div>
      <strong>{title}</strong>
      <small>{detail}</small>
    </article>
  );
}
