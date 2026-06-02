import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { OS_NAV_ITEMS } from "./nav-config";
import { useTheme, type ThemeContextValue } from "@/shared/hooks/useTheme";
import { StatusPill } from "@/shared/ui";
import "./os-tray.css";

export interface OsTopTrayProps {
  guardCount: number;
  dbStatus?: "LIVE" | "MISSING";
  onOpenPalette: () => void;
}

function formatClock(date: Date): string {
  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}

function ThemeButton({ theme, cycleTheme }: ThemeContextValue) {
  return (
    <button
      type="button"
      className="fso-tray-icon-btn"
      onClick={cycleTheme}
      data-testid="theme-toggle"
      aria-label={`Switch theme (current: ${theme})`}
      title={`Theme · ${theme}`}
    >
      <span aria-hidden>◐</span>
    </button>
  );
}

export function OsTopTray({
  guardCount,
  dbStatus = "MISSING",
  onOpenPalette,
}: OsTopTrayProps) {
  const themeCtx = useTheme();
  const [clock, setClock] = useState(() => formatClock(new Date()));
  const dbTone = dbStatus === "LIVE" ? "success" : "danger";

  useEffect(() => {
    const handle = window.setInterval(
      () => setClock(formatClock(new Date())),
      30_000,
    );
    return () => window.clearInterval(handle);
  }, []);

  return (
    <header className="fso-tray" data-testid="os-tray">
      <div className="fso-tray-brand">
        <span className="fso-tray-brand-mark" aria-hidden>◉</span>
        <span className="fso-tray-brand-name">FinSkillOS</span>
        <span className="fso-tray-brand-version">v4.1</span>
      </div>

      <div className="fso-tray-nav-cluster">
        <nav className="fso-tray-nav" data-testid="os-nav" aria-label="Product modules">
          {OS_NAV_ITEMS.map((item) => (
            <NavLink
              key={item.key}
              to={item.path}
              end={item.path === "/"}
              data-page={item.key}
              data-testid={`os-nav-${item.key}`}
              aria-label={item.label}
              className={({ isActive }) =>
                `fso-tray-nav-btn ${isActive ? "active" : ""}`.trim()
              }
              title={item.description}
            >
              <span
                className="fso-tray-nav-icon"
                data-testid={`os-nav-icon-${item.key}`}
                aria-hidden
              >
                {item.iconChar}
              </span>
              <span className="fso-tray-nav-label">{item.shortLabel}</span>
            </NavLink>
          ))}
        </nav>
        <div className="fso-tray-command-slot">
          <button
            type="button"
            className="fso-tray-icon-btn"
            onClick={onOpenPalette}
            data-testid="open-command-palette"
            aria-label="Open command drawer (Ctrl + K)"
            title="Command · Ctrl or Command K"
          >
            <span aria-hidden>⌘</span>
          </button>
          <span className="fso-tray-command-label" aria-hidden>
          </span>
        </div>
      </div>

      <div className="fso-tray-right" data-testid="os-status-pills">
        <StatusPill
          label={`DB · ${dbStatus}`}
          tone={dbTone}
          testId="status-db"
        />
        <StatusPill label="Read Mode" tone="info" testId="status-read-mode" />
        <StatusPill
          label={`Guards · ${guardCount}`}
          tone={guardCount > 0 ? "warning" : "neutral"}
          testId="status-guards"
        />
        <ThemeButton {...themeCtx} />
        <span className="fso-tray-clock" data-testid="clock">{clock}</span>
      </div>
    </header>
  );
}
