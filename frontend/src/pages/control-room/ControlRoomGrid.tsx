import { GoalProgressCard } from "@/features/portfolio/components/GoalProgressCard";
import { PortfolioExposureCard } from "@/features/portfolio/components/PortfolioExposureCard";
import { ReviewQueueCard } from "@/features/portfolio/components/ReviewQueueCard";
import { OperatingStateHero } from "@/features/regime/components/OperatingStateHero";
import { RegimeStateVector } from "@/features/regime/components/RegimeStateVector";
import { InterpretationCards } from "@/features/regime/components/InterpretationCards";
import { GuardStack } from "@/features/risk-guards/components/GuardStack";
import { CatalystListCard } from "@/features/events/components/CatalystListCard";
import { WatchlistCard } from "@/features/market/components/WatchlistCard";
import { PortfolioMarketTapePanel } from "@/features/market/components/PortfolioMarketTapePanel";
import {
  ConflictsPanel,
  DriversPanel,
  InterpretationPanel,
  JudgmentHeader,
  SafetyCaption,
  SectionHeader,
  WatchpointsPanel,
} from "@/shared/ui";
import type { ControlRoomData } from "@/features/control-room/types";
import "./control-room-grid.css";

export interface ControlRoomGridProps {
  data: ControlRoomData;
}

export function ControlRoomGrid({ data }: ControlRoomGridProps) {
  return (
    <div className="fso-control-room" data-testid="control-room-grid">
      <SectionHeader
        eyebrow="FinSkillOS · Module"
        title="Control Room"
      />
      <JudgmentHeader judgment={data.judgment} />
      <div className="fso-control-evidence-row">
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
      <div className="fso-control-grid">
        <section
          className="fso-control-column"
          data-testid="control-room-left"
          aria-label="Mission · Portfolio · Review"
        >
          <GoalProgressCard mission={data.mission} />
          <PortfolioExposureCard slices={data.portfolioExposure} />
          <ReviewQueueCard items={data.reviewQueue} />
        </section>

        <section
          className="fso-control-column fso-control-column--center"
          data-testid="control-room-center"
          aria-label="Operating State · Vector · Tape · Interpretation"
        >
          <OperatingStateHero state={data.operatingState} />
          <RegimeStateVector state={data.operatingState} />
          <PortfolioMarketTapePanel points={data.marketTape} badge="90D · Fixture" />
          <InterpretationCards cards={data.interpretationCards} />
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
      <SafetyCaption>{data.safetyCaption}</SafetyCaption>
    </div>
  );
}
