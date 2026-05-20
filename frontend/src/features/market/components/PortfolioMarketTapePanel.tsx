import { Panel } from "@/shared/ui";
import { toNumber, type Numeric } from "@/shared/lib/format";
import "./portfolio-market-tape-panel.css";

export interface MarketTapePoint {
  label: string;
  portfolio: Numeric;
  benchmark: Numeric;
}

export interface PortfolioMarketTapePanelProps {
  points: MarketTapePoint[];
  badge?: string;
}

const VIEW_WIDTH = 720;
const VIEW_HEIGHT = 220;
const PADDING_X = 24;
const PADDING_TOP = 18;
const PADDING_BOTTOM = 34;

interface SeriesPath {
  d: string;
  endX: number;
  endY: number;
}

function buildPath(
  values: number[],
  min: number,
  max: number,
): SeriesPath {
  if (values.length === 0) {
    return { d: "", endX: PADDING_X, endY: VIEW_HEIGHT - PADDING_BOTTOM };
  }
  const usableW = VIEW_WIDTH - PADDING_X * 2;
  const usableH = VIEW_HEIGHT - PADDING_TOP - PADDING_BOTTOM;
  const span = max - min || 1;
  const stepX = values.length === 1 ? 0 : usableW / (values.length - 1);
  const coords = values.map((v, i) => {
    const x = PADDING_X + stepX * i;
    const norm = (v - min) / span;
    const y = PADDING_TOP + usableH - norm * usableH;
    return { x, y };
  });
  const d = coords
    .map((c, i) => `${i === 0 ? "M" : "L"}${c.x.toFixed(2)} ${c.y.toFixed(2)}`)
    .join(" ");
  const last = coords[coords.length - 1];
  return { d, endX: last.x, endY: last.y };
}

/**
 * Lightweight SVG line chart for the Control Room center column.
 *
 * Slice 13.6 cleanup contract:
 *  - Pure SVG, no chart library.
 *  - Normalised view (each series starts at the same point) — never
 *    used to show absolute price targets.
 *  - Safety caption is non-removable: "Normalized view · not
 *    prediction · stored data only".
 */
export function PortfolioMarketTapePanel({
  points,
  badge = "Fixture",
}: PortfolioMarketTapePanelProps) {
  const portfolioValues = points.map((p) => toNumber(p.portfolio));
  const benchmarkValues = points.map((p) => toNumber(p.benchmark));
  const all = [...portfolioValues, ...benchmarkValues];
  const min = all.length ? Math.min(...all) : 0;
  const max = all.length ? Math.max(...all) : 1;

  const portfolio = buildPath(portfolioValues, min, max);
  const benchmark = buildPath(benchmarkValues, min, max);

  const lastPortfolio = portfolioValues[portfolioValues.length - 1] ?? 0;
  const lastBenchmark = benchmarkValues[benchmarkValues.length - 1] ?? 0;
  const startPortfolio = portfolioValues[0] ?? 0;
  const startBenchmark = benchmarkValues[0] ?? 0;
  const portfolioDeltaPct =
    startPortfolio === 0 ? 0 : ((lastPortfolio - startPortfolio) / startPortfolio) * 100;
  const benchmarkDeltaPct =
    startBenchmark === 0 ? 0 : ((lastBenchmark - startBenchmark) / startBenchmark) * 100;

  return (
    <Panel
      title="Portfolio / Market Tape"
      badge={badge}
      badgeTone="info"
      testId="portfolio-market-tape"
    >
      <div className="fso-tape-legend" data-testid="portfolio-market-tape-legend">
        <span className="fso-tape-legend-item">
          <span className="fso-tape-swatch fso-tape-swatch--portfolio" />
          Portfolio
          <strong className={portfolioDeltaPct >= 0 ? "fso-tape-up" : "fso-tape-down"}>
            {portfolioDeltaPct >= 0 ? "+" : ""}
            {portfolioDeltaPct.toFixed(2)}%
          </strong>
        </span>
        <span className="fso-tape-legend-item">
          <span className="fso-tape-swatch fso-tape-swatch--benchmark" />
          Benchmark
          <strong className={benchmarkDeltaPct >= 0 ? "fso-tape-up" : "fso-tape-down"}>
            {benchmarkDeltaPct >= 0 ? "+" : ""}
            {benchmarkDeltaPct.toFixed(2)}%
          </strong>
        </span>
      </div>

      <svg
        className="fso-tape-svg"
        viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`}
        preserveAspectRatio="none"
        role="img"
        aria-label="Portfolio vs benchmark normalized line chart"
      >
        <line
          x1={PADDING_X}
          x2={VIEW_WIDTH - PADDING_X}
          y1={VIEW_HEIGHT - PADDING_BOTTOM}
          y2={VIEW_HEIGHT - PADDING_BOTTOM}
          className="fso-tape-axis"
        />
        <line
          x1={PADDING_X}
          x2={VIEW_WIDTH - PADDING_X}
          y1={PADDING_TOP + (VIEW_HEIGHT - PADDING_TOP - PADDING_BOTTOM) / 2}
          y2={PADDING_TOP + (VIEW_HEIGHT - PADDING_TOP - PADDING_BOTTOM) / 2}
          className="fso-tape-axis-soft"
        />
        <path d={benchmark.d} className="fso-tape-series fso-tape-series--benchmark" />
        <path d={portfolio.d} className="fso-tape-series fso-tape-series--portfolio" />
        {points.length > 0 && (
          <>
            <circle
              cx={benchmark.endX}
              cy={benchmark.endY}
              r={4}
              className="fso-tape-marker fso-tape-marker--benchmark"
            />
            <circle
              cx={portfolio.endX}
              cy={portfolio.endY}
              r={5}
              className="fso-tape-marker fso-tape-marker--portfolio"
            />
          </>
        )}
      </svg>

      <div className="fso-tape-buckets" aria-hidden>
        {points.map((p) => (
          <span key={p.label}>{p.label}</span>
        ))}
      </div>

      <p
        className="fso-tape-caption"
        data-testid="portfolio-market-tape-caption"
      >
        Normalized view · not prediction · stored data only.
      </p>
    </Panel>
  );
}
