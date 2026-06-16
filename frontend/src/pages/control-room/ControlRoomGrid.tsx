import { EvidenceGraphPanel } from "@/features/control-room/components/EvidenceGraphPanel";
import { AllocationPie } from "@/features/portfolio/components/AllocationPie";
import { GoalProgressCard } from "@/features/portfolio/components/GoalProgressCard";
import { ReviewQueueCard } from "@/features/portfolio/components/ReviewQueueCard";
import { OperatingStateHero } from "@/features/regime/components/OperatingStateHero";
import { RegimeStateVector } from "@/features/regime/components/RegimeStateVector";
import { InterpretationCards } from "@/features/regime/components/InterpretationCards";
import { GuardStack } from "@/features/risk-guards/components/GuardStack";
import { CatalystListCard } from "@/features/events/components/CatalystListCard";
import { WatchlistCard } from "@/features/market/components/WatchlistCard";
import { PortfolioMarketTapePanel } from "@/features/market/components/PortfolioMarketTapePanel";
import {
  Badge,
  type BadgeTone,
  ConflictsPanel,
  DriversPanel,
  InterpretationPanel,
  JudgmentHeader,
  SafetyCaption,
  SectionHeader,
  StatusPill,
  WatchpointsPanel,
} from "@/shared/ui";
import type {
  ControlRoomData,
  ControlRoomDataState,
  ControlRoomDataStatus,
} from "@/features/control-room/types";
import "./control-room-grid.css";

export interface ControlRoomGridProps {
  data: ControlRoomData;
  liveFailed?: boolean;
}

export function ControlRoomGrid({
  data,
  liveFailed = false,
}: ControlRoomGridProps) {
  return (
    <div className="fso-control-room" data-testid="control-room-grid">
      {liveFailed ? (
        <StatusPill
          label="Live data unavailable — showing sample shape, not live data"
          tone="warning"
          testId="control-room-live-failed"
        />
      ) : null}
      <SectionHeader
        eyebrow="FinSkillOS · Module"
        title="Control Room"
      />
      <div className="fso-v42-topline">
        <JudgmentHeader judgment={data.judgment} />
        <DriversPanel
          drivers={data.drivers.map((driver) => ({
            label: driver.title,
            value: driver.score,
            detail: driver.note,
          }))}
        />
        <ConflictsPanel
          conflicts={data.conflicts.map((conflict) => ({
            label: conflict.title,
            description: conflict.note,
          }))}
        />
      </div>
      <ControlRoomStateBand dataState={data.dataState} />
      <div className="fso-control-grid">
        <section
          className="fso-control-column"
          data-testid="control-room-left"
          aria-label="Mission · Portfolio · Review"
        >
          <GoalProgressCard mission={data.mission} />
          <AllocationPie allocation={data.allocation} />
          <ReviewQueueCard items={data.reviewQueue} />
        </section>

        <section
          className="fso-control-column fso-control-column--center"
          data-testid="control-room-center"
          aria-label="Operating State · Vector · Tape · Interpretation"
        >
          <OperatingStateHero state={data.operatingState} />
          <RegimeStateVector state={data.operatingState} />
          <PortfolioMarketTapePanel
            points={data.marketTape}
            badge={
              data.dataState.marketTapeStatus === "OK"
                ? "Live DB"
                : "No stored tape"
            }
          />
          <InterpretationCards cards={data.interpretationCards} />
          {/* v3 Phase 8 (182): the evidence graph + interpretation + watchpoints
              flow inside the (widest) center column so it fills the vertical
              space beside the taller Risk-Firewall rail instead of leaving a
              void and pushing these sections far below the fold. */}
          {data.evidenceGraph && data.evidenceGraph.nodes.length > 0 ? (
            <EvidenceGraphPanel graph={data.evidenceGraph} />
          ) : null}
          <InterpretationPanel
            bullets={[
              data.interpretation.verdict,
              data.interpretation.whyItMatters,
              data.interpretation.whatRemainsUncertain,
            ]}
          />
          <WatchpointsPanel
            watchpoints={data.watchpoints.map((watchpoint) => ({
              label: watchpoint.title,
              description: watchpoint.note,
            }))}
          />
        </section>

        <section
          className="fso-control-column"
          data-testid="control-room-right"
          aria-label="Risk Firewall · Catalysts · Watchlist"
        >
          <GuardStack guards={data.riskFirewall} />
          <CatalystListCard events={data.catalystWatch} />
          <WatchlistCard items={data.watchlist} />
        </section>
      </div>
      <SafetyCaption>{data.safetyCaption}</SafetyCaption>
    </div>
  );
}

