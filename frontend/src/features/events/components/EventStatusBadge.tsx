import type { EventBadgeTone, EventDateStatus } from "../types";
import "./event-status-badge.css";

const TONE_COLOR: Record<EventBadgeTone, string> = {
  success: "var(--fso-green)",
  info: "var(--fso-cyan)",
  warning: "var(--fso-amber)",
  purple: "var(--fso-purple, #b475f7)",
  danger: "var(--fso-red)",
};

const DEFAULT_TONE: Record<EventDateStatus, EventBadgeTone> = {
  CONFIRMED: "success",
  WINDOW: "info",
  TENTATIVE: "warning",
  REPORTED: "warning",
  SPECULATIVE: "purple",
};

export interface EventStatusBadgeProps {
  status: EventDateStatus;
  toneMap?: Record<string, EventBadgeTone>;
}

/**
 * One date-status badge. Colour mapping follows the Slice 11 contract:
 * CONFIRMED green, WINDOW cyan, TENTATIVE/REPORTED amber, SPECULATIVE
 * purple. A caller-supplied ``toneMap`` overrides the defaults.
 */
export function EventStatusBadge({ status, toneMap }: EventStatusBadgeProps) {
  const tone = (toneMap?.[status] ?? DEFAULT_TONE[status]) as EventBadgeTone;
  const color = TONE_COLOR[tone];
  return (
    <span
      className="fso-event-status-badge"
      style={{ color, borderColor: color }}
      data-status={status}
      data-tone={tone}
    >
      {status}
    </span>
  );
}
