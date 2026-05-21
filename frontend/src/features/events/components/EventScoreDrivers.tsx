import { DriversPanel } from "@/shared/ui";
import type { EventDriver } from "../types";

export interface EventScoreDriversProps {
  drivers: EventDriver[];
}

/** Renders the Slice-13.9 "Primary Drivers" section for the event view. */
export function EventScoreDrivers({ drivers }: EventScoreDriversProps) {
  return (
    <DriversPanel
      title="Primary Drivers"
      drivers={drivers}
      testId="event-drivers"
    />
  );
}
