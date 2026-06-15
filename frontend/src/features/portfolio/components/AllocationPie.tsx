import { Panel } from "@/shared/ui";
import { formatKrw } from "@/shared/lib/format";
import type { AllocationSlice } from "@/features/portfolio/types";

import "./allocation-pie.css";

export interface AllocationPieProps {
  allocation?: AllocationSlice[];
}

const COLORS = [
  "#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#fb7185",
  "#a78bfa", "#22d3ee", "#f472b6", "#4ade80",
];
const REST = "#64748b";

const R = 56;
const CX = 70;
const CY = 70;
const STROKE = 24;
const CIRC = 2 * Math.PI * R;

/**
 * Portfolio allocation donut — per-ticker share (sectors are not populated). Top 8
 * holdings + a "기타" remainder. Descriptive composition view, no execution.
 */
export function AllocationPie({ allocation = [] }: AllocationPieProps) {
  if (allocation.length === 0) return null;

  const top = allocation.slice(0, 8);
  const restPct = allocation.slice(8).reduce((sum, a) => sum + a.weightPct, 0);
  const slices = restPct > 0.05
    ? [...top, { ticker: "기타", value: "", weightPct: restPct }]
    : top;

  let acc = 0;

  return (
    <Panel title="Allocation" badge="HOLDINGS" badgeTone="info" testId="mission-allocation">
      <div className="fso-alloc">
        <svg viewBox="0 0 140 140" className="fso-alloc-svg" role="img" aria-label="Allocation donut">
          {slices.map((s, i) => {
            const frac = Math.max(0, s.weightPct / 100);
            const dash = `${frac * CIRC} ${CIRC}`;
            const offset = -acc * CIRC;
            acc += frac;
            return (
              <circle
                key={s.ticker}
                cx={CX}
                cy={CY}
                r={R}
                fill="none"
                stroke={s.ticker === "기타" ? REST : COLORS[i % COLORS.length]}
                strokeWidth={STROKE}
                strokeDasharray={dash}
                strokeDashoffset={offset}
                transform={`rotate(-90 ${CX} ${CY})`}
              />
            );
          })}
          <text x={CX} y={CY - 2} className="fso-alloc-center-top">{allocation.length}</text>
          <text x={CX} y={CY + 12} className="fso-alloc-center-sub">holdings</text>
        </svg>
        <ul className="fso-alloc-legend">
          {slices.map((s, i) => (
            <li key={s.ticker} data-testid={`alloc-${s.ticker}`}>
              <span
                className="fso-alloc-dot"
                style={{ background: s.ticker === "기타" ? REST : COLORS[i % COLORS.length] }}
              />
              <span className="fso-alloc-tk">{s.ticker}</span>
              <span className="fso-alloc-pct">{s.weightPct.toFixed(1)}%</span>
              {s.value ? (
                <span className="fso-alloc-val">{formatKrw(Number(s.value))}</span>
              ) : null}
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}
