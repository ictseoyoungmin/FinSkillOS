/** Number / percent / currency formatters used across the cockpit. */

/**
 * Numeric values cross the API / JSON boundary as either `number` or
 * `string` — Pydantic serialises `Decimal` to a string, while
 * frontend fixtures pass numbers directly. Components should accept
 * the union and call `toNumber` before doing arithmetic.
 */
export type Numeric = number | string;

export function toNumber(value: Numeric | null | undefined): number {
  if (value === null || value === undefined) return 0;
  const n = typeof value === "string" ? Number(value) : value;
  return Number.isFinite(n) ? n : 0;
}

const krw = new Intl.NumberFormat("ko-KR", {
  style: "currency",
  currency: "KRW",
  maximumFractionDigits: 0,
});

const pct1 = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export function formatKrw(value: Numeric | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const n = toNumber(value);
  if (!Number.isFinite(n)) return "—";
  return krw.format(n);
}

export function formatPct(
  value: Numeric | null | undefined,
  fraction = 1,
): string {
  if (value === null || value === undefined) return "—";
  const n = toNumber(value);
  if (!Number.isFinite(n)) return "—";
  if (fraction === 1) return `${pct1.format(n)}%`;
  return `${n.toFixed(fraction)}%`;
}

export function formatDelta(value: string): string {
  // The fixture already includes sign + percent — return as-is.
  return value;
}
