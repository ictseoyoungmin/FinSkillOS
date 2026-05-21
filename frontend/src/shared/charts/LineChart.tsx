import { toNumber, type Numeric } from "@/shared/lib/format";
import "./line-chart.css";

export interface LineChartSeries {
  name: string;
  values: Array<Numeric | null>;
  tone?: "primary" | "muted";
  dashed?: boolean;
}

export interface LineChartProps {
  labels: string[];
  series: LineChartSeries[];
  /** Optional axis caption shown below the chart. */
  caption?: string;
  /** Test id used by Playwright structural tests. */
  testId?: string;
  /** SVG viewBox dimensions; defaults match the v4.1 mockup. */
  width?: number;
  height?: number;
}

const PADDING_X = 28;
const PADDING_TOP = 18;
const PADDING_BOTTOM = 34;

interface SeriesPath {
  d: string;
  endX: number;
  endY: number;
}

function pathFor(
  values: number[],
  min: number,
  max: number,
  innerW: number,
  innerH: number,
): SeriesPath {
  if (values.length === 0) {
    return { d: "", endX: PADDING_X, endY: PADDING_TOP + innerH };
  }
  const span = max - min || 1;
  const stepX = values.length === 1 ? 0 : innerW / (values.length - 1);
  const coords = values.map((v, i) => {
    const x = PADDING_X + stepX * i;
    const norm = (v - min) / span;
    const y = PADDING_TOP + innerH - norm * innerH;
    return { x, y };
  });
  const d = coords
    .map((c, i) => `${i === 0 ? "M" : "L"}${c.x.toFixed(2)} ${c.y.toFixed(2)}`)
    .join(" ");
  const last = coords[coords.length - 1];
  return { d, endX: last.x, endY: last.y };
}

/**
 * Reusable, dependency-free SVG line chart. Used by:
 *
 *  - Control Room: Portfolio / Market Tape panel (via
 *    `PortfolioMarketTapePanel`, which keeps its own normalisation
 *    legend and safety caption).
 *  - Market Kernel: stored bar series chart panel.
 *
 * The chart is intentionally descriptive — no overlays, no drawing
 * tools, no prediction labels. Slice 13.7 spec lists those as not
 * allowed.
 */
export function LineChart({
  labels,
  series,
  caption,
  testId,
  width = 720,
  height = 240,
}: LineChartProps) {
  const innerW = width - PADDING_X * 2;
  const innerH = height - PADDING_TOP - PADDING_BOTTOM;

  const normalisedSeries = series.map((s) => ({
    ...s,
    numeric: s.values.map((v) => (v === null ? null : toNumber(v))),
  }));
  const allFinite = normalisedSeries
    .flatMap((s) => s.numeric.filter((v): v is number => v !== null))
    .filter((v) => Number.isFinite(v));
  const min = allFinite.length ? Math.min(...allFinite) : 0;
  const max = allFinite.length ? Math.max(...allFinite) : 1;

  return (
    <div className="fso-linechart" data-testid={testId}>
      <svg
        className="fso-linechart-svg"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        role="img"
        aria-label="Stored bar series line chart"
      >
        <line
          x1={PADDING_X}
          x2={width - PADDING_X}
          y1={PADDING_TOP + innerH}
          y2={PADDING_TOP + innerH}
          className="fso-linechart-axis"
        />
        <line
          x1={PADDING_X}
          x2={width - PADDING_X}
          y1={PADDING_TOP + innerH / 2}
          y2={PADDING_TOP + innerH / 2}
          className="fso-linechart-axis-soft"
        />
        {normalisedSeries.map((s) => {
          // Drop null points so a partial series still renders.
          const finite = s.numeric.filter((v): v is number => v !== null);
          const path = pathFor(finite, min, max, innerW, innerH);
          const tone = s.tone ?? "primary";
          return (
            <path
              key={s.name}
              d={path.d}
              className={`fso-linechart-series fso-linechart-series--${tone} ${
                s.dashed ? "fso-linechart-series--dashed" : ""
              }`.trim()}
            />
          );
        })}
      </svg>
      <div className="fso-linechart-axislabels" aria-hidden>
        {labels.map((label) => (
          <span key={label}>{label}</span>
        ))}
      </div>
      {caption ? <p className="fso-linechart-caption">{caption}</p> : null}
    </div>
  );
}
