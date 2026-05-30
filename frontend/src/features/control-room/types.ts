import type {
  MissionProgress,
  PortfolioExposureSlice,
  ReviewQueueItem,
} from "@/features/portfolio/types";
import type { OperatingState } from "@/features/regime/types";
import type { GuardSummary } from "@/features/risk-guards/types";
import type { CatalystSummary } from "@/features/events/types";
import type {
  MarketTapePoint,
  TickerStripItem,
  WatchlistItem,
} from "@/features/market/types";
import type {
  EvidenceConflictData,
  EvidenceDriverData,
  EvidenceWatchpointData,
  IntegratedInterpretationData,
  JudgmentHeaderData,
} from "@/shared/types/evidence";

export interface ControlRoomSystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export type ControlRoomDataStatus = "OK" | "PARTIAL" | "MISSING";
export type ControlRoomFreshnessStatus = "FRESH" | "STALE" | "MISSING";

export interface ControlRoomDataState {
  source: "fixture" | "live";
  overviewStatus: ControlRoomDataStatus;
  systemStatus: ControlRoomDataStatus;
  missionStatus: ControlRoomDataStatus;
  marketTapeStatus: ControlRoomDataStatus;
  guardStatus: ControlRoomDataStatus;
  catalystStatus: ControlRoomDataStatus;
  watchlistStatus: ControlRoomDataStatus;
  marketTapePoints: number;
  guardCount: number;
  catalystCount: number;
  watchlistCount: number;
  latestMarketAt: string | null;
  latestEventAt: string | null;
  latestWatchlistAt: string | null;
  marketFreshnessStatus: ControlRoomFreshnessStatus;
  catalystFreshnessStatus: ControlRoomFreshnessStatus;
  watchlistFreshnessStatus: ControlRoomFreshnessStatus;
  railFreshnessStatus: ControlRoomFreshnessStatus;
  railFreshnessNote: string;
  marketStaleAfterDays: number;
  watchlistStaleAfterDays: number;
  sourceNote: string;
  refreshNote: string;
}

export interface ControlRoomData {
  generatedAt: string;
  systemStatus: ControlRoomSystemStatus;
  dataState: ControlRoomDataState;
  judgment: JudgmentHeaderData;
  drivers: EvidenceDriverData[];
  conflicts: EvidenceConflictData[];
  interpretation: IntegratedInterpretationData;
  watchpoints: EvidenceWatchpointData[];
  safetyCaption: string;
  tickerStrip: TickerStripItem[];
  mission: MissionProgress;
  operatingState: OperatingState;
  portfolioExposure: PortfolioExposureSlice[];
  reviewQueue: ReviewQueueItem[];
  interpretationCards: string[];
  riskFirewall: GuardSummary[];
  catalystWatch: CatalystSummary[];
  watchlist: WatchlistItem[];
  marketTape: MarketTapePoint[];
  source: "fixture" | "live";
}
