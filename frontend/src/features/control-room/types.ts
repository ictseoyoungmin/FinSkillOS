import type {
  MissionProgress,
  PortfolioExposureSlice,
  ReviewQueueItem,
} from "@/features/portfolio/types";
import type { OperatingState } from "@/features/regime/types";
import type { GuardSummary } from "@/features/risk-guards/types";
import type { CatalystSummary } from "@/features/events/types";
import type { TickerStripItem, WatchlistItem } from "@/features/market/types";
import type { MarketTapePoint } from "@/features/market/components/PortfolioMarketTapePanel";

export interface ControlRoomSystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export interface ControlRoomData {
  generatedAt: string;
  systemStatus: ControlRoomSystemStatus;
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
