import { useQuery } from "@tanstack/react-query";
import { fetchMissionControl } from "@/features/portfolio/api";
import { CapitalMapPanel } from "@/features/portfolio/components/CapitalMapPanel";
import { MilestoneTimeline } from "@/features/portfolio/components/MilestoneTimeline";
import { MissionGoalTracker } from "@/features/portfolio/components/MissionGoalTracker";
import { PortfolioSnapshotPanel } from "@/features/portfolio/components/PortfolioSnapshotPanel";
import { missionControlFixture } from "@/mocks/fixtures/missionControl.fixture";
import { EmptyState, Panel, SectionHeader } from "@/shared/ui";
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

  return (
    <div className="fso-mission-control" data-testid="mission-control-page">
      <SectionHeader eyebrow="FinSkillOS · Module" title="Mission Control" />
      <div className="fso-mission-control-grid">
        <div className="fso-mission-control-col">
          <MissionGoalTracker goal={payload.goal} />
          <MilestoneTimeline milestones={payload.milestones} />
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
        </div>
        <div className="fso-mission-control-col">
          <PortfolioSnapshotPanel snapshot={payload.portfolio} />
          <CapitalMapPanel
            title="Sector Exposure"
            badge="Sector"
            slices={payload.capitalMap}
            testId="mission-capital-map-sector"
          />
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
  );
}
