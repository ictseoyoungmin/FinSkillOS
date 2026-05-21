import { useQuery } from "@tanstack/react-query";
import { fetchNewsIntelligence } from "@/features/news/api";
import { EventLinkedNewsPanel } from "@/features/news/components/EventLinkedNewsPanel";
import { HoldingsRelevantNews } from "@/features/news/components/HoldingsRelevantNews";
import { ManualArticleEntry } from "@/features/news/components/ManualArticleEntry";
import { NewsImpactMap } from "@/features/news/components/NewsImpactMap";
import { NewsJudgmentHeader } from "@/features/news/components/NewsJudgmentHeader";
import { NewsWatchpointsPanel } from "@/features/news/components/NewsWatchpointsPanel";
import { newsIntelligenceFixture } from "@/mocks/fixtures/newsIntelligence.fixture";
import {
  ConflictsPanel,
  DriversPanel,
  EmptyState,
  InterpretationPanel,
  SectionHeader,
} from "@/shared/ui";
import "./news-intelligence.css";

export function NewsIntelligencePage() {
  const { data, error } = useQuery({
    queryKey: ["news-intelligence"],
    queryFn: ({ signal }) => fetchNewsIntelligence(signal),
    placeholderData: newsIntelligenceFixture,
  });

  if (error && !data) {
    return (
      <EmptyState
        testId="news-intelligence-error"
        title="News Intelligence is unavailable"
        message={
          "The API is unreachable and no fixture is cached. " +
          "Check the FastAPI container and reload."
        }
      />
    );
  }

  const payload = data ?? newsIntelligenceFixture;

  return (
    <div className="fso-news-intel" data-testid="news-intelligence-page">
      <SectionHeader eyebrow="FinSkillOS · Module" title="News Intelligence" />
      <NewsJudgmentHeader judgment={payload.judgment} />
      <div className="fso-news-intel-grid">
        <div className="fso-news-intel-col">
          <DriversPanel
            drivers={payload.drivers}
            testId="news-drivers"
          />
          <HoldingsRelevantNews articles={payload.holdingsRelevant} />
          <NewsImpactMap entries={payload.impactMap} />
          <EventLinkedNewsPanel articles={payload.eventLinked} />
        </div>
        <div className="fso-news-intel-col">
          <ConflictsPanel
            conflicts={payload.conflicts}
            testId="news-conflicts"
          />
          <InterpretationPanel
            bullets={payload.integratedInterpretation}
            testId="news-interpretation"
          />
          <NewsWatchpointsPanel watchpoints={payload.watchpoints} />
          <ManualArticleEntry rules={payload.manualEntryRules} />
        </div>
      </div>
      <p
        className="fso-news-intel-caption"
        data-testid="news-intelligence-safety-caption"
      >
        {payload.safetyCaption}
      </p>
    </div>
  );
}
