import { Badge, Panel } from "@/shared/ui";
import { toNumber } from "@/shared/lib/format";
import type { TapeStrengthEntry } from "../types";
import "./tape-strength-cards.css";

export interface TapeStrengthCardsProps {
  strongest: TapeStrengthEntry[];
  weakest: TapeStrengthEntry[];
}

function ScoreList({
  entries,
  emptyMessage,
  testId,
}: {
  entries: TapeStrengthEntry[];
  emptyMessage: string;
  testId: string;
}) {
  if (entries.length === 0) {
    return (
      <p className="fso-tape-strength-empty" data-testid={testId}>
        {emptyMessage}
      </p>
    );
  }
  return (
    <ul className="fso-tape-strength-list" data-testid={testId}>
      {entries.map((entry) => {
        const score = toNumber(entry.relativeStrengthScore);
        return (
          <li key={entry.ticker}>
            <strong>{entry.ticker}</strong>
            <span className="fso-tape-strength-label">{entry.label}</span>
            <span
              className={`fso-tape-strength-score ${
                score >= 0 ? "fso-tape-strength-pos" : "fso-tape-strength-neg"
              }`}
            >
              {score >= 0 ? "+" : ""}
              {score.toFixed(2)}
            </span>
            {entry.trendState ? (
              <Badge tone={score >= 0 ? "success" : "warning"}>
                {entry.trendState}
              </Badge>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

export function TapeStrengthCards({
  strongest,
  weakest,
}: TapeStrengthCardsProps) {
  return (
    <div className="fso-tape-strength-grid" data-testid="tape-strength-cards">
      <Panel
        title="Strongest"
        badge="Top 3"
        badgeTone="success"
        testId="relative-strength-ranking"
      >
        <ScoreList
          entries={strongest}
          emptyMessage="No ranked instruments yet."
          testId="analysis-workspace-strongest-list"
        />
      </Panel>
      <Panel
        title="Weakest"
        badge="Bottom 3"
        badgeTone="warning"
        testId="analysis-workspace-weakest"
      >
        <ScoreList
          entries={weakest}
          emptyMessage="No ranked instruments yet."
          testId="analysis-workspace-weakest-list"
        />
      </Panel>
    </div>
  );
}
