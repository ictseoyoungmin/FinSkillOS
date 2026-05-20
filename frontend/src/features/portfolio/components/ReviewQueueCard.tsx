import { Badge, Panel } from "@/shared/ui";
import type { BadgeTone } from "@/shared/ui";
import type { ReviewQueueItem } from "../types";
import "./review-queue-card.css";

const TONE_BY_TAG: Record<ReviewQueueItem["tag"], BadgeTone> = {
  weekly: "info",
  mistake: "warning",
  thesis: "purple",
  event: "danger",
};

export interface ReviewQueueCardProps {
  items: ReviewQueueItem[];
}

export function ReviewQueueCard({ items }: ReviewQueueCardProps) {
  return (
    <Panel
      title="Review Queue"
      badge="Weekly"
      badgeTone="info"
      testId="review-queue-card"
    >
      <ul className="fso-review-list">
        {items.map((item) => (
          <li className="fso-review-row" key={item.title}>
            <div className="fso-review-head">
              <span className="fso-review-title">{item.title}</span>
              <Badge tone={TONE_BY_TAG[item.tag]}>{item.tag}</Badge>
            </div>
            <p className="fso-review-note">{item.note}</p>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
