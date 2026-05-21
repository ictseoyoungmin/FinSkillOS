import { Panel } from "@/shared/ui";

export interface SymbolWatchpointsProps {
  watchpoints: string[];
  interpretation: string;
  safetyCaption: string;
}

export function SymbolWatchpoints({
  watchpoints,
  interpretation,
  safetyCaption,
}: SymbolWatchpointsProps) {
  return (
    <Panel
      title="Watchpoints + Interpretation"
      badge="Read-only"
      badgeTone="neutral"
      testId="symbol-watchpoints"
    >
      <p className="fso-kernel-interpretation">{interpretation}</p>
      {watchpoints.length > 0 ? (
        <ul className="fso-kernel-watchpoints">
          {watchpoints.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      ) : null}
      <small
        className="fso-kernel-safety"
        data-testid="symbol-watchpoints-safety-caption"
      >
        {safetyCaption}
      </small>
    </Panel>
  );
}
