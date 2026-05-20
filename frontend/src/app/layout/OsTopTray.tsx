import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { OS_NAV_ITEMS } from "./nav-config";
import { useTheme, type ThemeContextValue } from "@/shared/hooks/useTheme";
import { StatusPill } from "@/shared/ui";
import "./os-tray.css";

export interface OsTopTrayProps {
  guardCount: number;
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
      className="fso-tray-btn"
      onClick={cycleTheme}
      data-testid="theme-toggle"
      aria-label={`Switch theme (current: ${theme})`}
    >
      <span className="fso-tray-btn-glyph" aria-hidden>◐</span>
      <span className="fso-tray-btn-label">Theme · {theme}</span>
    </button>
  );
}

export function OsTopTray({ guardCount, onOpenPalette }: OsTopTrayProps) {
  const themeCtx = useTheme();
  const [clock, setClock] = useState(() => formatClock(new Date()));

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

      <nav className="fso-tray-nav" data-testid="os-nav" aria-label="Product modules">
        {OS_NAV_ITEMS.map((item) => (
          <NavLink
            key={item.key}
            to={item.path}
            end={item.path === "/"}
            data-page={item.key}
            data-testid={`os-nav-${item.key}`}
            className={({ isActive }) =>
              `fso-tray-nav-btn ${isActive ? "active" : ""}`.trim()
            }
            title={item.description}
          >
            <span className="fso-tray-nav-dot" aria-hidden />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="fso-tray-right" data-testid="os-status-pills">
        <StatusPill label="DB · Live" tone="success" testId="status-db" />
        <StatusPill label="Read Mode" tone="info" testId="status-read-mode" />
        <StatusPill
          label={`Guards · ${guardCount}`}
          tone={guardCount > 0 ? "warning" : "neutral"}
          testId="status-guards"
        />
        <button
          type="button"
          className="fso-tray-btn"
          onClick={onOpenPalette}
          data-testid="open-command-palette"
          aria-label="Open command palette (Ctrl + K)"
        >
          <span className="fso-tray-btn-glyph" aria-hidden>⌘</span>
          <span className="fso-tray-btn-label">Command · ⌘K</span>
        </button>
        <ThemeButton {...themeCtx} />
        <span className="fso-tray-clock" data-testid="clock">{clock}</span>
      </div>
    </header>
  );
}
