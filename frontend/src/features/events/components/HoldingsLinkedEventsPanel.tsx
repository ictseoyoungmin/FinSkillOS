import type { EventBadgeTone, EventRiskRow } from "../types";
import { EventRiskTable } from "./EventRiskTable";

export interface HoldingsLinkedEventsPanelProps {
  events: EventRiskRow[];
  toneMap?: Record<string, EventBadgeTone>;
}

/** Subset of upcoming events whose links overlap the user's holdings. */
export function HoldingsLinkedEventsPanel({
  events,
  toneMap,
}: HoldingsLinkedEventsPanelProps) {
  return (
    <EventRiskTable
      title="Holdings-Linked Events"
      events={events}
      toneMap={toneMap}
      testId="event-holdings-linked"
    />
  );
}
