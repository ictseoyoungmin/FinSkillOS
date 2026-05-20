import { useCallback, useEffect, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchControlRoom } from "@/features/control-room/api";
import { controlRoomFixture } from "@/mocks/fixtures/controlRoom.fixture";
import { OsTopTray } from "./OsTopTray";
import { OsTickerStrip } from "./OsTickerStrip";
import { OsStatusBar } from "./OsStatusBar";
import { OsCommandPalette } from "./OsCommandPalette";
import { navItemForPath } from "./nav-config";
import "./os-shell.css";

export interface OsShellProps {
  children: ReactNode;
}

/**
 * Layout that wraps every routed page. Owns:
 *  - top tray (brand + nav + status pills + command + theme + clock)
 *  - ticker strip
 *  - status bar
 *  - the global command palette (Ctrl/Cmd+K)
 *
 * Ticker / status counts come from the Control Room snapshot — that
 * query runs once per session because React Query dedupes by key.
 */
export function OsShell({ children }: OsShellProps) {
  const { pathname } = useLocation();
  const [paletteOpen, setPaletteOpen] = useState(false);

  const { data } = useQuery({
    queryKey: ["control-room"],
    queryFn: ({ signal }) => fetchControlRoom(signal),
    placeholderData: controlRoomFixture,
  });

  const openPalette = useCallback(() => setPaletteOpen(true), []);
  const closePalette = useCallback(() => setPaletteOpen(false), []);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const isPaletteHotkey =
        (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k";
      if (isPaletteHotkey) {
        event.preventDefault();
        setPaletteOpen((open) => !open);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const activeNav = navItemForPath(pathname);

  return (
    <div
      className="fso-os-shell fso-os-scanlines"
      data-active-module={activeNav?.key ?? "control"}
    >
      <OsTopTray
        guardCount={data?.systemStatus.guardCount ?? 0}
        onOpenPalette={openPalette}
      />
      <OsTickerStrip items={data?.tickerStrip ?? []} />
      <main className="fso-os-workspace" data-testid="os-workspace">
        {children}
      </main>
      <OsStatusBar
        source={data?.source ?? "fixture"}
        generatedAt={data?.generatedAt ?? ""}
      />
      <OsCommandPalette open={paletteOpen} onClose={closePalette} />
    </div>
  );
}
