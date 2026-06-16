import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchMarketKernel } from "@/features/market/api";
import { SymbolCandlestickChart } from "@/features/symbol/components/SymbolCandlestickChart";
import { EventOverlayPanel } from "@/features/market/components/EventOverlayPanel";
import { IndicatorSnapshotPanel } from "@/features/market/components/IndicatorSnapshotPanel";
import { MarketKernelInterpretation } from "@/features/market/components/MarketKernelInterpretation";
import { AddToCollectionFolder } from "@/features/collection-control/components/AddToCollectionFolder";
import { SymbolUniverseRail } from "@/features/market/components/SymbolUniverseRail";
import { TickerSearch } from "@/features/market/components/TickerSearch";
import { marketKernelFixture } from "@/mocks/fixtures/marketKernel.fixture";
import {
  Badge,
  ConflictsPanel,
  DriversPanel,
  EmptyState,
  JudgmentHeader,
  SafetyCaption,
  SectionHeader,
  StatusPill,
} from "@/shared/ui";
import type { BadgeTone } from "@/shared/ui/Badge";
import type { MarketKernelData } from "@/features/market/kernel-types";
import "./market-kernel.css";

const DEFAULT_TICKER = "NVDA";
const TIMEFRAMES = ["1D", "1W", "1M"] as const;
const TIMEFRAME_API: Record<(typeof TIMEFRAMES)[number], string> = {
  "1D": "1d",
  "1W": "1wk",
  "1M": "1mo",
};
// The shared chart emits API timeframe values; map them back to the page's labels.
const API_TO_TIMEFRAME: Record<string, (typeof TIMEFRAMES)[number]> = {
  "1d": "1D",
  "1wk": "1W",
  "1mo": "1M",
};
const CHART_TIMEFRAMES = ["1d", "1wk", "1mo"] as const;

export function MarketKernelPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const ticker = (searchParams.get("ticker") ?? DEFAULT_TICKER).toUpperCase();
  const [timeframe, setTimeframe] = useState<(typeof TIMEFRAMES)[number]>("1D");

  const { data, error } = useQuery({
    queryKey: ["market-kernel", ticker, timeframe],
    queryFn: ({ signal }) =>
      fetchMarketKernel(ticker, TIMEFRAME_API[timeframe], signal),
    placeholderData: marketKernelFixture(ticker),
  });

  const selectSymbol = (symbol: string) => {
    const next = new URLSearchParams(searchParams);
    next.set("ticker", symbol);
    setSearchParams(next, { replace: false });
  };

  const payload = data ?? marketKernelFixture(ticker);

  return (
    <div className="fso-market-kernel" data-testid="market-kernel-page">
      {error ? (
        <StatusPill
          label="Live data unavailable — showing sample shape, not live data"
          tone="warning"
          testId="market-kernel-live-failed"
        />
      ) : null}
      <SectionHeader
        eyebrow="FinSkillOS · Module"
        title="Market Kernel"
      />
      <div className="fso-v42-topline">
        <JudgmentHeader judgment={payload.judgment} />
        <DriversPanel
          drivers={payload.drivers.map((driver) => ({
            label: driver.title,
            value: driver.score,
            detail: driver.note,
          }))}
        />
        <ConflictsPanel
          conflicts={payload.conflicts.map((conflict) => ({
            label: conflict.title,
            description: conflict.note,
          }))}
        />
      </div>
      <MarketKernelDataStateBand payload={payload} />
      <div className="fso-market-kernel-grid">
        <SymbolUniverseRail
          universe={payload.universe}
          activeSymbol={payload.header.ticker}
          onSelect={selectSymbol}
        />
        <div className="fso-market-kernel-main">
          <div className="fso-market-kernel-toolbar">
            <TickerSearch
              initialValue={payload.header.ticker}
              onSubmit={selectSymbol}
            />
            <AddToCollectionFolder ticker={payload.header.ticker} />
          </div>

          {payload.setupHint ? (
            <EmptyState
              testId="market-kernel-setup-hint"
              title="Limited data available"
              message={payload.setupHint}
            />
          ) : null}

          <div data-testid="market-kernel-chart-panel">
            <SymbolCandlestickChart
              header={{
                ticker: payload.header.ticker,
                timeframe: payload.header.timeframe,
                latestClose: payload.header.latestClose,
                latestTime: payload.header.latestTime,
                dataStatus: payload.header.dataStatus,
              }}
              bars={payload.bars}
              selectedTimeframe={TIMEFRAME_API[timeframe]}
              onTimeframeChange={(value) =>
                setTimeframe(API_TO_TIMEFRAME[value] ?? "1D")
              }
              timeframes={CHART_TIMEFRAMES}
              testId="chart-panel"
            />
          </div>
          {/* v4.2 (273): the meta Integrated Interpretation + review Watchpoints
              ("Market Kernel is reading…", "Refresh timestamp") were boilerplate;
              MarketKernelInterpretation in the side rail carries the substantive
              read + safety caption. */}
        </div>
        <aside className="fso-market-kernel-side" aria-label="Market interpretation">
          <IndicatorSnapshotPanel indicators={payload.indicators} />
          <EventOverlayPanel events={payload.events} />
          <MarketKernelInterpretation
            interpretation={payload.interpretation}
            watchpoints={payload.watchpoints}
            safetyCaption={payload.safetyCaption}
          />
        </aside>
      </div>
      <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
    </div>
  );
}

