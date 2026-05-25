import { useTheme } from "@/shared/hooks/useTheme";
import "./os-status-bar.css";

export interface OsStatusBarProps {
  source: "fixture" | "live";
  dbStatus?: "LIVE" | "MISSING";
  generatedAt: string;
  staleFlags?: string[];
}

export function OsStatusBar({
  source,
  dbStatus = "MISSING",
  generatedAt,
  staleFlags = [],
}: OsStatusBarProps) {
  const { theme } = useTheme();
  const freshnessLabel =
    staleFlags.length === 0 ? "OK" : `${staleFlags.length} stale`;

  return (
    <footer className="fso-status-bar" data-testid="os-status-bar">
      <span>
        <span className="fso-status-key">Data source</span>{" "}
        <span className="fso-status-value" data-testid="snapshot-source-status">
          {source.toUpperCase()}
        </span>
      </span>
      <span>
        <span className="fso-status-key">DB</span>{" "}
        <span className="fso-status-value" data-testid="db-status">
          {dbStatus}
        </span>
      </span>
      <span>
        <span className="fso-status-key">Freshness</span>{" "}
        <span className="fso-status-value" data-testid="freshness-status">
          {freshnessLabel}
        </span>
      </span>
      <span>
        <span className="fso-status-key">Theme</span>{" "}
        <span className="fso-status-value">{theme}</span>
      </span>
      <span>
        <span className="fso-status-key">Read mode</span>{" "}
        <span className="fso-status-value">No execution controls</span>
      </span>
      <span className="fso-status-when">
        snapshot · {generatedAt}
      </span>
    </footer>
  );
}
