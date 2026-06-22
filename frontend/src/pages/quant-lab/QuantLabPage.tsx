import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import {
  decodeSpecParam,
  fetchQuantLab,
  fetchQuantLabSaved,
  runQuantLabSpec,
} from "@/features/quant-lab/api";
import { QuantControls } from "@/features/quant-lab/components/QuantControls";
import { QuantDataPrepPanel } from "@/features/quant-lab/components/QuantDataPrepPanel";
import { QuantEquityChart } from "@/features/quant-lab/components/QuantEquityChart";
import { QuantMetricsPanel } from "@/features/quant-lab/components/QuantMetricsPanel";
import { QuantPortfolioPanel } from "@/features/quant-lab/components/QuantPortfolioPanel";
import { QuantSavedPanel } from "@/features/quant-lab/components/QuantSavedPanel";
import { QuantScreenPanel } from "@/features/quant-lab/components/QuantScreenPanel";
import { QuantReplayPanel } from "@/features/quant-lab/components/QuantReplayPanel";
import { QuantStrategyPanel } from "@/features/quant-lab/components/QuantStrategyPanel";
import { QuantWalkForwardPanel } from "@/features/quant-lab/components/QuantWalkForwardPanel";
import { JudgmentHeader, Panel, SafetyCaption, SectionHeader } from "@/shared/ui";
import "./quant-lab.css";

export function QuantLabPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const strategy = searchParams.get("strategy") ?? undefined;
  const ticker = searchParams.get("ticker") ?? undefined;
  const specParam = searchParams.get("spec") ?? undefined;
  const savedParam = searchParams.get("saved") ?? undefined;
  const customSpec = useMemo(
    () => (specParam ? decodeSpecParam(specParam) : null),
    [specParam],
  );

  const { data, error, isPending, isFetching } = useQuery({
    queryKey: ["quant-lab", savedParam ?? "", specParam ?? "", strategy ?? "", ticker ?? ""],
    queryFn: ({ signal }) =>
      savedParam
        ? fetchQuantLabSaved(savedParam, signal)
        : customSpec
          ? runQuantLabSpec(customSpec, signal)
          : fetchQuantLab(strategy, ticker, signal),
    placeholderData: keepPreviousData,
  });

  const setParam = (key: "strategy" | "ticker", value: string) => {
    const next = new URLSearchParams(searchParams);
    next.set(key, value);
    // Picking a built-in strategy/ticker drops any custom-spec / saved deep-link.
    next.delete("spec");
    next.delete("saved");
    if (key === "strategy") next.delete("ticker");
    setSearchParams(next, { replace: true });
  };

  const loadSaved = (savedId: string) => {
    const next = new URLSearchParams();
    next.set("saved", savedId);
    setSearchParams(next, { replace: true });
  };

  const warnings = useMemo(() => data?.warnings ?? [], [data]);

  if (isPending && !data) {
    return (
      <div className="fso-quant-lab" data-testid="quant-lab-page">
        <SectionHeader eyebrow="FinSkillOS · Module" title="Quant Lab" />
        <Panel title="Loading" testId="quant-lab-loading">
          <p className="fso-quant-note" role="status">
            시뮬레이션 결과를 불러오는 중…
          </p>
        </Panel>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="fso-quant-lab" data-testid="quant-lab-page">
        <SectionHeader eyebrow="FinSkillOS · Module" title="Quant Lab" />
        <Panel title="Unavailable" badge="error" badgeTone="danger" testId="quant-lab-error">
          <p className="fso-quant-note" role="alert">
            {error instanceof Error
              ? error.message
              : "Quant Lab 시뮬레이션을 불러올 수 없습니다."}
          </p>
        </Panel>
      </div>
    );
  }

  return (
    <div className="fso-quant-lab" data-testid="quant-lab-page">
      <SectionHeader eyebrow="FinSkillOS · Module" title="Quant Lab" />
      <JudgmentHeader judgment={data.judgment} />
      <SafetyCaption>{data.safetyCaption}</SafetyCaption>

      <QuantControls
        strategies={data.availableStrategies}
        tickers={
          data.availableTickers.includes(data.strategy.ticker)
            ? data.availableTickers
            : [data.strategy.ticker, ...data.availableTickers]
        }
        selectedStrategy={data.strategy.id}
        selectedTicker={data.strategy.ticker}
        busy={isFetching}
        onStrategyChange={(id) => setParam("strategy", id)}
        onTickerChange={(t) => setParam("ticker", t)}
      />

      {warnings.length > 0 ? (
        <Panel title="Notes" testId="quant-warnings" badge={`${warnings.length}`} badgeTone="warning">
          <ul className="fso-quant-warnings">
            {warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </Panel>
      ) : null}

      <div className="fso-quant-grid">
        <div className="fso-quant-main">
          <QuantReplayPanel
            curve={data.equityCurve}
            markers={data.markers}
            ticker={data.strategy.ticker}
            autoPlay={Boolean(specParam || savedParam || (strategy && ticker))}
          />
          <QuantEquityChart curve={data.equityCurve} ticker={data.strategy.ticker} />
          <QuantMetricsPanel metrics={data.metrics} />
          <QuantWalkForwardPanel windows={data.walkForward} />
          <QuantPortfolioPanel
            strategyId={data.strategy.id}
            strategyName={data.strategy.name}
            customSpec={customSpec}
          />
        </div>
        <div className="fso-quant-side">
          <QuantStrategyPanel
            strategy={data.strategy}
            segments={data.exposureSegments}
            regimeCovered={data.dataState.regimeCovered}
          />
          <QuantScreenPanel
            strategyId={data.strategy.id}
            strategyName={data.strategy.name}
            currentTicker={data.strategy.ticker}
            customSpec={customSpec}
            onPick={(t) => setParam("ticker", t)}
          />
          <QuantDataPrepPanel coverage={data.coverage} dataState={data.dataState} />
          <QuantSavedPanel customSpec={customSpec} onLoad={loadSaved} />
        </div>
      </div>
    </div>
  );
}
