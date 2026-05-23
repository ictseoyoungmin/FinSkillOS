import { Panel } from "@/shared/ui";

export interface MissingDataPanelProps {
  tickers: string[];
  setupHint: string | null;
}

export function MissingDataPanel({ tickers, setupHint }: MissingDataPanelProps) {
  return (
    <Panel
      title="Missing Data"
      badge={`${tickers.length}`}
      badgeTone="warning"
      testId="missing-data-panel"
    >
      {setupHint ? (
        <p className="fso-missing-hint">{setupHint}</p>
      ) : null}
      {tickers.length > 0 ? (
        <ul className="fso-missing-list">
          {tickers.map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ul>
      ) : (
        <p className="fso-missing-hint">No missing data in this snapshot.</p>
      )}
    </Panel>
  );
}
