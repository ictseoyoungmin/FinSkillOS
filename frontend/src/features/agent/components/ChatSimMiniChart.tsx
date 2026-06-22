import { useEffect, useMemo, useRef, useState } from "react";
import type { ChatSimPreview } from "../types";
import "./chat-sim-mini-chart.css";

export interface ChatSimMiniChartProps {
  sim: ChatSimPreview;
  onOpen: (navPath: string) => void;
}

const W = 280;
const H = 96;
const PAD = 6;

function pct(v: number | null): string {
  return v === null || !Number.isFinite(v) ? "—" : `${(v * 100).toFixed(1)}%`;
}

function ratio(v: number | null): string {
  return v === null || !Number.isFinite(v) ? "—" : v.toFixed(2);
}

/**
 * Compact in-chat simulation preview: a price sparkline that streams in
 * left→right once, with exposure-ON shading and ▲/▼ 노출 시작·해제 markers.
 * Descriptive only — never buy/sell. The full animated replay lives in the tab.
 */
export function ChatSimMiniChart({ sim, onOpen }: ChatSimMiniChartProps) {
  const n = sim.closes.length;
  const [shown, setShown] = useState(n);
  const raf = useRef<number | null>(null);

  // Stream the sparkline in once on mount.
  useEffect(() => {
    if (n <= 1) {
      setShown(n);
      return;
    }
    setShown(1);
    const start = performance.now();
    const DURATION = 1400;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / DURATION);
      setShown(Math.max(1, Math.round(p * n)));
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current !== null) cancelAnimationFrame(raf.current);
    };
  }, [n]);

  const { min, span } = useMemo(() => {
    const vals = sim.closes.filter((v) => Number.isFinite(v));
    const lo = vals.length ? Math.min(...vals) : 0;
    const hi = vals.length ? Math.max(...vals) : 1;
    return { min: lo, span: hi - lo || 1 };
  }, [sim.closes]);

  if (n === 0) return null;

  const innerW = W - PAD * 2;
  const innerH = H - PAD * 2;
  const stepX = n <= 1 ? 0 : innerW / (n - 1);
  const xAt = (i: number) => PAD + stepX * i;
  const yAt = (v: number) => PAD + innerH - ((v - min) / span) * innerH;

  const visible = sim.closes.slice(0, shown);
  const path = visible
    .map((c, i) => `${i === 0 ? "M" : "L"}${xAt(i).toFixed(1)} ${yAt(c).toFixed(1)}`)
    .join(" ");

  const bands: Array<{ x: number; w: number }> = [];
  let run: number | null = null;
  for (let i = 0; i < shown; i += 1) {
    const on = sim.exposures[i];
    if (on && run === null) run = i;
    if ((!on || i === shown - 1) && run !== null) {
      const end = on ? i : i - 1;
      bands.push({ x: xAt(run), w: Math.max(1.5, xAt(end) - xAt(run)) });
      run = null;
    }
  }

  return (
    <div className="fso-sim-mini" data-testid="chat-sim-mini">
      <div className="fso-sim-mini-head">
        <strong>{sim.ticker}</strong> · {sim.strategyName}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="fso-sim-mini-svg" role="img" aria-label={`${sim.ticker} 시뮬레이션 미니 차트`}>
        {bands.map((b, i) => (
          <rect key={i} x={b.x} y={PAD} width={b.w} height={innerH} className="fso-sim-mini-band" />
        ))}
        <path d={path} className="fso-sim-mini-line" fill="none" />
        {sim.markers
          .filter((m) => m.index < shown)
          .map((m, i) => {
            const x = xAt(m.index);
            const y = yAt(sim.closes[m.index]);
            const enter = m.kind === "ENTER";
            return (
              <circle
                key={i}
                cx={x}
                cy={y}
                r={3}
                className={enter ? "fso-sim-mini-enter" : "fso-sim-mini-exit"}
              />
            );
          })}
      </svg>
      <div className="fso-sim-mini-stats">
        노출 {pct(sim.exposurePct)} · 누적 {pct(sim.totalReturn)} · Sharpe {ratio(sim.sharpe)} · MDD {pct(sim.maxDrawdown)}
      </div>
      <button
        className="fso-sim-mini-open"
        onClick={() => onOpen(sim.navPath)}
        data-testid="chat-sim-open-tab"
      >
        탭에서 전체 리플레이 ▶
      </button>
    </div>
  );
}
