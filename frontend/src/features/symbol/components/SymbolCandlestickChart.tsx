import { useMemo, useState } from "react";
import { toNumber, type Numeric } from "@/shared/lib/format";
import { Badge, Panel } from "@/shared/ui";
import type { SymbolLabHeader, SymbolRecentBar } from "../types";

export interface SymbolCandlestickChartProps {
  header: SymbolLabHeader;
  bars: SymbolRecentBar[];
  selectedTimeframe: string;
  onTimeframeChange: (timeframe: string) => void;
}

interface OverlayConfig {
  key: "ema20" | "ema60" | "ema120" | "bollinger";
  label: string;
  help: string;
}

const TIMEFRAMES = [
  { label: "5m", value: "5m" },
  { label: "15m", value: "15m" },
  { label: "1h", value: "1h" },
  { label: "1d", value: "1d" },
  { label: "1w", value: "1wk" },
  { label: "1mon", value: "1mo" },
  { label: "1y", value: "1y" },
];

const OVERLAYS: OverlayConfig[] = [
  {
    key: "ema20",
    label: "EMA20",
    help: "Shorter moving-average context computed from stored close bars.",
  },
  {
    key: "ema60",
    label: "EMA60",
    help: "Medium trend context; descriptive only.",
  },
  {
    key: "ema120",
    label: "EMA120",
    help: "Longer trend context when enough bars are available.",
  },
  {
    key: "bollinger",
    label: "Bollinger",
    help: "Upper/lower volatility bands around the close path.",
  },
];

const WIDTH = 760;
const PRICE_HEIGHT = 250;
const VOLUME_HEIGHT = 70;
const HEIGHT = PRICE_HEIGHT + VOLUME_HEIGHT + 34;
const PAD_X = 34;
const PAD_TOP = 18;

function finite(value: Numeric | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  const n = toNumber(value);
  return Number.isFinite(n) ? n : null;
}

function pathFor(
  values: Array<number | null>,
  xAt: (index: number) => number,
  yAt: (value: number) => number,
): string {
  let d = "";
  values.forEach((value, index) => {
    if (value === null) return;
    const command = d ? "L" : "M";
    d += `${command}${xAt(index).toFixed(2)} ${yAt(value).toFixed(2)} `;
  });
  return d.trim();
}

function shortDate(iso: string): string {
  const [date] = iso.split("T");
  return date?.slice(5) ?? iso;
}

function computedEma(values: number[], period: number): Array<number | null> {
  if (values.length === 0) return [];
  const alpha = 2 / (period + 1);
  let prev = values[0];
  return values.map((value, index) => {
    prev = index === 0 ? value : value * alpha + prev * (1 - alpha);
    return index + 1 >= period ? prev : null;
  });
}

function computedBollinger(values: number[], period = 20) {
  return values.map((_, index) => {
    if (index + 1 < period) return { mid: null, upper: null, lower: null };
    const window = values.slice(index + 1 - period, index + 1);
    const mean = window.reduce((sum, value) => sum + value, 0) / period;
    const variance =
      window.reduce((sum, value) => sum + (value - mean) ** 2, 0) / period;
    const width = Math.sqrt(variance) * 2;
    return { mid: mean, upper: mean + width, lower: mean - width };
  });
}

