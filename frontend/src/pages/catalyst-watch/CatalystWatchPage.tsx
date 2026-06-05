import { useQuery } from "@tanstack/react-query";
import { fetchEventRadar } from "@/features/events/api";
import { EventExposureJudgment } from "@/features/events/components/EventExposureJudgment";
import { EventLinkedNewsPanel } from "@/features/events/components/EventLinkedNewsPanel";
import { EventRiskTable } from "@/features/events/components/EventRiskTable";
import { EventScoreDrivers } from "@/features/events/components/EventScoreDrivers";
import { HighRiskEventsPanel } from "@/features/events/components/HighRiskEventsPanel";
import { HoldingsLinkedEventsPanel } from "@/features/events/components/HoldingsLinkedEventsPanel";
import { eventRadarFixture } from "@/mocks/fixtures/eventRadar.fixture";
import {
  Badge,
  ConflictsPanel,
  EmptyState,
  InterpretationPanel,
  Panel,
  SafetyCaption,
  SectionHeader,
  StatusPill,
  WatchpointsPanel,
} from "@/shared/ui";
import type { BadgeTone } from "@/shared/ui/Badge";
import type { EventRadarData } from "@/features/events/types";
import "./catalyst-watch.css";

export function CatalystWatchPage() {
  const { data, error, failureReason } = useQuery({
    queryKey: ["event-radar"],
    queryFn: ({ signal }) => fetchEventRadar(signal),
    placeholderData: eventRadarFixture,
  });
  const liveFailed = Boolean(error ?? failureReason);

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
      {liveFailed ? (
        <StatusPill
          label="Live data unavailable — showing sample shape, not live data"
          tone="warning"
          testId="catalyst-watch-live-failed"
        />
      ) : null}
      <SectionHeader eyebrow="FinSkillOS · Module" title="Catalyst Watch" />
      <div className="fso-v42-topline">
        <EventExposureJudgment judgment={payload.judgment} />
        <div data-testid="event-score-drivers">
          <EventScoreDrivers drivers={payload.drivers} />
        </div>
        <ConflictsPanel conflicts={payload.conflicts} />
      </div>
      <CatalystDataStateBand payload={payload} />
      <div className="fso-catalyst-watch-grid">
        <div className="fso-catalyst-watch-col">
          <div data-testid="event-upcoming">
            <div data-testid="event-upcoming-table">
              <EventRiskTable
                title="Upcoming Events"
                events={payload.upcoming}
                toneMap={payload.dateStatusBadgeTone}
                testId="event-risk-table"
              />
            </div>
          </div>
          <HighRiskEventsPanel
            events={payload.highRisk}
            toneMap={payload.dateStatusBadgeTone}
          />
          <HoldingsLinkedEventsPanel
            events={payload.holdingsLinked}
            toneMap={payload.dateStatusBadgeTone}
          />
        </div>
        <div className="fso-catalyst-watch-col">
          <InterpretationPanel
            bullets={payload.integratedInterpretation}
          />
          <WatchpointsPanel
            watchpoints={payload.watchpoints}
            title="Watchpoints"
          />
          <EventCatalogEvidence payload={payload} />
          {/* v3 Phase 8 (183): the long linked-news list fills the side column
              beside the taller event tables instead of stretching col 1. */}
          <EventLinkedNewsPanel articles={payload.linkedNews} />
        </div>
      </div>
      <div data-testid="catalyst-watch-safety-caption">
        <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
      </div>
    </div>
  );
}

function EventCatalogEvidence({ payload }: { payload: EventRadarData }) {
  const state = payload.dataState;
  const catalogBadge =
    state.calendarStatus === "db_backed"
      ? "DB-backed"
      : state.calendarStatus === "empty"
        ? "Live empty"
        : "Fixture";

  return (
    <Panel
      title="Event Catalog Evidence"
      badge={catalogBadge}
      badgeTone={state.calendarStatus === "db_backed" ? "success" : "warning"}
      testId="event-catalog-evidence"
    >
      <div className="fso-event-catalog-grid">
        <EventCatalogMetric
          label="Calendar rows"
          value={`${state.eventCount}`}
          detail={state.calendarDetail}
        />
        <EventCatalogMetric
          label="Confirmed dates"
          value={`${state.confirmedCount}`}
          detail={state.dateConfidenceDetail}
        />
        <EventCatalogMetric
          label="Uncertain dates"
          value={`${state.uncertainCount}`}
          detail="Tentative, reported, window, and speculative events."
        />
        <EventCatalogMetric
          label="Linked news"
          value={`${state.linkedNewsCount}`}
          detail="Stored metadata linked to event exposure rows."
        />
      </div>
      <p className="fso-event-catalog-note">
        Event catalog rows are read from stored fixture or DB-backed evidence.
        New event ingestion belongs in provider or System Ops workflows, not the
        Catalyst Watch review surface.
      </p>
    </Panel>
  );
}

function EventCatalogMetric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="fso-event-catalog-metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function CatalystDataStateBand({ payload }: { payload: EventRadarData }) {
  const state = payload.dataState;
  const sourceLabel =
    state.calendarStatus === "db_backed" ? "LIVE" : "FIXTURE";
  const sourceTone: BadgeTone =
    state.calendarStatus === "db_backed" ? "success" : "warning";
  const confidenceTone: BadgeTone = dateConfidenceTone(
    state.dateConfidenceStatus,
  );
  const nearestLabel =
    state.nearestEventDays === null ? "No event" : `T-${state.nearestEventDays}`;

  return (
    <div
      className="fso-catalyst-state-band"
      data-testid="catalyst-data-state"
    >
      <CatalystStateItem
        label="Calendar source"
        value={sourceLabel}
        detail={state.calendarDetail}
        tone={sourceTone}
      />
      <CatalystStateItem
        label="Date confidence"
        value={state.dateConfidenceStatus.toUpperCase()}
        detail={state.dateConfidenceDetail}
        tone={confidenceTone}
      />
      <CatalystStateItem
        label="Event rows"
        value={`${state.eventCount}`}
        detail={`${nearestLabel} nearest · ${state.linkedNewsCount} linked news`}
        tone={state.eventCount > 0 ? "info" : "neutral"}
      />
      <CatalystStateItem
        label="DB / mode"
        value={payload.systemStatus.db.toUpperCase()}
        detail={`${payload.systemStatus.mode} · ${state.sourceNote}`}
        tone={
          payload.systemStatus.db.toUpperCase() === "LIVE"
            ? "success"
            : "warning"
        }
      />
    </div>
  );
}

function dateConfidenceTone(
  status: EventRadarData["dataState"]["dateConfidenceStatus"],
): BadgeTone {
  if (status === "confirmed") {
    return "success";
  }
  if (status === "mixed") {
    return "info";
  }
  if (status === "uncertain") {
    return "warning";
  }
  return "neutral";
}

interface CatalystStateItemProps {
  label: string;
  value: string;
  detail: string;
  tone: BadgeTone;
}

function CatalystStateItem({
  label,
  value,
  detail,
  tone,
}: CatalystStateItemProps) {
  return (
    <div className="fso-catalyst-state-item">
      <span>{label}</span>
      <Badge tone={tone}>{value}</Badge>
      <small>{detail}</small>
    </div>
  );
}
