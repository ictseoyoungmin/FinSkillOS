import type { Numeric } from "@/shared/lib/format";

export type TickerDirection = "up" | "down" | "flat";

export interface TickerStripItem {
  symbol: string;
  price: string;
  change: string;
  direction: TickerDirection;
  currency: string;
  logoUrl: string | null;
  held: boolean;
}

export interface WatchlistItem {
  symbol: string;
  label: string;
  note: string;
  tone: "info" | "warning" | "danger" | "neutral" | "success";
}

export interface MarketTapePoint {
  label: string;
  portfolio: Numeric;
  benchmark: Numeric;
}
