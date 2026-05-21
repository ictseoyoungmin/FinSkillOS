import type { UniverseTicker } from "../kernel-types";
import "./symbol-universe-rail.css";

export interface SymbolUniverseRailProps {
  universe: UniverseTicker[];
  activeSymbol: string;
  onSelect: (symbol: string) => void;
}

const KIND_LABEL: Record<UniverseTicker["kind"], string> = {
  FOCUS: "Focus",
  INDEX_ETF: "Index ETF",
  SECTOR_ETF: "Sector ETF",
  MACRO_PROXY: "Macro Proxy",
};

export function SymbolUniverseRail({
  universe,
  activeSymbol,
  onSelect,
}: SymbolUniverseRailProps) {
  const groups = new Map<UniverseTicker["kind"], UniverseTicker[]>();
  for (const ticker of universe) {
    const bucket = groups.get(ticker.kind) ?? [];
    bucket.push(ticker);
    groups.set(ticker.kind, bucket);
  }
  const orderedKinds: UniverseTicker["kind"][] = [
    "FOCUS",
    "INDEX_ETF",
    "SECTOR_ETF",
    "MACRO_PROXY",
  ];

  return (
    <aside
      className="fso-universe-rail"
      data-testid="symbol-universe-rail"
      aria-label="Symbol universe"
    >
      {orderedKinds.map((kind) => {
        const items = groups.get(kind);
        if (!items || items.length === 0) return null;
        return (
          <div key={kind} className="fso-universe-group">
            <div className="fso-universe-group-head">{KIND_LABEL[kind]}</div>
            <ul className="fso-universe-list">
              {items.map((item) => {
                const isActive = item.symbol === activeSymbol;
                return (
                  <li key={item.symbol}>
                    <button
                      type="button"
                      className={`fso-universe-item ${
                        isActive ? "fso-universe-item--active" : ""
                      }`.trim()}
                      data-active={isActive}
                      onClick={() => onSelect(item.symbol)}
                    >
                      <span className="fso-universe-symbol">{item.symbol}</span>
                      <span className="fso-universe-label">{item.label}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })}
    </aside>
  );
}
