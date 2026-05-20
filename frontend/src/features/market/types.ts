export type TickerDirection = "up" | "down" | "flat";

export interface TickerStripItem {
  symbol: string;
  price: string;
  change: string;
  direction: TickerDirection;
}

export interface WatchlistItem {
  symbol: string;
  label: string;
  note: string;
  tone: "info" | "warning" | "danger" | "neutral" | "success";
}
