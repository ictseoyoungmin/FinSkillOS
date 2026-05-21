import { Panel } from "@/shared/ui";
import type { PerformanceBucketVM } from "../types";
import { PerformanceBucketTable } from "./PerformanceBucketTable";

export interface PerformanceByRegimeProps {
  buckets: PerformanceBucketVM[];
}

export function PerformanceByRegime({ buckets }: PerformanceByRegimeProps) {
  return (
    <Panel
      title="Performance by Regime"
      badge={String(buckets.length)}
      badgeTone="info"
      testId="trade-performance-regime"
    >
      <PerformanceBucketTable buckets={buckets} keyHeader="Regime" />
    </Panel>
  );
}
