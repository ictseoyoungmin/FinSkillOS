import { useQuery } from "@tanstack/react-query";
import { fetchMissionControl } from "@/features/portfolio/api";
import { CapitalMapPanel } from "@/features/portfolio/components/CapitalMapPanel";
import { MilestoneTimeline } from "@/features/portfolio/components/MilestoneTimeline";
import { MissionGoalTracker } from "@/features/portfolio/components/MissionGoalTracker";
import { PortfolioSnapshotPanel } from "@/features/portfolio/components/PortfolioSnapshotPanel";
import { missionControlFixture } from "@/mocks/fixtures/missionControl.fixture";
import { formatKrw, formatPct } from "@/shared/lib/format";
import {
  ConflictsPanel,
  DriversPanel,
  EmptyState,
  InterpretationPanel,
  JudgmentHeader,
  Panel,
  SectionHeader,
  WatchpointsPanel,
} from "@/shared/ui";
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
            <strong>{payload.source.toUpperCase()}</strong>
            <small>
              DB {payload.systemStatus.db} · {generatedLabel}
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
                badge="Sector"
                slices={payload.capitalMap}
                testId="capital-map"
              />
            </div>
            {payload.themeMap.length > 0 ? (
              <CapitalMapPanel
                title="Theme Exposure"
                badge="Theme"
                slices={payload.themeMap}
                testId="mission-capital-map-theme"
              />
            ) : null}
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
