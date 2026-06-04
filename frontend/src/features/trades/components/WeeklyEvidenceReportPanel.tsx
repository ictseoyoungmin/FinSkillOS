import { useState } from "react";
import { Panel } from "@/shared/ui";
import { fetchWeeklyEvidenceReport } from "../api";
import "./weekly-evidence-report-panel.css";

/**
 * Weekly Evidence Report (Slice 168). Loads a cross-tab markdown report
 * (regime + portfolio + catalysts + trade review) on demand and offers copy /
 * download. Descriptive process review only — no execution controls.
 */
export function WeeklyEvidenceReportPanel() {
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const onLoad = async () => {
    setBusy(true);
    setError(null);
    try {
      const report = await fetchWeeklyEvidenceReport();
      setMarkdown(report.markdown);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Report load failed.");
    } finally {
      setBusy(false);
    }
  };

  const onCopy = async () => {
    if (!markdown) return;
    try {
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };

  const onDownload = () => {
    if (!markdown) return;
    const blob = new Blob([markdown], { type: "text/markdown" });
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.download = "weekly-evidence-report.md";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(href);
  };

  return (
    <Panel
      title="Weekly Evidence Report"
      badge="Cross-tab"
      badgeTone="info"
      testId="weekly-evidence-report"
    >
      <p className="fso-weekly-evidence-note">
        One descriptive markdown report — regime, portfolio, catalysts, and the
        trade-process review for the week.
      </p>
      <div className="fso-weekly-evidence-actions">
        <button
          type="button"
          onClick={onLoad}
          disabled={busy}
          data-testid="weekly-evidence-load"
        >
          {busy ? "Assembling…" : markdown ? "Refresh report" : "Build report"}
        </button>
        {markdown ? (
          <>
            <button type="button" onClick={onCopy}>
              {copied ? "Copied!" : "Copy"}
            </button>
            <button type="button" onClick={onDownload}>
              Download .md
            </button>
          </>
        ) : null}
      </div>
      {markdown ? (
        <textarea
          className="fso-weekly-evidence-text"
          value={markdown}
          readOnly
          rows={Math.min(24, Math.max(8, markdown.split("\n").length + 1))}
          data-testid="weekly-evidence-textarea"
        />
      ) : null}
      {error ? (
        <p
          className="fso-weekly-evidence-error"
          data-testid="weekly-evidence-error"
        >
          {error}
        </p>
      ) : null}
    </Panel>
  );
}
