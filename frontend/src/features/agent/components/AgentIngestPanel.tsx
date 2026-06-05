import { useState } from "react";
import { Panel } from "@/shared/ui";
import {
  applyImportPositions,
  previewImportPositions,
} from "@/features/portfolio/api";
import type {
  MissionControlData,
  PortfolioImportResult,
} from "@/features/portfolio/types";
import { ingestPortfolioPaste } from "../api";
import type { IngestProposalResponse } from "../types";
import "./agent-ingest-panel.css";

export interface AgentIngestPanelProps {
  /** Writes are only offered when the DB is live (same gate as the editor). */
  editable: boolean;
  onApplied?: (snapshot: MissionControlData) => void;
}

const PLACEHOLDER = `Paste holdings — e.g.
NVDA 10 ₩25,000,000 Semiconductors AI
TSLA, 12, 12000000, Consumer, EV
ticker,quantity,market_value,sector
AAPL,5,1000000,Tech`;

/**
 * Agent ingestion (v3 Phase 11 / Slice 190). Paste free-form holdings → parse to
 * a reviewable proposal → preview the import (dry-run) → confirm. Every write
 * reuses the audited portfolio import; nothing is applied until the user confirms.
 */
export function AgentIngestPanel({ editable, onApplied }: AgentIngestPanelProps) {
  const [text, setText] = useState("");
  const [proposal, setProposal] = useState<IngestProposalResponse | null>(null);
  const [preview, setPreview] = useState<PortfolioImportResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [applied, setApplied] = useState<string | null>(null);

  const reset = () => {
    setProposal(null);
    setPreview(null);
    setError(null);
    setApplied(null);
  };

  const onParse = async () => {
    setBusy(true);
    reset();
    try {
      setProposal(await ingestPortfolioPaste(text));
    } catch {
      setError("Could not parse the pasted text.");
    } finally {
      setBusy(false);
    }
  };

  const onPreview = async () => {
    if (!proposal) return;
    setBusy(true);
    setError(null);
    try {
      setPreview(await previewImportPositions(proposal.normalizedCsv));
    } catch {
      setError("Import preview failed.");
    } finally {
      setBusy(false);
    }
  };

  const onConfirm = async () => {
    if (!proposal) return;
    setBusy(true);
    setError(null);
    try {
      const result = await applyImportPositions(proposal.normalizedCsv);
      setApplied(
        `Applied — ${result.adds} added, ${result.updates} updated.`,
      );
      setProposal(null);
      setPreview(null);
      setText("");
      if (result.snapshot) onApplied?.(result.snapshot);
    } catch {
      setError("Import apply failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Panel
      title="Agent Paste Import"
      badge="Preview → Confirm"
      badgeTone="info"
      testId="agent-ingest-panel"
    >
      <p className="fso-ingest-lead">
        Paste portfolio holdings; the agent collates them into a reviewable
        proposal. Nothing is written until you confirm.
      </p>
      <textarea
        className="fso-ingest-textarea"
        value={text}
        placeholder={PLACEHOLDER}
        onChange={(event) => setText(event.target.value)}
        rows={6}
        data-testid="agent-ingest-textarea"
      />
      <div className="fso-ingest-actions">
        <button
          type="button"
          onClick={onParse}
          disabled={busy || text.trim() === ""}
          data-testid="agent-ingest-parse"
        >
          Parse paste
        </button>
        {proposal ? (
          <button type="button" className="fso-ingest-ghost" onClick={reset}>
            Clear
          </button>
        ) : null}
      </div>

      {applied ? (
        <p className="fso-ingest-applied" data-testid="agent-ingest-applied">
          {applied}
        </p>
      ) : null}
      {error ? <p className="fso-ingest-error">{error}</p> : null}

      {proposal ? (
        <div className="fso-ingest-proposal" data-testid="agent-ingest-proposal">
          <div className="fso-ingest-proposal-head">
            <span>{proposal.rowCount} holdings parsed</span>
            {proposal.warnings.length > 0 ? (
              <span className="fso-ingest-warn-count">
                {proposal.warnings.length} warning
                {proposal.warnings.length > 1 ? "s" : ""}
              </span>
            ) : null}
          </div>
          {proposal.rows.length > 0 ? (
            <table className="fso-ingest-table">
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Qty</th>
                  <th>Value</th>
                  <th>Sector</th>
                  <th>Theme</th>
                </tr>
              </thead>
              <tbody>
                {proposal.rows.map((row) => (
                  <tr key={row.ticker}>
                    <td>{row.ticker}</td>
                    <td>{row.quantity}</td>
                    <td>{row.marketValue}</td>
                    <td>{row.sector ?? "—"}</td>
                    <td>{row.theme ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
          {proposal.warnings.length > 0 ? (
            <ul className="fso-ingest-warnings">
              {proposal.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          ) : null}

          {proposal.rowCount > 0 ? (
            <div className="fso-ingest-actions">
              <button
                type="button"
                onClick={onPreview}
                disabled={busy || !editable}
                data-testid="agent-ingest-preview"
              >
                Preview import
              </button>
              {preview ? (
                <button
                  type="button"
                  className="fso-ingest-confirm"
                  onClick={onConfirm}
                  disabled={busy || !editable}
                  data-testid="agent-ingest-confirm"
                >
                  Confirm — {preview.adds} add / {preview.updates} update
                </button>
              ) : null}
            </div>
          ) : null}
          {!editable ? (
            <p className="fso-ingest-note">
              Import is available only when the database is live.
            </p>
          ) : null}
        </div>
      ) : null}
    </Panel>
  );
}
