import type { EventBadgeTone, EventRiskRow } from "../types";
import { EventRiskTable } from "./EventRiskTable";

export interface HighRiskEventsPanelProps {
  events: EventRiskRow[];
  toneMap?: Record<string, EventBadgeTone>;
}

/**
 * Re-uses EventRiskTable but pre-filters to HIGH / CRITICAL risk
 * rows so the page can render a focused "what deserves attention now"
 * section alongside the full upcoming-events table.
 */
export function HighRiskEventsPanel({ events, toneMap }: HighRiskEventsPanelProps) {
  return (
    <EventRiskTable
      title="High-Risk Events"
      events={events}
      toneMap={toneMap}
      testId="event-high-risk"
    />
  );
}
