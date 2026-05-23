import { useQuery } from "@tanstack/react-query";
import { fetchTradeMemory } from "@/features/trades/api";
import { MistakeFrequencyPanel } from "@/features/trades/components/MistakeFrequencyPanel";
import { PerformanceByRegime } from "@/features/trades/components/PerformanceByRegime";
import { PerformanceBySectorTheme } from "@/features/trades/components/PerformanceBySectorTheme";
import { PerformanceByStrategy } from "@/features/trades/components/PerformanceByStrategy";
import { ProcessJudgmentHeader } from "@/features/trades/components/ProcessJudgmentHeader";
import { RecentEntriesTable } from "@/features/trades/components/RecentEntriesTable";
import { TradeEntryForm } from "@/features/trades/components/TradeEntryForm";
import { TradeMemoryWatchpoints } from "@/features/trades/components/TradeMemoryWatchpoints";
import { WeeklyMarkdownExport } from "@/features/trades/components/WeeklyMarkdownExport";
import { WeeklyReviewPanel } from "@/features/trades/components/WeeklyReviewPanel";
import { tradeMemoryFixture } from "@/mocks/fixtures/tradeMemory.fixture";
import {
  ConflictsPanel,
  DriversPanel,
  EmptyState,
  InterpretationPanel,
  SafetyCaption,
  SectionHeader,
} from "@/shared/ui";
import "./trade-memory.css";

export function TradeMemoryPage() {
  const { data, error } = useQuery({
    queryKey: ["trade-memory"],
    queryFn: ({ signal }) => fetchTradeMemory(signal),
    placeholderData: tradeMemoryFixture,
  });

  if (error && !data) {
    return (
      <EmptyState
        testId="trade-memory-error"
        title="Trade Memory is unavailable"
        message={
          "The API is unreachable and no fixture is cached. " +
          "Check the FastAPI container and reload."
        }
      />
    );
  }

  const payload = data ?? tradeMemoryFixture;

  return (
    <div className="fso-trade-memory" data-testid="trade-memory-page">
      <SectionHeader eyebrow="FinSkillOS · Module" title="Trade Memory" />
      <ProcessJudgmentHeader judgment={payload.judgment} />
      <div className="fso-trade-memory-grid">
        <div className="fso-trade-memory-col">
          <DriversPanel drivers={payload.drivers} />
          <RecentEntriesTable entries={payload.recentEntries} />
          <PerformanceByRegime buckets={payload.performanceByRegime} />
          <PerformanceBySectorTheme
            buckets={payload.performanceBySectorTheme}
          />
          <PerformanceByStrategy buckets={payload.performanceByStrategy} />
          <MistakeFrequencyPanel rows={payload.mistakeFrequency} />
        </div>
        <div className="fso-trade-memory-col">
          <ConflictsPanel conflicts={payload.conflicts} />
          <InterpretationPanel
            bullets={payload.integratedInterpretation}
          />
          <TradeMemoryWatchpoints watchpoints={payload.watchpoints} />
          <WeeklyReviewPanel review={payload.weeklyReview} />
          <WeeklyMarkdownExport markdown={payload.weeklyReview.markdown} />
          <TradeEntryForm rules={payload.formRules} />
        </div>
      </div>
      <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
    </div>
  );
}
