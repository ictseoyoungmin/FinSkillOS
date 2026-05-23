import { useQuery } from "@tanstack/react-query";
import { fetchAnalysisWorkspace } from "@/features/analysis/api";
import { IndexUniverseTable } from "@/features/analysis/components/IndexUniverseTable";
import { TapeStrengthCards } from "@/features/analysis/components/TapeStrengthCards";
import { RegimeContextPanel } from "@/features/analysis/components/RegimeContextPanel";
import { MissingDataPanel } from "@/features/analysis/components/MissingDataPanel";
import { analysisWorkspaceFixture } from "@/mocks/fixtures/analysisWorkspace.fixture";
import {
  ConflictsPanel,
  DriversPanel,
  EmptyState,
  InterpretationPanel,
  JudgmentHeader,
  SafetyCaption,
  SectionHeader,
  WatchpointsPanel,
} from "@/shared/ui";
import "./analysis-workspace.css";

export function AnalysisWorkspacePage() {
  const { data, error } = useQuery({
    queryKey: ["analysis-workspace"],
    queryFn: ({ signal }) => fetchAnalysisWorkspace(signal),
    placeholderData: analysisWorkspaceFixture,
  });

  if (error && !data) {
    return (
      <EmptyState
        testId="analysis-workspace-error"
        title="Analysis Workspace is unavailable"
        message={
          "The API is unreachable and no fixture is cached. " +
          "Check the FastAPI container and reload."
        }
      />
    );
  }

  const payload = data ?? analysisWorkspaceFixture;

  return (
    <div
      className="fso-analysis-workspace"
      data-testid="analysis-workspace-page"
    >
      <SectionHeader
        eyebrow="FinSkillOS · Module"
        title="Analysis Workspace"
      />
      <JudgmentHeader judgment={payload.judgment} />
      <div className="fso-analysis-evidence-row">
        <DriversPanel
          drivers={payload.drivers.map((driver) => ({
            label: driver.title,
            value: driver.score,
            detail: driver.note,
          }))}
        />
        <ConflictsPanel
          conflicts={payload.conflicts.map((conflict) => ({
            label: conflict.title,
            description: conflict.note,
          }))}
        />
      </div>
      <div className="fso-analysis-grid">
        <div className="fso-analysis-main">
          <IndexUniverseTable rows={payload.universe} />
          <TapeStrengthCards
            strongest={payload.strongest}
            weakest={payload.weakest}
          />
        </div>
        <aside className="fso-analysis-side" aria-label="Regime context">
          <RegimeContextPanel regime={payload.regime} />
          <MissingDataPanel
            tickers={payload.missingData}
            setupHint={payload.setupHint}
          />
        </aside>
      </div>
      <p
        className="fso-analysis-safety"
        data-testid="analysis-workspace-safety-caption"
      >
        {payload.safetyCaption}
      </p>
      <InterpretationPanel
        bullets={[
          payload.interpretation.verdict,
          payload.interpretation.whyItMatters,
          payload.interpretation.whatRemainsUncertain,
        ]}
      />
      <WatchpointsPanel
        watchpoints={payload.watchpoints.map((watchpoint) => ({
          label: watchpoint.title,
          description: watchpoint.note,
        }))}
      />
      <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
    </div>
  );
}
