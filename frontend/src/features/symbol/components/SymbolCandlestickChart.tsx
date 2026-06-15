import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent,
} from "react";
import { toNumber, type Numeric } from "@/shared/lib/format";
import { Badge, Panel } from "@/shared/ui";
import type { SymbolLabHeader, SymbolRecentBar } from "../types";

export interface SymbolCandlestickChartProps {
  header: SymbolLabHeader;
  bars: SymbolRecentBar[];
  selectedTimeframe: string;
  onTimeframeChange: (timeframe: string) => void;
  /** Restrict the timeframe buttons (by API value). Defaults to the full set. */
  timeframes?: readonly string[];
  /** Panel test id (defaults to "symbol-candlestick-chart"). */
  testId?: string;
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
  { label: "1mo", value: "1mo" },
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
const USD_TO_KRW = 1520.82;
const RIGHT_CANDLE_GAP = 4;
const TOOLTIP_WIDTH_PX = 248;
const TOOLTIP_HEIGHT_PX = 216;
const STAGE_RIGHT_AXIS_PX = 98;

type PriceCurrency = "USD" | "KRW";

const usdPrice = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const krwPrice = new Intl.NumberFormat("ko-KR", {
  style: "currency",
  currency: "KRW",
  maximumFractionDigits: 0,
});

const compactVolume = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

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

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function dateParts(iso: string) {
  const [date = "", time = ""] = iso.split("T");
  const [year = "", month = "", day = ""] = date.split("-");
  const clock = time.slice(0, 5);
  return { date, year, month, day, clock };
}

function isIntraday(timeframe: string): boolean {
  return timeframe === "5m" || timeframe === "15m" || timeframe === "1h";
}

function sameMonth(a: ReturnType<typeof dateParts>, b: ReturnType<typeof dateParts>) {
  return a.year === b.year && a.month === b.month;
}

function sameYear(a: ReturnType<typeof dateParts>, b: ReturnType<typeof dateParts>) {
  return a.year === b.year;
}

function tickLabel(iso: string, timeframe: string, previousIso?: string): string {
  const current = dateParts(iso);
  const previous = previousIso ? dateParts(previousIso) : null;
  const dayChanged = !previous || current.date !== previous.date;
  const monthChanged =
    !previous || current.year !== previous.year || current.month !== previous.month;
  const yearChanged = !previous || current.year !== previous.year;

  if (isIntraday(timeframe)) {
    if (yearChanged) return `${current.year}-${current.month}-${current.day}`;
    if (dayChanged) return `${current.month}-${current.day}`;
    return current.clock;
  }
  if (timeframe === "1y") {
    return current.year;
  }
  if (timeframe === "1mo") {
    if (yearChanged) return current.year;
    return current.month;
  }
  if (timeframe === "1wk") {
    return yearChanged ? current.year : `${current.month}-${current.day}`;
  }
  if (yearChanged) return `${current.year}-${current.month}`;
  if (monthChanged) return `${current.month}-${current.day}`;
  return current.day;
}

function fullTimestamp(iso: string, timeframe: string): string {
  const parts = dateParts(iso);
  if (isIntraday(timeframe) && parts.clock) {
    return `${parts.date} ${parts.clock}`;
  }
  return parts.date || iso;
}

function formatPrice(
  value: Numeric | null | undefined,
  currency: PriceCurrency,
): string {
  const n = finite(value);
  if (n === null) return "-";
  return currency === "KRW" ? krwPrice.format(n * USD_TO_KRW) : usdPrice.format(n);
}

function formatAxisPrice(value: number, currency: PriceCurrency): string {
  return currency === "KRW"
    ? krwPrice.format(value * USD_TO_KRW)
    : usdPrice.format(value);
}

function axisTickValues(min: number, max: number, count: number): number[] {
  if (count <= 1) return [max];
  return Array.from({ length: count }, (_, index) => {
    const ratio = index / (count - 1);
    return max - (max - min) * ratio;
  });
}

function timeTickIndexes(
  start: number,
  end: number,
  bars: SymbolRecentBar[],
  timeframe: string,
  candleStep: number,
): number[] {
  const length = end - start;
  if (length <= 0) return [];
  const minLabelGap = Math.max(1, Math.ceil(58 / Math.max(1, candleStep)));
  const maxTicks = Math.max(2, Math.floor(length / minLabelGap) + 1);
  const boundaryIndexes: number[] = [start];
  const minorCandidates: number[] = [];

  for (let index = start + 1; index < end; index += 1) {
    const previous = dateParts(bars[index - 1]?.barTime ?? "");
    const current = dateParts(bars[index]?.barTime ?? "");
    if (isIntraday(timeframe)) {
      if (current.date !== previous.date) boundaryIndexes.push(index);
      else minorCandidates.push(index);
      continue;
    }
    if (timeframe === "1mo") {
      if (!sameYear(current, previous) || !sameMonth(current, previous)) {
        boundaryIndexes.push(index);
      }
      continue;
    }
    if (timeframe === "1y") {
      if (!sameYear(current, previous)) boundaryIndexes.push(index);
      continue;
    }
    if (!sameYear(current, previous) || !sameMonth(current, previous)) {
      boundaryIndexes.push(index);
    } else {
      minorCandidates.push(index);
    }
  }

  const preferred =
    timeframe === "1mo" || timeframe === "1y"
      ? boundaryIndexes
      : [...boundaryIndexes, ...sampleEvenly(minorCandidates, maxTicks)];
  const merged = Array.from(new Set([...preferred, end - 1]))
    .filter((index) => index >= start && index < end)
    .sort((a, b) => a - b);
  return enforceTickSpacing(merged, minLabelGap, new Set([start, end - 1]));
}

function sampleEvenly(indexes: number[], maxCount: number): number[] {
  if (indexes.length <= maxCount) return indexes;
  if (maxCount <= 0) return [];
  const step = indexes.length / maxCount;
  return Array.from({ length: maxCount }, (_, index) => {
    return indexes[Math.min(indexes.length - 1, Math.floor(index * step))];
  });
}

function enforceTickSpacing(
  indexes: number[],
  minGap: number,
  required: Set<number>,
): number[] {
  const kept: number[] = [];
  for (const index of indexes) {
    const previous = kept[kept.length - 1];
    if (
      previous === undefined ||
      index - previous >= minGap ||
      required.has(index)
    ) {
      kept.push(index);
    }
  }
  return kept.filter((index, position) => {
    const next = kept[position + 1];
    return next === undefined || next - index >= minGap || required.has(index);
  });
}

function formatVolume(value: Numeric | null | undefined): string {
  const n = finite(value);
  if (n === null) return "-";
  return Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n);
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
  timeframes,
  testId = "symbol-candlestick-chart",
}: SymbolCandlestickChartProps) {
  const visibleTimeframes = timeframes
    ? TIMEFRAMES.filter((item) => timeframes.includes(item.value))
    : TIMEFRAMES;
  const [menuOpen, setMenuOpen] = useState(false);
  const [enabled, setEnabled] = useState({
    ema20: true,
    ema60: false,
    ema120: false,
    bollinger: true,
  });
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [pointerPrice, setPointerPrice] = useState<number | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [currency, setCurrency] = useState<PriceCurrency>("USD");
  const [visible, setVisible] = useState({ start: 0, count: 80 });
  const visibleRef = useRef(visible);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const [drag, setDrag] = useState<{
    pointerId: number;
    startX: number;
    startIndex: number | null;
    startWindow: number;
  } | null>(null);

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
  const totalCount = chronological.length;
  const maxVisibleCount = Math.max(1, totalCount);
  const minVisibleCount = Math.min(maxVisibleCount, 24);
  const visibleCount = clamp(visible.count, minVisibleCount, maxVisibleCount);
  const maxStart = Math.max(0, totalCount - visibleCount);
  const visibleStart = clamp(visible.start, 0, maxStart);
  const visibleEnd = Math.min(totalCount, visibleStart + visibleCount);
  const visibleBars = chronological.slice(visibleStart, visibleEnd);
  const visibleIndexes = visibleBars.map((_, index) => visibleStart + index);
  const visibleEma20 = visibleIndexes.map((index) => ema20[index]);
  const visibleEma60 = visibleIndexes.map((index) => ema60[index]);
  const visibleEma120 = visibleIndexes.map((index) => ema120[index]);
  const visibleFallbackEma20 = visibleIndexes.map((index) => fallbackEma20[index]);
  const visibleFallbackEma60 = visibleIndexes.map((index) => fallbackEma60[index]);
  const visibleFallbackEma120 = visibleIndexes.map(
    (index) => fallbackEma120[index],
  );
  const visibleBbUpper = visibleIndexes.map((index) => bbUpper[index]);
  const visibleBbLower = visibleIndexes.map((index) => bbLower[index]);

  useEffect(() => {
    setActiveIndex(null);
    setSelectedIndex(null);
    setDrag(null);
    setVisible({
      start: Math.max(0, totalCount - Math.min(totalCount, 80)),
      count: Math.min(totalCount, 80),
    });
  }, [selectedTimeframe, totalCount]);

  useEffect(() => {
    visibleRef.current = { start: visibleStart, count: visibleCount };
  }, [visibleCount, visibleStart]);

  const prices = visibleBars.flatMap((bar) =>
    [bar.high, bar.low, bar.open, bar.close]
      .map(finite)
      .filter((v): v is number => v !== null),
  );
  const overlayPrices = [
    ...visibleEma20,
    ...visibleEma60,
    ...visibleEma120,
    ...visibleBbUpper,
    ...visibleBbLower,
    ...visibleFallbackEma20,
    ...visibleFallbackEma60,
    ...visibleFallbackEma120,
  ].filter((v): v is number => v !== null);
  const allPrices = [...prices, ...overlayPrices];
  const priceMin = allPrices.length ? Math.min(...allPrices) : 0;
  const priceMax = allPrices.length ? Math.max(...allPrices) : 1;
  const span = priceMax - priceMin || 1;
  const volumeMax = Math.max(
    ...visibleBars.map((bar) => finite(bar.volume) ?? 0),
    1,
  );
  const innerW = WIDTH - PAD_X * 2;
  const candleSlots = Math.max(1, visibleBars.length - 1 + RIGHT_CANDLE_GAP);
  const candleStep = innerW / candleSlots;
  const candleW = Math.max(3, Math.min(12, candleStep * 0.56));
  const xAt = (index: number) => PAD_X + candleStep * (index - visibleStart);
  const priceY = (value: number) =>
    PAD_TOP + PRICE_HEIGHT - ((value - priceMin) / span) * PRICE_HEIGHT;
  const volumeBase = PAD_TOP + PRICE_HEIGHT + VOLUME_HEIGHT;
  const priceAxisLabels = axisTickValues(priceMin, priceMax, 6).map((value) => ({
    label: formatAxisPrice(value, currency),
    y: priceY(value),
  }));
  const volumeAxisLabels = axisTickValues(0, volumeMax, 4).map((value) => ({
    label: compactVolume.format(value),
    y: volumeBase - (value / volumeMax) * (VOLUME_HEIGHT - 8),
  }));
  const timeAxisTicks = timeTickIndexes(
    visibleStart,
    visibleEnd,
    chronological,
    selectedTimeframe,
    candleStep,
  ).map((index, tickIndex, indexes) => ({
    index,
    label: tickLabel(
      chronological[index].barTime,
      selectedTimeframe,
      tickIndex > 0 ? chronological[indexes[tickIndex - 1]].barTime : undefined,
    ),
    x: xAt(index),
  }));
  const activeBar =
    activeIndex === null ? null : (chronological[activeIndex] ?? null);
  const activeX = activeIndex === null ? null : xAt(activeIndex);
  const activeClose = activeBar ? finite(activeBar.close) : null;
  const activeY = activeClose === null ? null : priceY(activeClose);
  const selectedVisible =
    selectedIndex !== null && selectedIndex >= visibleStart && selectedIndex < visibleEnd;
  const selectedBar =
    selectedVisible && selectedIndex !== null
      ? (chronological[selectedIndex] ?? null)
      : null;
  const selectedX =
    selectedVisible && selectedIndex !== null ? xAt(selectedIndex) : null;
  const selectedClose = selectedBar ? finite(selectedBar.close) : null;
  const selectedY = selectedClose === null ? null : priceY(selectedClose);
  const selectedOpen = selectedBar ? finite(selectedBar.open) : null;
  const selectedIsUp =
    selectedOpen === null || selectedClose === null
      ? true
      : selectedClose >= selectedOpen;
  const latestVisibleBar = visibleBars[visibleBars.length - 1] ?? null;
  const latestVisibleClose = latestVisibleBar ? finite(latestVisibleBar.close) : null;
  const latestVisibleOpen = latestVisibleBar ? finite(latestVisibleBar.open) : null;
  const latestVisibleIsUp =
    latestVisibleOpen === null || latestVisibleClose === null
      ? true
      : latestVisibleClose >= latestVisibleOpen;
  const latestVisibleY =
    latestVisibleClose === null ? null : priceY(latestVisibleClose);
  const pointerY = pointerPrice === null ? null : priceY(pointerPrice);
  const tooltipXPercent =
    selectedX === null
      ? 50
      : clamp(
          (selectedX / WIDTH) * 100,
          ((TOOLTIP_WIDTH_PX / 2 + 8) / (WIDTH + STAGE_RIGHT_AXIS_PX)) * 100,
          100 -
            ((TOOLTIP_WIDTH_PX / 2 + STAGE_RIGHT_AXIS_PX + 8) /
              (WIDTH + STAGE_RIGHT_AXIS_PX)) *
              100,
        );
  const tooltipYPercent =
    selectedY === null
      ? 18
      : clamp(
          (selectedY / HEIGHT) * 100,
          ((TOOLTIP_HEIGHT_PX + 10) / HEIGHT) * 100,
          96,
        );

  const handlePointerMove = (event: PointerEvent<SVGSVGElement>) => {
    if (!visibleBars.length) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const relativeX = ((event.clientX - rect.left) / rect.width) * WIDTH;
    const relativeY = ((event.clientY - rect.top) / rect.height) * HEIGHT;
    const pointerPriceValue =
      priceMax -
      ((clamp(relativeY, PAD_TOP, PAD_TOP + PRICE_HEIGHT) - PAD_TOP) /
        PRICE_HEIGHT) *
        span;
    setPointerPrice(pointerPriceValue);
    if (drag) {
      const movedBars = Math.round(
        (((event.clientX - drag.startX) / rect.width) * WIDTH) / candleStep,
      );
      setVisible((state) => ({
        ...state,
        start: clamp(drag.startWindow - movedBars, 0, maxStart),
      }));
      return;
    }
    const index = Math.max(
      visibleStart,
      Math.min(
        visibleEnd - 1,
        visibleStart + Math.round((relativeX - PAD_X) / candleStep),
      ),
    );
    setActiveIndex(index);
  };

  const handlePointerDown = (event: PointerEvent<SVGSVGElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const relativeX = ((event.clientX - rect.left) / rect.width) * WIDTH;
    const startIndex = visibleBars.length
      ? Math.max(
          visibleStart,
          Math.min(
            visibleEnd - 1,
            visibleStart + Math.round((relativeX - PAD_X) / candleStep),
          ),
        )
      : null;
    setActiveIndex(startIndex);
    event.currentTarget.setPointerCapture(event.pointerId);
    setDrag({
      pointerId: event.pointerId,
      startX: event.clientX,
      startIndex,
      startWindow: visibleStart,
    });
  };

  const handlePointerUp = (event: PointerEvent<SVGSVGElement>) => {
    if (drag?.pointerId === event.pointerId) {
      event.currentTarget.releasePointerCapture(event.pointerId);
      if (Math.abs(event.clientX - drag.startX) < 4 && drag.startIndex !== null) {
        setSelectedIndex((current) =>
          current === drag.startIndex ? null : drag.startIndex,
        );
      }
      setDrag(null);
    }
  };

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return undefined;
    const handleWheel = (event: WheelEvent) => {
      if (!totalCount) return;
      // Plain wheel scrolls the page (the chart is large and central — trapping
      // the wheel made Symbol Lab feel un-scrollable). Zoom only with Ctrl/⌘,
      // which is also what a trackpad pinch sends, so pinch-to-zoom still works.
      if (!event.ctrlKey && !event.metaKey) return;
      const current = visibleRef.current;
      const currentCount = clamp(current.count, minVisibleCount, maxVisibleCount);
      const scale = event.deltaY > 0 ? 1.18 : 0.84;
      const nextCount = Math.round(
        clamp(currentCount * scale, minVisibleCount, maxVisibleCount),
      );
      if (nextCount === currentCount) return;
      event.preventDefault();
      const rect = stage.getBoundingClientRect();
      const anchorRatio = clamp((event.clientX - rect.left) / rect.width, 0, 1);
      const currentStart = clamp(
        current.start,
        0,
        Math.max(0, totalCount - currentCount),
      );
      const anchorIndex = currentStart + Math.round(anchorRatio * (currentCount - 1));
      const nextStart = clamp(
        Math.round(anchorIndex - anchorRatio * (nextCount - 1)),
        0,
        Math.max(0, totalCount - nextCount),
      );
      setVisible({ start: nextStart, count: nextCount });
    };
    stage.addEventListener("wheel", handleWheel, { passive: false });
    return () => stage.removeEventListener("wheel", handleWheel);
  }, [maxVisibleCount, minVisibleCount, totalCount]);

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
      testId={testId}
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
              : formatPrice(header.latestClose, currency)}
          </span>
          <Badge tone={dataStatusTone}>{header.dataStatus}</Badge>
        </div>
      </div>

      <div className="fso-symbol-chart-toolbar">
        <div className="fso-symbol-timeframes" aria-label="Chart timeframe">
          {visibleTimeframes.map((item) => (
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
        <div className="fso-symbol-chart-tools">
          <div className="fso-symbol-currency-toggle" aria-label="Price currency">
            {(["USD", "KRW"] as const).map((item) => (
              <button
                key={item}
                type="button"
                className={
                  item === currency
                    ? "fso-symbol-chip fso-symbol-chip--active"
                    : "fso-symbol-chip"
                }
                onClick={() => setCurrency(item)}
              >
                {item}
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
      </div>

      <div className="fso-candlechart" data-testid="symbol-candle-svg">
        <div className="fso-candle-stage" ref={stageRef}>
          <svg
            viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
            preserveAspectRatio="none"
            role="img"
            className={drag ? "fso-candle-svg fso-candle-svg--dragging" : "fso-candle-svg"}
            onPointerMove={handlePointerMove}
            onPointerDown={handlePointerDown}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
            onPointerLeave={() => {
              setActiveIndex(null);
              setPointerPrice(null);
              setDrag(null);
            }}
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
            {timeAxisTicks.map((tick) => (
              <line
                key={`grid-${tick.index}`}
                x1={tick.x}
                x2={tick.x}
                y1={PAD_TOP}
                y2={volumeBase}
                className="fso-candle-time-grid"
              />
            ))}
            {enabled.bollinger ? (
              <>
                <path
                  d={pathFor(visibleBbUpper, (index) => xAt(visibleIndexes[index]), priceY)}
                  className="fso-candle-overlay fso-candle-overlay--band"
                />
                <path
                  d={pathFor(visibleBbLower, (index) => xAt(visibleIndexes[index]), priceY)}
                  className="fso-candle-overlay fso-candle-overlay--band"
                />
              </>
            ) : null}
            {enabled.ema20 ? (
              <path
                d={pathFor(
                  visibleEma20.some(Boolean) ? visibleEma20 : visibleFallbackEma20,
                  (index) => xAt(visibleIndexes[index]),
                  priceY,
                )}
                className="fso-candle-overlay fso-candle-overlay--ema20"
              />
            ) : null}
            {enabled.ema60 ? (
              <path
                d={pathFor(
                  visibleEma60.some(Boolean) ? visibleEma60 : visibleFallbackEma60,
                  (index) => xAt(visibleIndexes[index]),
                  priceY,
                )}
                className="fso-candle-overlay fso-candle-overlay--ema60"
              />
            ) : null}
            {enabled.ema120 ? (
              <path
                d={pathFor(
                  visibleEma120.some(Boolean)
                    ? visibleEma120
                    : visibleFallbackEma120,
                  (index) => xAt(visibleIndexes[index]),
                  priceY,
                )}
                className="fso-candle-overlay fso-candle-overlay--ema120"
              />
            ) : null}
            {visibleBars.map((bar, visibleIndex) => {
              const index = visibleStart + visibleIndex;
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
            {activeX !== null ? (
              <>
                <line
                  x1={activeX}
                  x2={activeX}
                  y1={PAD_TOP}
                  y2={volumeBase}
                  className="fso-candle-crosshair"
                />
                {pointerY !== null ? (
                  <line
                    x1={PAD_X}
                    x2={WIDTH - PAD_X}
                    y1={pointerY}
                    y2={pointerY}
                    className="fso-candle-crosshair"
                  />
                ) : null}
                {activeY !== null ? (
                  <circle
                    cx={activeX}
                    cy={activeY}
                    r={3.2}
                    className="fso-candle-crosshair-dot"
                  />
                ) : null}
              </>
            ) : null}
          </svg>
          <div className="fso-candle-right-axis" aria-hidden>
            {priceAxisLabels.map((item) => (
              <span
                key={`${item.label}-${item.y}`}
                className="fso-candle-right-axis-label fso-candle-right-axis-label--price"
                style={{ top: `${(item.y / HEIGHT) * 100}%` }}
              >
                {item.label}
              </span>
            ))}
            {volumeAxisLabels.map((item) => (
              <span
                key={`volume-${item.label}-${item.y}`}
                className="fso-candle-right-axis-label fso-candle-right-axis-label--volume"
                style={{ top: `${(item.y / HEIGHT) * 100}%` }}
              >
                {item.label}
              </span>
            ))}
            {latestVisibleClose !== null && latestVisibleY !== null ? (
              <span
                className={
                  latestVisibleIsUp
                    ? "fso-candle-right-axis-label fso-candle-right-axis-label--last fso-candle-right-axis-label--last-up"
                    : "fso-candle-right-axis-label fso-candle-right-axis-label--last fso-candle-right-axis-label--last-down"
                }
                style={{ top: `${(latestVisibleY / HEIGHT) * 100}%` }}
              >
                {formatAxisPrice(latestVisibleClose, currency)}
              </span>
            ) : null}
            {pointerPrice !== null && pointerY !== null ? (
              <span
                className="fso-candle-right-axis-label fso-candle-right-axis-label--pointer"
                style={{ top: `${(pointerY / HEIGHT) * 100}%` }}
              >
                {formatAxisPrice(pointerPrice, currency)}
              </span>
            ) : null}
          </div>
          {selectedBar && selectedX !== null ? (
            <div
              className={
                selectedIsUp
                  ? "fso-candle-tooltip fso-candle-tooltip--up"
                  : "fso-candle-tooltip fso-candle-tooltip--down"
              }
              style={{
                left: `${tooltipXPercent}%`,
                top: `${tooltipYPercent}%`,
              }}
            >
              <div className="fso-candle-tooltip-head">
                <strong>{fullTimestamp(selectedBar.barTime, selectedTimeframe)}</strong>
                <span>{selectedTimeframe.toUpperCase()}</span>
              </div>
              <dl>
                <div>
                  <dt>Open</dt>
                  <dd>{formatPrice(selectedBar.open, currency)}</dd>
                </div>
                <div>
                  <dt>High</dt>
                  <dd>{formatPrice(selectedBar.high, currency)}</dd>
                </div>
                <div>
                  <dt>Low</dt>
                  <dd>{formatPrice(selectedBar.low, currency)}</dd>
                </div>
                <div>
                  <dt>Close</dt>
                  <dd>{formatPrice(selectedBar.close, currency)}</dd>
                </div>
                <div>
                  <dt>Volume</dt>
                  <dd>{formatVolume(selectedBar.volume)}</dd>
                </div>
                <div>
                  <dt>EMA20</dt>
                  <dd>{formatPrice(selectedBar.ema20, currency)}</dd>
                </div>
                <div>
                  <dt>EMA60</dt>
                  <dd>{formatPrice(selectedBar.ema60, currency)}</dd>
                </div>
                <div>
                  <dt>EMA120</dt>
                  <dd>{formatPrice(selectedBar.ema120, currency)}</dd>
                </div>
                <div>
                  <dt>BB Upper</dt>
                  <dd>{formatPrice(selectedBar.bbUpper, currency)}</dd>
                </div>
                <div>
                  <dt>BB Lower</dt>
                  <dd>{formatPrice(selectedBar.bbLower, currency)}</dd>
                </div>
              </dl>
            </div>
          ) : null}
        </div>
        <div className="fso-linechart-axislabels" aria-hidden>
          {timeAxisTicks.length ? (
            timeAxisTicks.map((tick) => (
              <span
                key={`${tick.index}-${tick.label}`}
                className="fso-linechart-axislabel"
                style={{ left: `${(tick.x / WIDTH) * 100}%` }}
              >
                {tick.label}
              </span>
            ))
          ) : (
            <span>No candle data</span>
          )}
        </div>
        <p className="fso-linechart-caption">
          Snapshot candles + volume · drag to pan · ⌘/Ctrl + scroll to zoom · no execution
        </p>
      </div>
    </Panel>
  );
}
