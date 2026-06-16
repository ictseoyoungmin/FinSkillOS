import type { KeyboardEvent, PointerEvent } from "react";
import { useRef, useState } from "react";
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

function formatValue(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 2 });
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
 * allowed. A hover / keyboard crosshair reads the stored value at a
 * point (descriptive, not a forecast); screen readers get an
 * equivalent data table and a live readout.
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
  const plotRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState<number | null>(null);

  const normalisedSeries = series.map((s) => ({
    ...s,
    numeric: s.values.map((v) => (v === null ? null : toNumber(v))),
  }));
  const allFinite = normalisedSeries
    .flatMap((s) => s.numeric.filter((v): v is number => v !== null))
    .filter((v) => Number.isFinite(v));
  const min = allFinite.length ? Math.min(...allFinite) : 0;
  const max = allFinite.length ? Math.max(...allFinite) : 1;
  const span = max - min || 1;

  const pointCount = Math.max(
    labels.length,
    ...normalisedSeries.map((s) => s.numeric.length),
    0,
  );
  const stepXFull = pointCount > 1 ? innerW / (pointCount - 1) : 0;
  const xForIndex = (i: number) => PADDING_X + stepXFull * i;
  const yForValue = (v: number) =>
    PADDING_TOP + innerH - ((v - min) / span) * innerH;

  const ariaLabel =
    pointCount > 0
      ? `Line chart of ${normalisedSeries
          .map((s) => s.name)
          .join(", ")}; ${pointCount} points from ${labels[0] ?? "start"} to ${
          labels[pointCount - 1] ?? "end"
        }. Use arrow keys to read each point.`
      : "Line chart with no stored points yet.";

  const clampIndex = (i: number) => Math.max(0, Math.min(pointCount - 1, i));

  // Sparse, point-positioned x-axis ticks — rendering every label crushes a
  // many-point series into an illegible strip.
  const tickTarget = Math.min(6, pointCount);
  const xTicks =
    pointCount <= 1
      ? pointCount === 1 && labels[0] != null
        ? [0]
        : []
      : Array.from({ length: tickTarget }, (_, k) =>
          Math.round((k * (pointCount - 1)) / (tickTarget - 1)),
        ).filter(
          (idx, position, arr) =>
            arr.indexOf(idx) === position && labels[idx] != null,
        );

  const handlePointerMove = (event: PointerEvent<HTMLDivElement>) => {
    const host = plotRef.current;
    if (!host || pointCount === 0) return;
    const rect = host.getBoundingClientRect();
    if (rect.width === 0) return;
    const viewX = ((event.clientX - rect.left) / rect.width) * width;
    const ratio = innerW === 0 ? 0 : (viewX - PADDING_X) / innerW;
    setActive(clampIndex(Math.round(ratio * (pointCount - 1))));
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (pointCount === 0) return;
    const base = active ?? pointCount - 1;
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      setActive(clampIndex(base - 1));
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      setActive(clampIndex(base + 1));
    } else if (event.key === "Home") {
      event.preventDefault();
      setActive(0);
    } else if (event.key === "End") {
      event.preventDefault();
      setActive(pointCount - 1);
    } else if (event.key === "Escape") {
      setActive(null);
    }
  };

  const activePoints =
    active === null
      ? []
      : normalisedSeries
          .map((s) => ({ name: s.name, value: s.numeric[active] ?? null }))
          .filter((p): p is { name: string; value: number } => p.value !== null);
  const activeLabel = active === null ? "" : labels[active] ?? `Point ${active + 1}`;
  const readoutText =
    active === null || activePoints.length === 0
      ? ""
      : `${activeLabel}: ${activePoints
          .map((p) => `${p.name} ${formatValue(p.value)}`)
          .join(", ")}`;
  const tooltipLeft = active === null ? 0 : (xForIndex(active) / width) * 100;

  return (
    <div className="fso-linechart" data-testid={testId}>
      <div
        ref={plotRef}
        className="fso-linechart-plot"
        role="img"
        aria-label={ariaLabel}
        tabIndex={0}
        onPointerMove={handlePointerMove}
        onPointerLeave={() => setActive(null)}
        onFocus={() => setActive((prev) => prev ?? (pointCount ? pointCount - 1 : null))}
        onBlur={() => setActive(null)}
        onKeyDown={handleKeyDown}
      >
        <svg
          className="fso-linechart-svg"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
          style={{ height }}
          aria-hidden
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
          {active !== null && pointCount > 0 ? (
            <>
              <line
                className="fso-linechart-crosshair"
                x1={xForIndex(active)}
                x2={xForIndex(active)}
                y1={PADDING_TOP}
                y2={PADDING_TOP + innerH}
              />
              {activePoints.map((p) => (
                <circle
                  key={p.name}
                  className="fso-linechart-dot"
                  cx={xForIndex(active)}
                  cy={yForValue(p.value)}
                  r={3.2}
                />
              ))}
            </>
          ) : null}
        </svg>
        {readoutText ? (
          <div
            className="fso-linechart-tooltip"
            style={{ left: `${tooltipLeft}%` }}
            aria-hidden
          >
            <strong>{activeLabel}</strong>
            {activePoints.map((p) => (
              <span key={p.name}>
                {p.name}: {formatValue(p.value)}
              </span>
            ))}
          </div>
        ) : null}
      </div>
      <div className="fso-linechart-axislabels" aria-hidden>
        {xTicks.map((i) => (
          <span key={i} style={{ left: `${(xForIndex(i) / width) * 100}%` }}>
            {labels[i]}
          </span>
        ))}
      </div>
      <span className="fso-sr-only" aria-live="polite">
        {readoutText}
      </span>
      {pointCount > 0 ? (
        <table className="fso-sr-only">
          <caption>{ariaLabel}</caption>
          <thead>
            <tr>
              <th scope="col">Point</th>
              {normalisedSeries.map((s) => (
                <th key={s.name} scope="col">
                  {s.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {labels.map((label, i) => (
              <tr key={`${label}-${i}`}>
                <th scope="row">{label}</th>
                {normalisedSeries.map((s) => (
                  <td key={s.name}>
                    {s.numeric[i] == null ? "—" : formatValue(s.numeric[i] as number)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
      {caption ? <p className="fso-linechart-caption">{caption}</p> : null}
    </div>
  );
}
