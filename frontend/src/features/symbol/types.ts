import type { Numeric } from "@/shared/lib/format";
import type {
  IndicatorSnapshot,
  UniverseTicker,
} from "@/features/market/kernel-types";
import type { RegimeContext } from "@/features/analysis/types";
import type {
  EvidenceConflictData,
  EvidenceDriverData,
  EvidenceWatchpointData,
  IntegratedInterpretationData,
  JudgmentHeaderData,
} from "@/shared/types/evidence";

export type DataStatus = "OK" | "PARTIAL" | "MISSING";

export interface SymbolPosition {
  ticker: string;
  sector: string | null;
  theme: string | null;
  strategyType: string | null;
  marketValue: Numeric | null;
  portfolioWeight: Numeric | null;
  pnlPct: Numeric | null;
  quantity: Numeric | null;
  thesis: string | null;
  overSinglePositionLimit: boolean;
}

export interface SymbolRecentBar {
  barTime: string;
  open: Numeric | null;
  high: Numeric | null;
  low: Numeric | null;
  close: Numeric;
  volume: Numeric | null;
  ema20?: Numeric | null;
  ema60?: Numeric | null;
  ema120?: Numeric | null;
  bbMid?: Numeric | null;
  bbUpper?: Numeric | null;
  bbLower?: Numeric | null;
}

export interface SymbolAlert {
  guardName: string;
  severity: string;
  title: string;
  message: string;
  alertDate: string;
}

export interface SymbolNewsItem {
  title: string;
  source: string;
  publishedAt: string;
  sentimentLabel: string;
  impactScore: Numeric;
  riskNote: string | null;
  url: string;
}

export interface SymbolLabHeader {
  ticker: string;
  timeframe: string;
  latestClose: Numeric | null;
  latestTime: string | null;
  dataStatus: DataStatus;
}

export interface SymbolIdentity {
  ticker: string;
  name: string;
  logoUrl: string | null;
  logoSource: "local_fallback" | "provider_cache" | "deferred";
  avatarText: string;
  brandColor: string;
}

export interface SymbolSubscriptionState {
  isSubscribed: boolean;
  canSubscribe: boolean;
  updateUniverseMember: boolean;
  lastAction: "none" | "subscribed" | "unsubscribed";
}

export interface SymbolSubscriptionFolderMember {
  ticker: string;
  name: string | null;
}

export interface SymbolSubscriptionFolder {
  id: string;
  name: string;
  description: string | null;
  sortOrder: number;
  members: SymbolSubscriptionFolderMember[];
}

export interface SymbolSubscriptionFolderList {
  folders: SymbolSubscriptionFolder[];
}

export interface SymbolLabSystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export interface SymbolLabData {
  generatedAt: string;
  systemStatus: SymbolLabSystemStatus;
  judgment: JudgmentHeaderData;
  drivers: EvidenceDriverData[];
  conflicts: EvidenceConflictData[];
  integratedInterpretation: IntegratedInterpretationData;
  reviewWatchpoints: EvidenceWatchpointData[];
  symbolUniverse: UniverseTicker[];
  identity: SymbolIdentity;
  subscription: SymbolSubscriptionState;
  header: SymbolLabHeader;
  technical: IndicatorSnapshot;
  recentBars: SymbolRecentBar[];
  position: SymbolPosition | null;
  alerts: SymbolAlert[];
  news: SymbolNewsItem[];
  regime: RegimeContext | null;
  watchpoints: string[];
  interpretation: string;
  setupHint: string | null;
  safetyCaption: string;
  source: "fixture" | "live";
}