function ControlRoomStateBand({
  dataState,
}: {
  dataState: ControlRoomDataState;
}) {
  const catalystDetail = [
    `${dataState.catalystCount} catalysts`,
    dataState.catalystFreshnessStatus.toLowerCase(),
    formatFreshness(dataState.latestEventAt),
  ].join(" ");
  const watchlistDetail = [
    `${dataState.watchlistCount} watchlist`,
    dataState.watchlistFreshnessStatus.toLowerCase(),
    formatFreshness(dataState.latestWatchlistAt),
  ].join(" ");

  return (
    <div
      className="fso-control-state-band"
      data-testid="control-room-state-band"
    >
      <ControlRoomStateItem
        label="Overview Source"
        value={dataState.source === "live" ? "Live" : "Fixture"}
        detail={dataState.sourceNote}
        tone={dataState.source === "live" ? "success" : "warning"}
      />
      <ControlRoomStateItem
        label="Evidence Coverage"
        value={dataState.overviewStatus}
        detail={[
          `Mission ${dataState.missionStatus}`,
          `System ${dataState.systemStatus}`,
        ].join(" · ")}
        tone={dataStatusTone(dataState.overviewStatus)}
      />
      <ControlRoomStateItem
        label="Market Tape"
        value={dataState.marketTapeStatus}
        detail={[
          `${dataState.marketTapePoints} normalized points`,
          dataState.marketFreshnessStatus.toLowerCase(),
          formatFreshness(dataState.latestMarketAt),
        ].join(" · ")}
        tone={dataStatusTone(dataState.marketTapeStatus)}
      />
      <ControlRoomStateItem
        label="Linked Modules"
        value={moduleStatus(dataState)}
        detail={[
          `${dataState.guardCount} guards`,
          catalystDetail,
          watchlistDetail,
        ].join(" · ")}
        tone={moduleTone(dataState)}
      />
      <ControlRoomStateItem
        label="Rail Freshness"
        value={dataState.railFreshnessStatus}
        detail={dataState.railFreshnessNote}
        tone={freshnessTone(dataState.railFreshnessStatus)}
      />
    </div>
  );
}

function formatFreshness(value: string | null): string {
  if (!value) {
    return "missing";
  }
  return value.slice(0, 10);
}

function freshnessTone(
  status: ControlRoomDataState["railFreshnessStatus"],
): BadgeTone {
  if (status === "FRESH") {
    return "success";
  }
  if (status === "STALE") {
    return "warning";
  }
  return "danger";
}

function ControlRoomStateItem({
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
    <div className="fso-control-state-item">
      <span>{label}</span>
      <Badge tone={tone}>{value}</Badge>
      <small>{detail}</small>
    </div>
  );
}

function dataStatusTone(status: ControlRoomDataStatus): BadgeTone {
  if (status === "OK") {
    return "success";
  }
  if (status === "PARTIAL") {
    return "warning";
  }
  return "danger";
}

function moduleTone(dataState: ControlRoomDataState): BadgeTone {
  return dataStatusTone(moduleStatus(dataState));
}

function moduleStatus(dataState: ControlRoomDataState): ControlRoomDataStatus {
  const statuses = [
    dataState.guardStatus,
    dataState.catalystStatus,
    dataState.watchlistStatus,
  ];
  if (statuses.every((status) => status === "OK")) {
    return "OK";
  }
  if (statuses.some((status) => status === "MISSING")) {
    return "MISSING";
  }
  return "PARTIAL";
}
