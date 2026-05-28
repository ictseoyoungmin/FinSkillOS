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
import type { NewsSourceCoverage } from "@/features/news/types";
import { newsIntelligenceFixture } from "@/mocks/fixtures/newsIntelligence.fixture";
import {
  Badge,
  EmptyState,
  InterpretationPanel,
  SafetyCaption,
  SectionHeader,
} from "@/shared/ui";
import type { BadgeTone } from "@/shared/ui";
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
  const coverage = payload.sourceCoverage;

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
      <SourceCoverageBand coverage={coverage} source={payload.source} />
      <div className="fso-news-intel-row fso-news-intel-main-row">
        <LatestNewsPanel
          articles={payload.latestNews}
          tickerIdentities={payload.tickerIdentities}
        />
        <NewsImpactMap
          entries={payload.impactMap}
          tickerIdentities={payload.tickerIdentities}
        />
      </div>
      <NewsEvidenceDetails
        title="Secondary Evidence"
        badge={`${payload.watchpoints.length + payload.holdingsRelevant.length + payload.eventLinked.length} rows`}
      >
        <div className="fso-news-evidence-grid">
          <NewsWatchpointsPanel watchpoints={payload.watchpoints} />
          <HoldingsRelevantNews
            articles={payload.holdingsRelevant}
            tickerIdentities={payload.tickerIdentities}
          />
          <EventLinkedNewsPanel
            articles={payload.eventLinked}
            tickerIdentities={payload.tickerIdentities}
          />
        </div>
      </NewsEvidenceDetails>
      <div data-testid="news-intelligence-safety-caption">
        <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
      </div>
    </div>
  );
}

function SourceCoverageBand({
  coverage,
  source,
}: {
  coverage: NewsSourceCoverage;
  source: "fixture" | "live";
}) {
  const latest = coverage.latestPublishedAt
    ? coverage.latestPublishedAt.slice(0, 16).replace("T", " ")
    : "No timestamp";

  return (
    <div
      className="fso-news-source-band"
      data-source={source}
      data-testid="news-source-coverage"
    >
      <CoverageItem
        label="Source"
        value={source.toUpperCase()}
        detail={source === "live" ? "Stored DB metadata" : "Deterministic sample"}
        tone={source === "live" ? "success" : "warning"}
      />
      <CoverageItem
        label="Providers"
        value={String(coverage.sourceCount)}
        detail={coverage.providerMix}
        tone={coverage.sourceCount > 1 ? "info" : "neutral"}
      />
      <CoverageItem
        label="Articles"
        value={String(coverage.articleCount)}
        detail={latest}
        tone={coverage.articleCount > 0 ? "info" : "neutral"}
      />
      <CoverageItem
        label="Coverage"
        value={coverage.confidence}
        detail={coverage.coverageNote}
        tone={coverageTone(coverage.confidence)}
      />
    </div>
  );
}

function coverageTone(confidence: NewsSourceCoverage["confidence"]): BadgeTone {
  if (confidence === "HIGH") return "success";
  if (confidence === "MODERATE") return "warning";
  return "neutral";
}

function CoverageItem({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  tone: BadgeTone;
}) {
  return (
    <div className="fso-news-source-item">
      <span>{label}</span>
      <Badge tone={tone}>{value}</Badge>
      <small>{detail}</small>
    </div>
  );
}
