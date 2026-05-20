import { BrowserRouter } from "react-router-dom";
import { QueryProvider } from "./app/providers/QueryProvider";
import { ThemeProvider } from "./app/providers/ThemeProvider";
import { OsShell } from "./app/layout/OsShell";
import { AppRoutes } from "./app/router/routes";

/**
 * The App is intentionally tiny — providers + router only. All
 * cockpit / layout / page composition lives inside `OsShell` and the
 * route table. Slice 13.6 rule: do NOT push business logic into App.
 */
export default function App() {
  return (
    <ThemeProvider>
      <QueryProvider>
        <BrowserRouter>
          <OsShell>
            <AppRoutes />
          </OsShell>
        </BrowserRouter>
      </QueryProvider>
    </ThemeProvider>
  );
}
