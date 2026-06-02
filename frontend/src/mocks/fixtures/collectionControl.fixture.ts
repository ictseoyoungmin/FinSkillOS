import type { CollectionControlData } from "@/features/collection-control/types";

const SYSTEM_MEMBERS = [
  "SPY",
  "QQQ",
  "DIA",
  "IWM",
  "SMH",
  "SOXX",
  "XLK",
  "XLF",
  "XLE",
  "XLV",
  "XLI",
  "XLY",
  "XLP",
  "XLU",
  "NVDA",
  "TSLA",
  "AAPL",
  "MSFT",
  "AMZN",
  "VIX",
  "US10Y",
  "DXY",
].map((ticker) => ({ ticker, name: ticker }));

export const collectionControlFixture: CollectionControlData = {
  generatedAt: "2026-01-01T00:00:00+00:00",
  systemStatus: { db: "LIVE", mode: "READ_MODE", guardCount: 0 },
  source: "fixture",
  folders: [
    {
      id: "00000000-0000-0000-0000-000000000001",
      name: "System",
      description: "Install-default sector leaders tracked out of the box.",
      sortOrder: 0,
      isSystem: true,
      isActive: true,
      trackMarket: true,
      trackIndicators: true,
      trackNews: true,
      memberCount: SYSTEM_MEMBERS.length,
      members: SYSTEM_MEMBERS,
    },
  ],
  totals: {
    folderCount: 1,
    activeFolderCount: 1,
    marketTickerCount: SYSTEM_MEMBERS.length,
    indicatorTickerCount: SYSTEM_MEMBERS.length,
    newsTickerCount: SYSTEM_MEMBERS.length,
    allActive: true,
    marketAll: true,
    indicatorsAll: true,
    newsAll: true,
  },
  safetyCaption:
    "Collection control is descriptive-only. Toggles decide which symbols the " +
    "worker observes; no orders or trade actions are ever placed.",
};
