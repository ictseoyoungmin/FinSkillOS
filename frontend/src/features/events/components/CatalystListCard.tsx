import { Badge, Card, Panel } from "@/shared/ui";
import type { CatalystSummary } from "../types";
import "./catalyst-list-card.css";

export interface CatalystListCardProps {
  events: CatalystSummary[];
}

export function CatalystListCard({ events }: CatalystListCardProps) {
  return (
    <Panel
      title="Catalyst Watch"
      badge="7D"
      badgeTone="warning"
      testId="catalyst-watch-summary"
    >
      {events.map((event) => (
        <Card key={event.title}>
          <div className="fso-catalyst-row">
            <span className="fso-catalyst-day" aria-hidden>
              {event.daysToEvent === null ? "—" : event.daysToEvent}
            </span>
            <div className="fso-catalyst-meta">
              <span className="fso-catalyst-title">{event.title}</span>
              <span className="fso-catalyst-sub">{event.subtitle}</span>
            </div>
            <Badge tone={event.tone}>{event.tag}</Badge>
          </div>
        </Card>
      ))}
    </Panel>
  );
}