function MarketKernelDataStateBand({ payload }: { payload: MarketKernelData }) {
  const state = payload.dataState;
  const sourceLabel = payload.source === "live" ? "LIVE" : "FIXTURE";
  const sourceTone: BadgeTone = payload.source === "live" ? "success" : "warning";
  const coverageTone = coverageToneFor(state.coverageLevel);
  const indicatorTone = indicatorToneFor(state.indicatorStatus);
  const eventTone: BadgeTone =
    state.eventOverlayStatus === "AVAILABLE" ? "info" : "neutral";
  const latestLabel = state.latestBarAt
    ? state.latestBarAt.slice(0, 10)
    : "No latest bar";

  return (
    <div
      className="fso-market-kernel-state-band"
      data-testid="market-kernel-data-state"
    >
      <MarketKernelStateItem
        label="Source"
        value={sourceLabel}
        detail={state.sourceNote}
        tone={sourceTone}
      />
      <MarketKernelStateItem
        label="Coverage"
        value={state.coverageLevel}
        detail={`${state.barCount} bars · ${state.evidenceCoveragePercent}% evidence · ${latestLabel}`}
        tone={coverageTone}
      />
      <MarketKernelStateItem
        label="Indicators"
        value={state.indicatorStatus}
        detail={state.refreshNote}
        tone={indicatorTone}
      />
      <MarketKernelStateItem
        label="Events"
        value={state.eventOverlayStatus}
        detail={
          payload.events.length > 0
            ? `${payload.events.length} overlays linked to this symbol`
            : state.missingSummary
        }
        tone={eventTone}
      />
    </div>
  );
}

function coverageToneFor(
  level: MarketKernelData["dataState"]["coverageLevel"],
): BadgeTone {
  if (level === "COMPLETE") {
    return "success";
  }
  if (level === "PARTIAL" || level === "SPARSE") {
    return "warning";
  }
  return "neutral";
}

function indicatorToneFor(
  status: MarketKernelData["dataState"]["indicatorStatus"],
): BadgeTone {
  if (status === "AVAILABLE") {
    return "success";
  }
  if (status === "PARTIAL") {
    return "warning";
  }
  return "neutral";
}

interface MarketKernelStateItemProps {
  label: string;
  value: string;
  detail: string;
  tone: BadgeTone;
}

function MarketKernelStateItem({
  label,
  value,
  detail,
  tone,
}: MarketKernelStateItemProps) {
  return (
    <div className="fso-market-kernel-state-item">
      <span>{label}</span>
      <Badge tone={tone}>{value}</Badge>
      <small>{detail}</small>
    </div>
  );
}
