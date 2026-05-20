import { useTheme } from "@/shared/hooks/useTheme";
import "./os-status-bar.css";

export interface OsStatusBarProps {
  source: "fixture" | "live";
  generatedAt: string;
}

export function OsStatusBar({ source, generatedAt }: OsStatusBarProps) {
  const { theme } = useTheme();
  return (
    <footer className="fso-status-bar" data-testid="os-status-bar">
      <span>
        <span className="fso-status-key">Data source</span>{" "}
        <span className="fso-status-value">{source.toUpperCase()}</span>
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
