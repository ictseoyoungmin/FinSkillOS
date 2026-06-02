export type CollectionFlag =
  | "is_active"
  | "track_market"
  | "track_indicators"
  | "track_news";

export interface CollectionFolderMember {
  ticker: string;
  name: string | null;
}

export interface CollectionFolder {
  id: string;
  name: string;
  description: string | null;
  sortOrder: number;
  isSystem: boolean;
  isActive: boolean;
  trackMarket: boolean;
  trackIndicators: boolean;
  trackNews: boolean;
  memberCount: number;
  members: CollectionFolderMember[];
}

export interface CollectionTotals {
  folderCount: number;
  activeFolderCount: number;
  marketTickerCount: number;
  indicatorTickerCount: number;
  newsTickerCount: number;
  allActive: boolean;
  marketAll: boolean;
  indicatorsAll: boolean;
  newsAll: boolean;
}

export interface CollectionControlData {
  generatedAt: string;
  systemStatus: { db: string; mode: string; guardCount: number };
  source: "fixture" | "live";
  folders: CollectionFolder[];
  totals: CollectionTotals;
  safetyCaption: string;
}

export interface CollectionFlagPatch {
  isActive?: boolean;
  trackMarket?: boolean;
  trackIndicators?: boolean;
  trackNews?: boolean;
}
