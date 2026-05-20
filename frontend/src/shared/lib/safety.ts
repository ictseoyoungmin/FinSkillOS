/**
 * Slice 13.6 safety contract — keep the React shell descriptive-only.
 *
 * `FORBIDDEN_CONTROL_LABELS` is consumed by the e2e tests; any button /
 * command palette entry whose visible text matches one of these is a
 * regression — the product UI must not surface execution controls.
 */

export const FORBIDDEN_CONTROL_LABELS: readonly string[] = Object.freeze([
  "Buy",
  "Sell",
  "Execute",
  "Trade Now",
  "Order",
  "Place Order",
  "지금 사라",
  "지금 팔아라",
  "매수 버튼",
  "매도 버튼",
]);

export const ALLOWED_DISCLAIMER_PHRASES: readonly string[] = Object.freeze([
  "No execution controls",
  "Not prediction",
  "Read mode",
  "Stored data only",
]);
