import { Panel } from "@/shared/ui";

export interface MarketKernelInterpretationProps {
  watchpoints: string[];
  interpretation: string;
  safetyCaption: string;
}

export function MarketKernelInterpretation({
  watchpoints,
  interpretation,
  safetyCaption,
}: MarketKernelInterpretationProps) {
  return (
    <Panel
      title="Interpretation"
      badge="Read-only"
      badgeTone="neutral"
      testId="market-kernel-interpretation"
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
        data-testid="market-kernel-safety-caption"
      >
        {safetyCaption}
      </small>
    </Panel>
  );
}
