import { useQuery } from "@tanstack/react-query";
import { Panel } from "@/shared/ui";
import { fetchDataInvariants } from "../api";

/**
 * Stored-data invariant audit (Slice 153). Currently: every indicator snapshot
 * must have a backing market bar (the Slice-102 invariant) — orphan snapshots can
 * surface phantom indicator values.
 */
export function DataInvariantPanel(): JSX.Element {
  const { data, isError } = useQuery({
    queryKey: ["data-invariants"],
    queryFn: ({ signal }) => fetchDataInvariants(signal),
  });

  if (isError) {
    return (
      <Panel title="Data Invariants" badge="unavailable" badgeTone="warning">
        <p className="fso-provenance-detail">
          Invariants could not be checked against the database.
        </p>
      </Panel>
    );
  }

  const report = data;
  const tone =
    !report || report.status === "UNKNOWN"
      ? "neutral"
      : report.status === "OK"
        ? "success"
        : "danger";

  return (
    <Panel
      title="Data Invariants"
      badge={report ? report.status.toLowerCase() : "loading"}
      badgeTone={tone}
    >
      <p className="fso-provenance-detail" data-testid="data-invariants-detail">
        {report?.detail ?? "Checking stored-data invariants…"}
      </p>
      {report && report.orphanSnapshotCount > 0 ? (
        <div className="fso-invariant-samples" data-testid="data-invariants-samples">
          {report.orphanSamples.map((v) => (
            <span
              key={`${v.ticker}-${v.at}`}
              className="fso-provenance-ticker"
              title={`${v.timeframe} · ${v.at}`}
            >
              {v.ticker}
            </span>
          ))}
        </div>
      ) : null}
    </Panel>
  );
}
