import { Panel } from "@/shared/ui";

export interface MissingDataPanelProps {
  tickers: string[];
  setupHint: string | null;
}

export function MissingDataPanel({ tickers, setupHint }: MissingDataPanelProps) {
  if (tickers.length === 0 && !setupHint) {
    return null;
  }
  return (
    <Panel
      title="Missing Data"
      badge={`${tickers.length}`}
      badgeTone="warning"
      testId="analysis-workspace-missing-data"
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
      ) : null}
    </Panel>
  );
}
