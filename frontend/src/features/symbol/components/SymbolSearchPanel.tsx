import { Panel } from "@/shared/ui";
import type { UniverseTicker } from "@/features/market/kernel-types";
import { TickerSearch } from "@/features/market/components/TickerSearch";

export interface SymbolSearchPanelProps {
  currentTicker: string;
  universe: UniverseTicker[];
  onSelect: (ticker: string) => void;
}

export function SymbolSearchPanel({
  currentTicker,
  universe,
  onSelect,
}: SymbolSearchPanelProps) {
  return (
    <Panel
      title="Symbol Search"
      badge="Ticker"
      badgeTone="info"
      testId="symbol-search"
    >
      <TickerSearch
        initialValue={currentTicker}
        placeholder="Search any ticker"
        suggestions={universe.map((item) => ({
          symbol: item.symbol,
          label: item.label,
        }))}
        onSubmit={onSelect}
      />
    </Panel>
  );
}
