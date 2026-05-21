import { Panel } from "@/shared/ui";
import type { PerformanceBucketVM } from "../types";
import { PerformanceBucketTable } from "./PerformanceBucketTable";

export interface PerformanceByStrategyProps {
  buckets: PerformanceBucketVM[];
}

export function PerformanceByStrategy({ buckets }: PerformanceByStrategyProps) {
  return (
    <Panel
      title="Performance by Strategy"
      badge={String(buckets.length)}
      badgeTone="info"
      testId="trade-performance-strategy"
    >
      <PerformanceBucketTable buckets={buckets} keyHeader="Strategy" />
    </Panel>
  );
}
