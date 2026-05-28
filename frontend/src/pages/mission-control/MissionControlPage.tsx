import { useQuery } from "@tanstack/react-query";
import { fetchMissionControl } from "@/features/portfolio/api";
import { CapitalMapPanel } from "@/features/portfolio/components/CapitalMapPanel";
import { MilestoneTimeline } from "@/features/portfolio/components/MilestoneTimeline";
import { MissionGoalTracker } from "@/features/portfolio/components/MissionGoalTracker";
import { PortfolioSnapshotPanel } from "@/features/portfolio/components/PortfolioSnapshotPanel";
import { missionControlFixture } from "@/mocks/fixtures/missionControl.fixture";
import { formatKrw, formatPct } from "@/shared/lib/format";
import {
  Badge,
  ConflictsPanel,
  DriversPanel,
  EmptyState,
  InterpretationPanel,
  JudgmentHeader,
  Panel,
  SectionHeader,
  WatchpointsPanel,
} from "@/shared/ui";
import type { BadgeTone } from "@/shared/ui/Badge";
import type { MissionControlData } from "@/features/portfolio/types";
import "./mission-control.css";

export function MissionControlPage() {
  const { data, error } = useQuery({
    queryKey: ["mission-control"],
    queryFn: ({ signal }) => fetchMissionControl(signal),
    placeholderData: missionControlFixture,
  });

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
      <SectionHeader eyebrow="FinSkillOS · Module" title="Mission Control" />
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
            <PortfolioSnapshotPanel snapshot={payload.portfolio} />
          </div>
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
      <div className="fso-mission-control-evidence-grid">
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
      </div>
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
