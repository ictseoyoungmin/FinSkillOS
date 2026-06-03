import { useQuery } from "@tanstack/react-query";
import { Panel } from "@/shared/ui";
import { fetchDataProvenance } from "../api";

/**
 * Where the stored market bars came from (Slice 152). Source distribution +
 * the tickers whose newest bar is synthetic (mock/test) — the actionable signal
 * that some rows are not real market data.
 */
export function DataProvenancePanel(): JSX.Element {
  const { data, isError } = useQuery({
    queryKey: ["data-provenance"],
    queryFn: ({ signal }) => fetchDataProvenance(signal),
  });

  if (isError) {
    return (
      <Panel title="Data Provenance" badge="unavailable" badgeTone="warning">
        <p className="fso-provenance-detail">
          Provenance could not be read from the database.
        </p>
      </Panel>
    );
  }

  const report = data;
  const ratio = report?.realRatioPercent ?? 0;
  const tone =
    !report || report.totalBars === 0
      ? "neutral"
      : report.syntheticTickers.length > 0
        ? "warning"
        : "success";

  return (
    <Panel
      title="Data Provenance"
      badge={report ? `${ratio}% real` : "loading"}
      badgeTone={tone}
    >
      <p className="fso-provenance-detail" data-testid="data-provenance-detail">
        {report?.detail ?? "Reading market-bar provenance…"}
      </p>

      {report && report.sources.length > 0 ? (
        <div className="fso-provenance-sources" data-testid="data-provenance-sources">
          {report.sources.map((src) => (
            <div
              key={src.source}
              className="fso-provenance-source"
              data-synthetic={src.synthetic ? "true" : "false"}
            >
              <span className="fso-provenance-source-name">{src.source}</span>
              <span className="fso-provenance-source-count">
                {src.barCount.toLocaleString()} bars
              </span>
            </div>
          ))}
        </div>
      ) : null}

      {report && report.syntheticTickers.length > 0 ? (
        <div className="fso-provenance-synthetic" data-testid="data-provenance-synthetic">
          <span className="fso-provenance-synthetic-label">
            Synthetic latest bar:
          </span>
          {report.syntheticTickers.map((t) => (
            <span
              key={t.ticker}
              className="fso-provenance-ticker"
              title={`${t.source} · ${t.latestAt ?? ""}`}
            >
              {t.ticker}
            </span>
          ))}
        </div>
      ) : null}
    </Panel>
  );
}
