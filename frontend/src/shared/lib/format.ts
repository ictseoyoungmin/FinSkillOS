/** Number / percent / currency formatters used across the cockpit. */

const krw = new Intl.NumberFormat("ko-KR", {
  style: "currency",
  currency: "KRW",
  maximumFractionDigits: 0,
});

const pct1 = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export function formatKrw(value: number | string): string {
  const n = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(n)) return "—";
  return krw.format(n);
}

export function formatPct(value: number | string, fraction = 1): string {
  const n = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(n)) return "—";
  if (fraction === 1) return `${pct1.format(n)}%`;
  return `${n.toFixed(fraction)}%`;
}

export function formatDelta(value: string): string {
  // The fixture already includes sign + percent — return as-is.
  return value;
}
