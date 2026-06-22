import { useMemo } from "react";
import type { QuantEquityPoint, QuantMarker } from "../types";

export interface QuantPriceReplayChartProps {
  curve: QuantEquityPoint[];
  markers: QuantMarker[];
  /** How many points (left→right) are revealed — drives the replay animation. */
  visibleCount: number;
  ticker: string;
  width?: number;
  height?: number;
}

const PAD_X = 30;
const PAD_TOP = 16;
const PAD_BOTTOM = 28;

/**
 * Time-ordered price chart with simulated exposure shading + ENTER/EXIT markers.
 * Descriptive only — markers are "노출 시작 / 노출 해제" (exposure on/off), never
 * buy/sell. ``visibleCount`` reveals the series progressively for the replay; the
 * axes stay fixed to the full range so the line grows into a stable frame.
 */
export function QuantPriceReplayChart({
  curve,
  markers,
  visibleCount,
  ticker,
  width = 720,
  height = 300,
}: QuantPriceReplayChartProps) {
  const innerW = width - PAD_X * 2;
  const innerH = height - PAD_TOP - PAD_BOTTOM;

  const { min, max } = useMemo(() => {
    const vals = curve.map((p) => p.close).filter((v) => Number.isFinite(v));
    if (vals.length === 0) return { min: 0, max: 1 };
    return { min: Math.min(...vals), max: Math.max(...vals) };
  }, [curve]);

  if (curve.length === 0) {
    return <p className="fso-quant-empty">표시할 가격 시계열이 없습니다.</p>;
  }

  const n = curve.length;
  const span = max - min || 1;
  const stepX = n <= 1 ? 0 : innerW / (n - 1);
  const xAt = (i: number) => PAD_X + stepX * i;
  const yAt = (v: number) => PAD_TOP + innerH - ((v - min) / span) * innerH;

  const shown = Math.max(1, Math.min(visibleCount, n));
  const visible = curve.slice(0, shown);

  const linePath = visible
    .map((p, i) => `${i === 0 ? "M" : "L"}${xAt(i).toFixed(1)} ${yAt(p.close).toFixed(1)}`)
    .join(" ");

  // Exposure shading: contiguous IN runs within the revealed window.
  const bands: Array<{ x: number; w: number }> = [];
  let runStart: number | null = null;
  for (let i = 0; i < shown; i += 1) {
    const on = visible[i].exposure;
    if (on && runStart === null) runStart = i;
    if ((!on || i === shown - 1) && runStart !== null) {
      const end = on ? i : i - 1;
      bands.push({ x: xAt(runStart), w: Math.max(2, xAt(end) - xAt(runStart)) });
      runStart = null;
    }
  }

  const dateIndex = new Map(curve.map((p, i) => [p.date, i]));
  const shownMarkers = markers.filter((m) => {
    const i = dateIndex.get(m.date);
    return i !== undefined && i < shown;
  });

  const lastIdx = shown - 1;
  const cursorX = xAt(lastIdx);

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="fso-quant-replay-svg"
      role="img"
      aria-label={`${ticker} 가격 시계열 시뮬레이션 리플레이`}
      data-testid="quant-price-replay"
    >
      {bands.map((b, i) => (
        <rect
          key={`band-${i}`}
          x={b.x}
          y={PAD_TOP}
          width={b.w}
          height={innerH}
          className="fso-quant-band"
        />
      ))}
      <path d={linePath} className="fso-quant-price-line" fill="none" />
      {/* replay cursor */}
      <line
        x1={cursorX}
        x2={cursorX}
        y1={PAD_TOP}
        y2={PAD_TOP + innerH}
        className="fso-quant-cursor"
      />
      {shownMarkers.map((m, i) => {
        const idx = dateIndex.get(m.date) ?? 0;
        const x = xAt(idx);
        const y = yAt(m.price);
        const enter = m.kind === "ENTER";
        return (
          <g key={`mk-${i}`} className={enter ? "fso-mk-enter" : "fso-mk-exit"}>
            <title>{`${m.date} · ${enter ? "매수" : "매도"} @ ${m.price}`}</title>
            <circle cx={x} cy={y} r={4.5} />
            <text x={x} y={enter ? y + 16 : y - 9} textAnchor="middle">
              {enter ? "▲" : "▼"}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
