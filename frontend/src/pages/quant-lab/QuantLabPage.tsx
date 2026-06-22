import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import {
  decodeSpecParam,
  fetchQuantLab,
  runQuantLabSpec,
} from "@/features/quant-lab/api";
import { QuantControls } from "@/features/quant-lab/components/QuantControls";
import { QuantEquityChart } from "@/features/quant-lab/components/QuantEquityChart";
import { QuantMetricsPanel } from "@/features/quant-lab/components/QuantMetricsPanel";
import { QuantReplayPanel } from "@/features/quant-lab/components/QuantReplayPanel";
import { QuantStrategyPanel } from "@/features/quant-lab/components/QuantStrategyPanel";
import { JudgmentHeader, Panel, SafetyCaption, SectionHeader } from "@/shared/ui";
import "./quant-lab.css";

export function QuantLabPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const strategy = searchParams.get("strategy") ?? undefined;
  const ticker = searchParams.get("ticker") ?? undefined;
  const specParam = searchParams.get("spec") ?? undefined;
  const customSpec = useMemo(
    () => (specParam ? decodeSpecParam(specParam) : null),
    [specParam],
  );

  const { data, error, isPending, isFetching } = useQuery({
    queryKey: ["quant-lab", specParam ?? "", strategy ?? "", ticker ?? ""],
    queryFn: ({ signal }) =>
      customSpec
        ? runQuantLabSpec(customSpec, signal)
        : fetchQuantLab(strategy, ticker, signal),
    placeholderData: keepPreviousData,
  });

  const setParam = (key: "strategy" | "ticker", value: string) => {
    const next = new URLSearchParams(searchParams);
    next.set(key, value);
    // Picking a built-in strategy/ticker leaves any custom-spec deep-link.
    next.delete("spec");
    if (key === "strategy") next.delete("ticker");
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
            autoPlay={Boolean(specParam || (strategy && ticker))}
          />
          <QuantEquityChart curve={data.equityCurve} ticker={data.strategy.ticker} />
          <QuantMetricsPanel metrics={data.metrics} />
        </div>
        <div className="fso-quant-side">
          <QuantStrategyPanel
            strategy={data.strategy}
            segments={data.exposureSegments}
            regimeCovered={data.dataState.regimeCovered}
          />
          <Panel title="Data state" testId="quant-data-state">
            <dl className="fso-quant-spec">
              <div>
                <dt>출처</dt>
                <dd>{data.dataState.source}</dd>
              </div>
              <div>
                <dt>바 수</dt>
                <dd>{data.dataState.barCount}</dd>
              </div>
            </dl>
            <p className="fso-quant-note">{data.dataState.dataNote}</p>
          </Panel>
        </div>
      </div>
    </div>
  );
}
