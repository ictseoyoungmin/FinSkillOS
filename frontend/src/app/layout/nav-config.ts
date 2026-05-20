/**
 * Single source of truth for the OS top-tray navigation. The router,
 * command palette, and visual nav buttons all read this list so a
 * label is changed in exactly one place.
 *
 * `key` is reused as the React Router path segment without leading
 * slash. `iconChar` provides a lightweight glyph for the OS tray —
 * no icon library required.
 */

export interface OsNavItem {
  key: string;
  label: string;
  path: string;
  iconChar: string;
  description: string;
}

export const OS_NAV_ITEMS: readonly OsNavItem[] = [
  {
    key: "control",
    label: "Control Room",
    path: "/",
    iconChar: "◉",
    description: "Cockpit overview · mission · regime · alerts",
  },
  {
    key: "kernel",
    label: "Market Kernel",
    path: "/market-kernel",
    iconChar: "⌁",
    description: "Chart terminal · indicator context",
  },
  {
    key: "analysis",
    label: "Analysis Workspace",
    path: "/analysis-workspace",
    iconChar: "⌬",
    description: "Index Lab · ETF tape · relative strength",
  },
  {
    key: "symbol",
    label: "Symbol Lab",
    path: "/symbol-lab",
    iconChar: "⌕",
    description: "Ticker-specific state and position context",
  },
  {
    key: "firewall",
    label: "Risk Firewall",
    path: "/risk-firewall",
    iconChar: "▣",
    description: "Constraints · limits · active guards",
  },
  {
    key: "mission",
    label: "Mission Control",
    path: "/mission-control",
    iconChar: "★",
    description: "Goal tracker · milestones · early-stop state",
  },
  {
    key: "news",
    label: "News Intel",
    path: "/news-intel",
    iconChar: "✎",
    description: "Holdings-relevant news + sentiment overlay",
  },
  {
    key: "catalyst",
    label: "Catalyst Watch",
    path: "/catalyst-watch",
    iconChar: "⌖",
    description: "Upcoming events · risk score · linked news",
  },
  {
    key: "memory",
    label: "Trade Memory",
    path: "/trade-memory",
    iconChar: "◇",
    description: "Weekly review · mistake patterns",
  },
  {
    key: "ops",
    label: "System Ops",
    path: "/system-ops",
    iconChar: "⚙",
    description: "DB · seed · recompute protocol cards",
  },
] as const;

export function navItemForPath(pathname: string): OsNavItem | undefined {
  if (pathname === "/" || pathname === "") {
    return OS_NAV_ITEMS[0];
  }
  return OS_NAV_ITEMS.find((item) => item.path !== "/" && pathname.startsWith(item.path));
}
