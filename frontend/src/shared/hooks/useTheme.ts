import { useContext } from "react";
import { ThemeContext } from "@/app/providers/ThemeProvider";

// Re-export so consumers can import the hook + its types from a single
// module (`@/shared/hooks/useTheme`) — the build failed in 13.6
// scaffolding because `OsTopTray.tsx` expected `ThemeContextValue` here.
export type { ThemeContextValue, ThemeId } from "@/app/providers/ThemeProvider";

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used inside <ThemeProvider>");
  }
  return ctx;
}
