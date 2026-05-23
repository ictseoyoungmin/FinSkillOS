import { WatchpointsPanel } from "@/shared/ui";
import type { TradeWatchpoint } from "../types";

export interface TradeMemoryWatchpointsProps {
  watchpoints: TradeWatchpoint[];
}

/** Thin wrapper around the shared WatchpointsPanel — Trade Memory testId. */
export function TradeMemoryWatchpoints({
  watchpoints,
}: TradeMemoryWatchpointsProps) {
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