export function SymbolCandlestickChart({
  header,
  bars,
  selectedTimeframe,
  onTimeframeChange,
}: SymbolCandlestickChartProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [enabled, setEnabled] = useState({
    ema20: true,
    ema60: false,
    ema120: false,
    bollinger: true,
  });

  const chronological = useMemo(
    () => [...bars].sort((a, b) => a.barTime.localeCompare(b.barTime)),
    [bars],
  );
  const closes = chronological.map((bar) => finite(bar.close) ?? 0);
  const ema20 = chronological.map((bar) => finite(bar.ema20));
  const ema60 = chronological.map((bar) => finite(bar.ema60));
  const ema120 = chronological.map((bar) => finite(bar.ema120));
  const fallbackEma20 = computedEma(closes, 20);
  const fallbackEma60 = computedEma(closes, 60);
  const fallbackEma120 = computedEma(closes, 120);
  const bollinger = computedBollinger(closes);
  const bbUpper = chronological.map(
    (bar, index) => finite(bar.bbUpper) ?? bollinger[index]?.upper ?? null,
  );
  const bbLower = chronological.map(
    (bar, index) => finite(bar.bbLower) ?? bollinger[index]?.lower ?? null,
  );

  const prices = chronological.flatMap((bar) =>
    [bar.high, bar.low, bar.open, bar.close]
      .map(finite)
      .filter((v): v is number => v !== null),
  );
  const overlayPrices = [
    ...ema20,
    ...ema60,
    ...ema120,
    ...bbUpper,
    ...bbLower,
    ...fallbackEma20,
    ...fallbackEma60,
    ...fallbackEma120,
  ].filter((v): v is number => v !== null);
  const allPrices = [...prices, ...overlayPrices];
  const priceMin = allPrices.length ? Math.min(...allPrices) : 0;
  const priceMax = allPrices.length ? Math.max(...allPrices) : 1;
  const span = priceMax - priceMin || 1;
  const volumeMax = Math.max(
    ...chronological.map((bar) => finite(bar.volume) ?? 0),
    1,
  );
  const innerW = WIDTH - PAD_X * 2;
  const candleStep =
    chronological.length <= 1 ? innerW : innerW / (chronological.length - 1);
  const candleW = Math.max(3, Math.min(12, candleStep * 0.56));
  const xAt = (index: number) => PAD_X + candleStep * index;
  const priceY = (value: number) =>
    PAD_TOP + PRICE_HEIGHT - ((value - priceMin) / span) * PRICE_HEIGHT;
  const volumeBase = PAD_TOP + PRICE_HEIGHT + VOLUME_HEIGHT;

  const dataStatusTone =
    header.dataStatus === "OK"
      ? "info"
      : header.dataStatus === "PARTIAL"
        ? "warning"
        : "danger";

  return (
    <Panel
      title={`Candles · ${header.ticker}`}
      badge={header.timeframe.toUpperCase()}
      badgeTone="info"
      testId="symbol-candlestick-chart"
    >
      <div className="fso-symbol-chart-header">
        <div>
          <strong>{header.ticker}</strong>
          <span className="fso-symbol-chart-meta">
            {header.latestTime
              ? header.latestTime.slice(0, 10)
              : "No bar timestamp"}
          </span>
        </div>
        <div className="fso-symbol-chart-latest">
          <span>
            {header.latestClose === null
              ? "-"
              : toNumber(header.latestClose).toFixed(2)}
          </span>
          <Badge tone={dataStatusTone}>{header.dataStatus}</Badge>
        </div>
      </div>

      <div className="fso-symbol-chart-toolbar">
        <div className="fso-symbol-timeframes" aria-label="Chart timeframe">
          {TIMEFRAMES.map((item) => (
            <button
              key={item.value}
              type="button"
              className={
                item.value === selectedTimeframe
                  ? "fso-symbol-chip fso-symbol-chip--active"
                  : "fso-symbol-chip"
              }
              onClick={() => onTimeframeChange(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="fso-symbol-overlay-menu">
          <button
            type="button"
            className="fso-symbol-chip"
            onClick={() => setMenuOpen((open) => !open)}
            aria-expanded={menuOpen}
          >
            Indicators ?
          </button>
          {menuOpen ? (
            <div className="fso-symbol-overlay-popover">
              {OVERLAYS.map((overlay) => (
                <label key={overlay.key} className="fso-symbol-overlay-option">
                  <input
                    type="checkbox"
                    checked={enabled[overlay.key]}
                    onChange={() =>
                      setEnabled((state) => ({
                        ...state,
                        [overlay.key]: !state[overlay.key],
                      }))
                    }
                  />
                  <span>{overlay.label}</span>
                  <span title={overlay.help} aria-label={overlay.help}>
                    ?
                  </span>
                </label>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      <div className="fso-candlechart" data-testid="symbol-candle-svg">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          preserveAspectRatio="none"
          role="img"
        >
          <line
            x1={PAD_X}
            x2={WIDTH - PAD_X}
            y1={PAD_TOP + PRICE_HEIGHT}
            y2={PAD_TOP + PRICE_HEIGHT}
            className="fso-candle-axis"
          />
          <line
            x1={PAD_X}
            x2={WIDTH - PAD_X}
            y1={PAD_TOP + PRICE_HEIGHT / 2}
            y2={PAD_TOP + PRICE_HEIGHT / 2}
            className="fso-candle-axis-soft"
          />
          {enabled.bollinger ? (
            <>
              <path
                d={pathFor(bbUpper, xAt, priceY)}
                className="fso-candle-overlay fso-candle-overlay--band"
              />
              <path
                d={pathFor(bbLower, xAt, priceY)}
                className="fso-candle-overlay fso-candle-overlay--band"
              />
            </>
          ) : null}
          {enabled.ema20 ? (
            <path
              d={pathFor(ema20.some(Boolean) ? ema20 : fallbackEma20, xAt, priceY)}
              className="fso-candle-overlay fso-candle-overlay--ema20"
            />
          ) : null}
          {enabled.ema60 ? (
            <path
              d={pathFor(ema60.some(Boolean) ? ema60 : fallbackEma60, xAt, priceY)}
              className="fso-candle-overlay fso-candle-overlay--ema60"
            />
          ) : null}
          {enabled.ema120 ? (
            <path
              d={pathFor(
                ema120.some(Boolean) ? ema120 : fallbackEma120,
                xAt,
                priceY,
              )}
              className="fso-candle-overlay fso-candle-overlay--ema120"
            />
          ) : null}
          {chronological.map((bar, index) => {
            const open = finite(bar.open) ?? finite(bar.close) ?? 0;
            const close = finite(bar.close) ?? open;
            const high = finite(bar.high) ?? Math.max(open, close);
            const low = finite(bar.low) ?? Math.min(open, close);
            const volume = finite(bar.volume) ?? 0;
            const x = xAt(index);
            const isUp = close >= open;
            const y = Math.min(priceY(open), priceY(close));
            const bodyH = Math.max(1, Math.abs(priceY(close) - priceY(open)));
            const volumeH = (volume / volumeMax) * (VOLUME_HEIGHT - 8);
            return (
              <g key={bar.barTime}>
                <rect
                  x={x - candleW / 2}
                  y={volumeBase - volumeH}
                  width={candleW}
                  height={volumeH}
                  className={
                    isUp
                      ? "fso-candle-volume fso-candle-volume--up"
                      : "fso-candle-volume fso-candle-volume--down"
                  }
                />
                <line
                  x1={x}
                  x2={x}
                  y1={priceY(high)}
                  y2={priceY(low)}
                  className={
                    isUp
                      ? "fso-candle-wick fso-candle-wick--up"
                      : "fso-candle-wick fso-candle-wick--down"
                  }
                />
                <rect
                  x={x - candleW / 2}
                  y={y}
                  width={candleW}
                  height={bodyH}
                  rx={1}
                  className={
                    isUp
                      ? "fso-candle-body fso-candle-body--up"
                      : "fso-candle-body fso-candle-body--down"
                  }
                />
              </g>
            );
          })}
        </svg>
        <div className="fso-linechart-axislabels" aria-hidden>
          {chronological.length ? (
            <>
              <span>{shortDate(chronological[0].barTime)}</span>
              <span>
                {shortDate(
                  chronological[Math.floor(chronological.length / 2)].barTime,
                )}
              </span>
              <span>{shortDate(chronological[chronological.length - 1].barTime)}</span>
            </>
          ) : (
            <span>No candle data</span>
          )}
        </div>
        <p className="fso-linechart-caption">
          Snapshot candles + volume · overlays are descriptive · no execution
        </p>
      </div>
    </Panel>
  );
}
