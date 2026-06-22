import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { LineChart } from "@/shared/charts/LineChart";
import { Metric, Panel } from "@/shared/ui";
import { fetchQuantLabPortfolio, portfolioQuantLabSpec } from "../api";

export interface QuantPortfolioPanelProps {
  strategyId: string;
  strategyName: string;
  customSpec: Record<string, unknown> | null;
}

function pct(v: number | null): string {
  return v === null || !Number.isFinite(v) ? "—" : `${(v * 100).toFixed(1)}%`;
}

function ratio(v: number | null): string {
  return v === null || !Number.isFinite(v) ? "—" : v.toFixed(2);
}

/**
 * Equal-weight multi-asset portfolio synthesis: the same strategy run on each
 * ticker and combined into one capital curve vs an equal-weight buy-and-hold
 * benchmark. On-demand (server-side backtests). Descriptive — not advice.
 */
export function QuantPortfolioPanel({
  strategyId,
  strategyName,
  customSpec,
}: QuantPortfolioPanelProps) {
  const [open, setOpen] = useState(false);
  const isCustom = strategyId === "CUSTOM";

  const { data, isFetching, error } = useQuery({
    queryKey: ["quant-portfolio", strategyId, isCustom ? "custom" : strategyId],
    queryFn: ({ signal }) =>
      isCustom && customSpec
        ? portfolioQuantLabSpec(customSpec, signal)
        : fetchQuantLabPortfolio(strategyId, undefined, signal),
    enabled: open,
  });

  return (
    <Panel title="Portfolio synthesis" testId="quant-portfolio">
      <p className="fso-quant-note">
        '{strategyName}'을 여러 종목에 동일가중으로 합성한 단일 자본곡선 (vs 동일가중 보유).
      </p>
      {!open ? (
        <button
          className="fso-chat-confirm"
          onClick={() => setOpen(true)}
          data-testid="quant-portfolio-run"
        >
          포트폴리오 합성하기 ▶
        </button>
      ) : isFetching ? (
        <p className="fso-quant-note" role="status">
          포트폴리오 백테스트 중…
        </p>
      ) : error ? (
        <p className="fso-quant-empty" role="alert">
          포트폴리오를 불러올 수 없습니다.
        </p>
      ) : data && data.curve.length > 0 ? (
        <>
          <p className="fso-quant-note">
            종목 {data.tickers.length}개 · 각 {(data.weight * 100).toFixed(1)}% 가중:{" "}
            {data.tickers.join(", ")}
          </p>
          <LineChart
            labels={data.curve.map((p) => p.date)}
            series={[
              {
                name: "포트폴리오",
                values: data.curve.map((p) => p.strategy),
                tone: "primary",
              },
              {
                name: "동일가중 보유",
                values: data.curve.map((p) => p.benchmark),
                tone: "muted",
                dashed: true,
              },
            ]}
            height={240}
            valueFormat={(v) => v.toFixed(3)}
            testId="quant-portfolio-chart"
            caption="동일가중 합성 자본곡선 (1.0 = 시작 자본)."
          />
          <div className="fso-quant-metrics-grid">
            <Metric label="누적 수익" value={pct(data.metrics.totalReturn)} />
            <Metric label="CAGR" value={pct(data.metrics.cagr)} />
            <Metric label="Sharpe" value={ratio(data.metrics.sharpe)} />
            <Metric label="최대 낙폭" value={pct(data.metrics.maxDrawdown)} />
            <Metric label="평균 보유" value={pct(data.metrics.exposurePct)} />
          </div>
        </>
      ) : (
        <p className="fso-quant-empty">합성할 종목 데이터가 부족합니다.</p>
      )}
    </Panel>
  );
}
