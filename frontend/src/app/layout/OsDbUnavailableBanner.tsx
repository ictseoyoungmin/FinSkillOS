export interface OsDbUnavailableBannerProps {
  /** From `/api/system-status`. `undefined` while the query is still loading. */
  dbStatus: string | undefined;
}

/**
 * Global banner shown only when the database is unreachable
 * (`/api/system-status` -> `dbStatus = "MISSING"`). In that state every tab
 * falls back to deterministic fixture *shape*; this banner makes it explicit
 * that those numbers are sample shape, not live data, so a DB outage is never
 * read as real data. It is descriptive only — no execution wording.
 *
 * The explicit `X-FSO-Use-Fixture` demo override keeps `dbStatus = "LIVE"`, so
 * the banner does not appear during visual baselines or intentional demos.
 */
export function OsDbUnavailableBanner({ dbStatus }: OsDbUnavailableBannerProps) {
  if (dbStatus !== "MISSING") {
    return null;
  }

  return (
    <div
      className="fso-db-unavailable-banner"
      role="status"
      data-testid="db-unavailable-banner"
    >
      <strong>Database unavailable.</strong> Tabs are showing sample shape, not
      live data. Connect a database or run a System Ops protocol to populate
      real data.
    </div>
  );
}
