import { Panel } from "@/shared/ui";
import { TickerSearch } from "@/features/market/components/TickerSearch";

export interface SymbolSearchPanelProps {
  currentTicker: string;
  onSelect: (ticker: string) => void;
}

export function SymbolSearchPanel({
  currentTicker,
  onSelect,
}: SymbolSearchPanelProps) {
  return (
    <Panel
      title="Symbol Search"
      badge="Ticker"
      badgeTone="info"
      testId="symbol-search-panel"
    >
      <TickerSearch initialValue={currentTicker} onSubmit={onSelect} />
    </Panel>
  );
}
