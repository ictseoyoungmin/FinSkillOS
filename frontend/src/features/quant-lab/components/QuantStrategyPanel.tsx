import { Panel } from "@/shared/ui";
import type { QuantSegment, QuantStrategySummary } from "../types";

export interface QuantStrategyPanelProps {
  strategy: QuantStrategySummary;
  segments: QuantSegment[];
  regimeCovered: boolean;
}

/**
 * The declarative spec shown as evidence — entry/exit conditions in the
 * cockpit's own feature vocabulary, plus the simulated exposure windows. This
 * is *what was simulated*, never a recommendation.
 */
export function QuantStrategyPanel({
  strategy,
  segments,
  regimeCovered,
}: QuantStrategyPanelProps) {
  return (
    <Panel title="Strategy spec" testId="quant-strategy">
      <p className="fso-quant-strategy-desc">{strategy.description}</p>
      <dl className="fso-quant-spec">
        <div>
          <dt>매수 조건</dt>
          <dd data-testid="quant-entry">{strategy.entryText}</dd>
        </div>
        <div>
          <dt>매도 조건</dt>
          <dd data-testid="quant-exit">{strategy.exitText}</dd>
        </div>
        <div>
          <dt>대상</dt>
          <dd>{strategy.ticker}</dd>
        </div>
        <div>
          <dt>Regime 피처</dt>
          <dd>{regimeCovered ? "구간 일부에 regime 히스토리 적용" : "regime 미적용 (히스토리 없음)"}</dd>
        </div>
      </dl>
      <h4 className="fso-quant-seg-head">보유 구간 ({segments.length})</h4>
      {segments.length > 0 ? (
        <ul className="fso-quant-segments" data-testid="quant-segments">
          {segments.map((seg) => (
            <li key={`${seg.start}-${seg.end}`}>
              <span className="fso-quant-seg-dot" aria-hidden />
              {seg.start} → {seg.end}
            </li>
          ))}
        </ul>
      ) : (
        <p className="fso-quant-empty">매수 구간이 없습니다.</p>
      )}
    </Panel>
  );
}
