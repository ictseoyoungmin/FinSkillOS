import { WatchpointsPanel } from "@/shared/ui";
import type { NewsWatchpoint } from "../types";

export interface NewsWatchpointsPanelProps {
  watchpoints: NewsWatchpoint[];
}

/** Thin wrapper over the shared WatchpointsPanel for News-specific testId. */
export function NewsWatchpointsPanel({
  watchpoints,
}: NewsWatchpointsPanelProps) {
  return (
    <WatchpointsPanel
      title="Watchpoints"
      watchpoints={watchpoints.map((entry) => ({
        label: entry.label,
        description: entry.description,
        tone: entry.tone,
      }))}
    />
  );
}
