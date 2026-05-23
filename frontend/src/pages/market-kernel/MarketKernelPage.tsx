import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchMarketKernel } from "@/features/market/api";
import { CandlePanel } from "@/features/market/components/CandlePanel";
import { EventOverlayPanel } from "@/features/market/components/EventOverlayPanel";
import { IndicatorSnapshotPanel } from "@/features/market/components/IndicatorSnapshotPanel";
import { MarketKernelInterpretation } from "@/features/market/components/MarketKernelInterpretation";
import { SymbolUniverseRail } from "@/features/market/components/SymbolUniverseRail";
import { TickerSearch } from "@/features/market/components/TickerSearch";
import { marketKernelFixture } from "@/mocks/fixtures/marketKernel.fixture";
import {
  ConflictsPanel,
  DriversPanel,
  EmptyState,
  InterpretationPanel,
  JudgmentHeader,
  SafetyCaption,
  SectionHeader,
  WatchpointsPanel,
} from "@/shared/ui";
import "./market-kernel.css";

const DEFAULT_TICKER = "NVDA";
const TIMEFRAMES = ["1D", "1W", "1M"] as const;

export function MarketKernelPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const ticker = (searchParams.get("ticker") ?? DEFAULT_TICKER).toUpperCase();
  const [timeframe, setTimeframe] = useState<(typeof TIMEFRAMES)[number]>("1D");

  const { data, error } = useQuery({
    queryKey: ["market-kernel", ticker],
    queryFn: ({ signal }) => fetchMarketKernel(ticker, signal),
    placeholderData: marketKernelFixture(ticker),
  });

  const selectSymbol = (symbol: string) => {
    const next = new URLSearchParams(searchParams);
    next.set("ticker", symbol);
    setSearchParams(next, { replace: false });
  };

  if (error && !data) {
    return (
      <EmptyState
        testId="market-kernel-error"
        title="Market Kernel is unavailable"
        message={
          "The API is unreachable and no fixture is cached. " +
          "Check the FastAPI container and reload."
        }
      />
    );
  }

  const payload = data ?? marketKernelFixture(ticker);

  return (
    <div className="fso-market-kernel" data-testid="market-kernel-page">
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
            <div
              className="fso-market-kernel-timeframes"
              role="tablist"
              data-testid="market-kernel-timeframes"
              aria-label="Chart timeframe"
            >
              {TIMEFRAMES.map((tf) => (
                <button
                  key={tf}
                  type="button"
                  role="tab"
                  aria-selected={tf === timeframe}
                  className={`fso-market-kernel-tf ${
                    tf === timeframe ? "fso-market-kernel-tf--active" : ""
                  }`.trim()}
                  onClick={() => setTimeframe(tf)}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          {payload.setupHint ? (
            <EmptyState
              testId="market-kernel-setup-hint"
              title="Limited data available"
              message={payload.setupHint}
            />
          ) : null}

          <div data-testid="market-kernel-chart-panel">
            <CandlePanel header={payload.header} bars={payload.bars} />
          </div>
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
      <InterpretationPanel
        bullets={[
          payload.integratedInterpretation.verdict,
          payload.integratedInterpretation.whyItMatters,
          payload.integratedInterpretation.whatRemainsUncertain,
        ]}
      />
      <WatchpointsPanel
        watchpoints={payload.reviewWatchpoints.map((watchpoint) => ({
          label: watchpoint.title,
          description: watchpoint.note,
        }))}
      />
      <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
    </div>
  );
}
