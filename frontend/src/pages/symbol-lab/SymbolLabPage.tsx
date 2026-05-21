import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchSymbolLab } from "@/features/symbol/api";
import { SymbolAlertsPanel } from "@/features/symbol/components/SymbolAlertsPanel";
import { SymbolNewsPanel } from "@/features/symbol/components/SymbolNewsPanel";
import { SymbolPositionContext } from "@/features/symbol/components/SymbolPositionContext";
import { SymbolRecentBarsTable } from "@/features/symbol/components/SymbolRecentBarsTable";
import { SymbolSearchPanel } from "@/features/symbol/components/SymbolSearchPanel";
import { SymbolTechnicalSnapshot } from "@/features/symbol/components/SymbolTechnicalSnapshot";
import { SymbolWatchpoints } from "@/features/symbol/components/SymbolWatchpoints";
import { RegimeContextPanel } from "@/features/analysis/components/RegimeContextPanel";
import { symbolLabFixture } from "@/mocks/fixtures/symbolLab.fixture";
import { EmptyState, SectionHeader } from "@/shared/ui";
import "@/pages/market-kernel/market-kernel.css";
import "./symbol-lab.css";

const DEFAULT_TICKER = "TSLA";

export function SymbolLabPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const ticker = (searchParams.get("ticker") ?? DEFAULT_TICKER).toUpperCase();

  const { data, error } = useQuery({
    queryKey: ["symbol-lab", ticker],
    queryFn: ({ signal }) => fetchSymbolLab(ticker, signal),
    placeholderData: symbolLabFixture(ticker),
  });

  const selectTicker = (next: string) => {
    const params = new URLSearchParams(searchParams);
    params.set("ticker", next);
    setSearchParams(params, { replace: false });
  };

  if (error && !data) {
    return (
      <EmptyState
        testId="symbol-lab-error"
        title="Symbol Lab is unavailable"
        message={
          "The API is unreachable and no fixture is cached. " +
          "Check the FastAPI container and reload."
        }
      />
    );
  }

  const payload = data ?? symbolLabFixture(ticker);

  return (
    <div className="fso-symbol-lab" data-testid="symbol-lab-page">
      <SectionHeader eyebrow="FinSkillOS · Module" title="Symbol Lab" />
      <SymbolSearchPanel
        currentTicker={payload.header.ticker}
        onSelect={selectTicker}
      />
      {payload.setupHint ? (
        <EmptyState
          testId="symbol-lab-setup-hint"
          title="Limited data available"
          message={payload.setupHint}
        />
      ) : null}
      <div className="fso-symbol-lab-grid">
        <div className="fso-symbol-lab-main">
          <SymbolTechnicalSnapshot
            header={payload.header}
            indicators={payload.technical}
          />
          <SymbolRecentBarsTable bars={payload.recentBars} />
          <SymbolWatchpoints
            watchpoints={payload.watchpoints}
            interpretation={payload.interpretation}
            safetyCaption={payload.safetyCaption}
          />
        </div>
        <aside className="fso-symbol-lab-side" aria-label="Position + Risk context">
          <SymbolPositionContext
            position={payload.position}
            ticker={payload.header.ticker}
          />
          <SymbolAlertsPanel alerts={payload.alerts} />
          <SymbolNewsPanel news={payload.news} />
          <RegimeContextPanel regime={payload.regime} />
        </aside>
      </div>
    </div>
  );
}
