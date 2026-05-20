import "./preparation-score-dial.css";

export interface PreparationScoreDialProps {
  /** 0–100 preparation score (NOT a price prediction). */
  score: number;
}

const RADIUS = 60;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function bandLabel(score: number): string {
  if (score < 20) return "Defensive";
  if (score < 45) return "Measured";
  if (score < 70) return "Constructive";
  if (score < 85) return "Elevated";
  return "Overheat";
}

export function PreparationScoreDial({ score }: PreparationScoreDialProps) {
  const clamped = Math.max(0, Math.min(100, score));
  const offset = CIRCUMFERENCE * (1 - clamped / 100);

  return (
    <div className="fso-dial" data-testid="preparation-score-dial">
      <svg viewBox="0 0 160 160" className="fso-dial-svg" aria-hidden>
        <circle
          cx="80"
          cy="80"
          r={RADIUS}
          className="fso-dial-track"
          fill="none"
          strokeWidth={10}
        />
        <circle
          cx="80"
          cy="80"
          r={RADIUS}
          className="fso-dial-progress"
          fill="none"
          strokeWidth={10}
          strokeLinecap="round"
          transform="rotate(-90 80 80)"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="fso-dial-meta">
        <span className="fso-dial-label">Prep Score</span>
        <span className="fso-dial-value">{clamped}</span>
        <span className="fso-dial-band">{bandLabel(clamped)}</span>
      </div>
    </div>
  );
}
