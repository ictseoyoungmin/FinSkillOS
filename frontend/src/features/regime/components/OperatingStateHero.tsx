import { Badge, Panel } from "@/shared/ui";
import { PreparationScoreDial } from "./PreparationScoreDial";
import type { OperatingState } from "../types";
import "./operating-state-hero.css";

export interface OperatingStateHeroProps {
  state: OperatingState;
}

export function OperatingStateHero({ state }: OperatingStateHeroProps) {
  return (
    <Panel
      title="Operating State"
      badge={state.regime}
      badgeTone="warning"
      testId="operating-state-hero"
    >
      <div className="fso-hero-grid">
        <div className="fso-hero-text">
          <h3 className="fso-hero-title">{state.title}</h3>
          <p className="fso-hero-summary">{state.summary}</p>
          <div className="fso-hero-tags">
            {state.tags.map((tag) => (
              <Badge key={tag} tone="info">
                {tag}
              </Badge>
            ))}
          </div>
          <small className="fso-hero-mode">
            Decision mode · {state.decisionMode}
          </small>
        </div>
        <PreparationScoreDial score={state.preparationScore} />
      </div>
    </Panel>
  );
}
