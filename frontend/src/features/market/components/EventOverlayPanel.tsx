import { Badge, EmptyState, Panel } from "@/shared/ui";
import type { EventOverlayItem } from "../kernel-types";

export interface EventOverlayPanelProps {
  events: EventOverlayItem[];
}

export function EventOverlayPanel({ events }: EventOverlayPanelProps) {
  return (
    <Panel
      title="Event Overlay"
      badge="7-30D"
      badgeTone="warning"
      testId="market-kernel-events"
    >
      {events.length === 0 ? (
        <EmptyState
          title="No tracked events"
          message="No upcoming catalysts are linked to this ticker in the stored data."
        />
      ) : (
        <ul className="fso-kernel-events">
          {events.map((event) => (
            <li key={event.title} className="fso-kernel-event">
              <span className="fso-kernel-event-day" aria-hidden>
                {event.daysToEvent === null ? "—" : `T-${event.daysToEvent}`}
              </span>
              <div className="fso-kernel-event-body">
                <span className="fso-kernel-event-title">{event.title}</span>
                <span className="fso-kernel-event-sub">{event.subtitle}</span>
              </div>
              <Badge tone={event.tone}>{event.tag}</Badge>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
