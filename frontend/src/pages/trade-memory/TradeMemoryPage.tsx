import { useQuery, useQueryClient } from "@tanstack/react-query";
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
  const queryClient = useQueryClient();
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
  const sourceSummary = buildTradeMemorySourceSummary(payload);

  return (
    <div className="fso-trade-memory" data-testid="trade-memory-page">
      <SectionHeader eyebrow="FinSkillOS · Module" title="Trade Memory" />
      <div
        className="fso-trade-memory-state"
        data-source={payload.source}
        data-testid="trade-memory-source-state"
      >
        <div>
          <span>{sourceSummary.eyebrow}</span>
          <strong>{sourceSummary.title}</strong>
          <small>{sourceSummary.detail}</small>
        </div>
        <dl>
          <div>
            <dt>Entries</dt>
            <dd>{payload.recentEntries.length}</dd>
          </div>
          <div>
            <dt>Weekly</dt>
            <dd>{payload.weeklyReview.tradeCount}</dd>
          </div>
          <div>
            <dt>Source</dt>
            <dd>{payload.source.toUpperCase()}</dd>
          </div>
        </dl>
      </div>
      <div className="fso-v42-topline">
        <ProcessJudgmentHeader judgment={payload.judgment} />
        <DriversPanel drivers={payload.drivers} />
        <ConflictsPanel conflicts={payload.conflicts} />
      </div>
      <div className="fso-trade-memory-grid">
        <div className="fso-trade-memory-col">
          <RecentEntriesTable entries={payload.recentEntries} />
          <PerformanceByRegime buckets={payload.performanceByRegime} />
          <PerformanceBySectorTheme
            buckets={payload.performanceBySectorTheme}
          />
          <PerformanceByStrategy buckets={payload.performanceByStrategy} />
          <MistakeFrequencyPanel rows={payload.mistakeFrequency} />
        </div>
        <div className="fso-trade-memory-col">
          <InterpretationPanel
            bullets={payload.integratedInterpretation}
          />
          <TradeMemoryWatchpoints watchpoints={payload.watchpoints} />
          <WeeklyReviewPanel review={payload.weeklyReview} />
          <WeeklyMarkdownExport markdown={payload.weeklyReview.markdown} />
          <TradeEntryForm
            rules={payload.formRules}
            onSaved={async () => {
              await queryClient.invalidateQueries({
                queryKey: ["trade-memory"],
              });
            }}
          />
        </div>
      </div>
      <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
    </div>
  );
}

function buildTradeMemorySourceSummary(
  payload: typeof tradeMemoryFixture,
): {
  eyebrow: string;
  title: string;
  detail: string;
} {
  if (payload.source === "fixture") {
    return {
      eyebrow: "Deterministic fixture",
      title: "Sample reflection data",
      detail: "Use fixture mode for visual QA and repeatable contract checks.",
    };
  }
  if (payload.recentEntries.length === 0) {
    return {
      eyebrow: "Live DB",
      title: "Journal is ready, no stored entries yet",
      detail:
        "Add reflection entries to activate regime, strategy, and mistake-tag analytics.",
    };
  }
  return {
    eyebrow: "Live DB",
    title: "Stored journal read model",
    detail:
      "Trade Memory is reading reflection entries and weekly review metrics from the database.",
  };
}
