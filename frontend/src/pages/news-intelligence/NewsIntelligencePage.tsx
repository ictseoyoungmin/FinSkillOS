import { useQuery } from "@tanstack/react-query";
import { fetchNewsIntelligence } from "@/features/news/api";
import { EventLinkedNewsPanel } from "@/features/news/components/EventLinkedNewsPanel";
import { HoldingsRelevantNews } from "@/features/news/components/HoldingsRelevantNews";
import { LatestNewsPanel } from "@/features/news/components/LatestNewsPanel";
import { NewsEvidenceDetails } from "@/features/news/components/NewsEvidenceDetails";
import { NewsImpactMap } from "@/features/news/components/NewsImpactMap";
import { NewsJudgmentHeader } from "@/features/news/components/NewsJudgmentHeader";
import { NewsSignalSummary } from "@/features/news/components/NewsSignalSummary";
import { NewsWatchpointsPanel } from "@/features/news/components/NewsWatchpointsPanel";
import { newsIntelligenceFixture } from "@/mocks/fixtures/newsIntelligence.fixture";
import {
  EmptyState,
  InterpretationPanel,
  SafetyCaption,
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
      <div className="fso-news-intel-row fso-news-intel-summary-row">
        <NewsJudgmentHeader judgment={payload.judgment} />
        <NewsSignalSummary
          judgment={payload.judgment}
          drivers={payload.drivers}
          conflicts={payload.conflicts}
        />
        <InterpretationPanel
          bullets={payload.integratedInterpretation}
          testId="news-interpretation-panel"
        />
      </div>
      <div className="fso-news-intel-row fso-news-intel-main-row">
        <LatestNewsPanel articles={payload.latestNews} />
        <NewsImpactMap entries={payload.impactMap} />
      </div>
      <NewsEvidenceDetails
        title="Secondary Evidence"
        badge={`${payload.watchpoints.length + payload.holdingsRelevant.length + payload.eventLinked.length} rows`}
      >
        <div className="fso-news-evidence-grid">
          <NewsWatchpointsPanel watchpoints={payload.watchpoints} />
          <HoldingsRelevantNews articles={payload.holdingsRelevant} />
          <EventLinkedNewsPanel articles={payload.eventLinked} />
        </div>
      </NewsEvidenceDetails>
      <div data-testid="news-intelligence-safety-caption">
        <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
      </div>
    </div>
  );
}
