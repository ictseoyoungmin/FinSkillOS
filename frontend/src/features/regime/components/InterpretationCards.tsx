import { Card, Panel } from "@/shared/ui";
import "./interpretation-cards.css";

export interface InterpretationCardsProps {
  cards: string[];
}

export function InterpretationCards({ cards }: InterpretationCardsProps) {
  return (
    <Panel
      title="Interpretation"
      badge="Descriptive"
      badgeTone="info"
      testId="interpretation-cards"
    >
      <div className="fso-interp-grid">
        {cards.map((line, idx) => (
          <Card key={idx}>
            <span className="fso-interp-eyebrow">Card {idx + 1}</span>
            <p className="fso-interp-text">{line}</p>
          </Card>
        ))}
      </div>
    </Panel>
  );
}
