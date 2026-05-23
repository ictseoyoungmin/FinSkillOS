import { useQuery } from "@tanstack/react-query";
import { fetchEventRadar } from "@/features/events/api";
import { EventExposureJudgment } from "@/features/events/components/EventExposureJudgment";
import { EventLinkedNewsPanel } from "@/features/events/components/EventLinkedNewsPanel";
import { EventRiskTable } from "@/features/events/components/EventRiskTable";
import { EventScoreDrivers } from "@/features/events/components/EventScoreDrivers";
import { HighRiskEventsPanel } from "@/features/events/components/HighRiskEventsPanel";
import { HoldingsLinkedEventsPanel } from "@/features/events/components/HoldingsLinkedEventsPanel";
import { ManualEventEntry } from "@/features/events/components/ManualEventEntry";
import { eventRadarFixture } from "@/mocks/fixtures/eventRadar.fixture";
import {
  ConflictsPanel,
  EmptyState,
  InterpretationPanel,
  SafetyCaption,
  SectionHeader,
  WatchpointsPanel,
} from "@/shared/ui";
import "./catalyst-watch.css";

export function CatalystWatchPage() {
  const { data, error } = useQuery({
    queryKey: ["event-radar"],
    queryFn: ({ signal }) => fetchEventRadar(signal),
    placeholderData: eventRadarFixture,
  });

  if (error && !data) {
    return (
      <EmptyState
        testId="catalyst-watch-error"
        title="Catalyst Watch is unavailable"
        message={
          "The API is unreachable and no fixture is cached. " +
          "Check the FastAPI container and reload."
        }
      />
    );
  }

  const payload = data ?? eventRadarFixture;

  return (
    <div className="fso-catalyst-watch" data-testid="catalyst-watch-page">
      <SectionHeader eyebrow="FinSkillOS · Module" title="Catalyst Watch" />
      <EventExposureJudgment judgment={payload.judgment} />
      <div className="fso-catalyst-watch-grid">
        <div className="fso-catalyst-watch-col">
          <div data-testid="event-score-drivers">
            <EventScoreDrivers drivers={payload.drivers} />
          </div>
          <EventRiskTable
            title="Upcoming Events"
            events={payload.upcoming}
            toneMap={payload.dateStatusBadgeTone}
            testId="event-risk-table"
          />
          <div className="fso-date-status-badges" data-testid="date-status-badges">
            {Object.keys(payload.dateStatusBadgeTone).join(" · ")}
          </div>
          <HighRiskEventsPanel
            events={payload.highRisk}
            toneMap={payload.dateStatusBadgeTone}
          />
          <HoldingsLinkedEventsPanel
            events={payload.holdingsLinked}
            toneMap={payload.dateStatusBadgeTone}
          />
          <EventLinkedNewsPanel articles={payload.linkedNews} />
        </div>
        <div className="fso-catalyst-watch-col">
          <ConflictsPanel conflicts={payload.conflicts} />
          <InterpretationPanel
            bullets={payload.integratedInterpretation}
          />
          <WatchpointsPanel
            watchpoints={payload.watchpoints}
            title="Watchpoints"
          />
          <ManualEventEntry rules={payload.manualEntryRules} />
        </div>
      </div>
      <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
    </div>
  );
}
