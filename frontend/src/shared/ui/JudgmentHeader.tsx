import type { JudgmentHeaderData } from "@/shared/types/evidence";
import "./judgment-header.css";

export interface JudgmentHeaderProps {
  judgment: JudgmentHeaderData;
}

function confidenceTone(confidence: number): "success" | "warning" | "danger" {
  if (confidence >= 75) return "success";
  if (confidence >= 55) return "warning";
  return "danger";
}

export function JudgmentHeader({ judgment }: JudgmentHeaderProps) {
  const tone = confidenceTone(judgment.confidence);

  return (
    <section className="fso-judgment-header" data-testid="judgment-header">
      <div className="fso-judgment-copy">
        <p className="fso-judgment-eyebrow">{judgment.eyebrow}</p>
        <h1 className="fso-judgment-title">
          {judgment.title}
          {judgment.accent ? (
            <span className="fso-judgment-accent"> {judgment.accent}</span>
          ) : null}
        </h1>
        <p className="fso-judgment-summary">{judgment.summary}</p>
      </div>
      <div className="fso-judgment-confidence" data-tone={tone}>
        <span className="fso-judgment-confidence-label">Confidence</span>
        <strong>{judgment.confidence}%</strong>
        <span className="fso-judgment-confidence-meter" aria-hidden>
          <span style={{ width: `${judgment.confidence}%` }} />
        </span>
      </div>
    </section>
  );
}

