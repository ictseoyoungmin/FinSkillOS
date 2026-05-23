import { Panel } from "@/shared/ui";
import { toNumber } from "@/shared/lib/format";
import type { EventBadgeTone, EventRiskRow } from "../types";
import { EventStatusBadge } from "./EventStatusBadge";
import "./event-risk-table.css";

export interface EventRiskTableProps {
  title?: string;
  events: EventRiskRow[];
  toneMap?: Record<string, EventBadgeTone>;
  testId: string;
}

/**
 * Upcoming events table. Each row shows the date-status badge, date
 * window, importance, event_risk_score, risk label, portfolio
 * exposure %, and the affected ticker / theme tags.
 */
export function EventRiskTable({
  title = "Upcoming Events",
  events,
  toneMap,
  testId,
}: EventRiskTableProps) {
  if (events.length === 0) {
    return (
      <Panel title={title} badge="0" badgeTone="info" testId={testId}>
        <p className="fso-event-risk-empty">No stored events match this view.</p>
      </Panel>
    );
  }
  return (
    <Panel
      title={title}
      badge={String(events.length)}
      badgeTone="warning"
      testId={testId}
    >
      <table
        className="fso-event-risk-table"
        data-testid={`${testId}-table`}
      >
        <thead>
          <tr>
            <th scope="col">Event</th>
            <th scope="col">Date</th>
            <th scope="col">Status</th>
            <th scope="col">Score</th>
            <th scope="col">Risk</th>
            <th scope="col">Exposure</th>
            <th scope="col">Tags</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <tr key={event.eventId}>
              <td>
                <div className="fso-event-risk-title">{event.title}</div>
                <div className="fso-event-risk-meta">
                  {event.eventType}
                  {event.daysToEvent !== null
                    ? ` · in ${event.daysToEvent}d`
                    : ""}
                </div>
              </td>
              <td className="fso-event-risk-date">
                {event.startDate}
                {event.endDate ? ` → ${event.endDate}` : ""}
              </td>
              <td data-testid="date-status-badges">
                <EventStatusBadge status={event.dateStatus} toneMap={toneMap} />
              </td>
              <td className="fso-event-risk-score">
                {Number(event.eventRiskScore).toFixed(2)}
              </td>
              <td className="fso-event-risk-label">{event.riskLabel}</td>
              <td className="fso-event-risk-exposure">
                {(toNumber(event.portfolioExposure) * 100).toFixed(1)}%
              </td>
              <td>
                <ul className="fso-event-risk-tags">
                  {event.affectedTickers.map((ticker) => (
                    <li key={`t-${ticker}`}>{ticker}</li>
                  ))}
                  {event.affectedThemes.map((theme) => (
                    <li key={`th-${theme}`}>{theme}</li>
                  ))}
                </ul>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}
