import { Panel } from "@/shared/ui";
import type { PerformanceBucketVM } from "../types";
import { PerformanceBucketTable } from "./PerformanceBucketTable";

export interface PerformanceBySectorThemeProps {
  buckets: PerformanceBucketVM[];
}

export function PerformanceBySectorTheme({
  buckets,
}: PerformanceBySectorThemeProps) {
  return (
    <Panel
      title="Performance by Sector / Theme"
      badge={String(buckets.length)}
      badgeTone="info"
      testId="trade-performance-sector-theme"
    >
      <PerformanceBucketTable buckets={buckets} keyHeader="Sector / Theme" />
    </Panel>
  );
}
