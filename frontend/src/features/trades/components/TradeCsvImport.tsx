import type { ChangeEvent } from "react";
import { useState } from "react";
import { Panel } from "@/shared/ui";
import { applyTradeImport, previewTradeImport } from "../api";
import type { TradeImportResult } from "../types";
import "./trade-csv-import.css";

export interface TradeCsvImportProps {
  /** Live DB session required to persist; fixture/offline disables controls. */
  editable: boolean;
  /** Called after a successful apply so the page can refetch. */
  onImported: () => void | Promise<void>;
}

/**
 * Append journal entries from CSV (Slice 160). Dry-run preview shows per-row
 * OK / INVALID; apply is append-only and atomic — the whole batch is rejected
 * if any row is invalid (descriptive-only wording included).
 */
export function TradeCsvImport({ editable, onImported }: TradeCsvImportProps) {
  const [csvText, setCsvText] = useState("");
  const [result, setResult] = useState<TradeImportResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setCsvText(await file.text());
    setResult(null);
    setError(null);
  };

  const onPreview = async () => {
    if (csvText.trim() === "") {
      setError("Paste or choose a CSV first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      setResult(await previewTradeImport(csvText));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Preview failed.");
    } finally {
      setBusy(false);
    }
  };

  const onApply = async () => {
    setBusy(true);
    setError(null);
    try {
      const applied = await applyTradeImport(csvText);
      setResult(applied);
      if (applied.status === "APPLIED") {
        setCsvText("");
        await onImported();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed.");
    } finally {
      setBusy(false);
    }
  };

  const canApply =
    result?.status === "PREVIEW" && result.totalRows > 0 && result.invalid === 0;

  return (
    <Panel
      title="Import Entries (CSV)"
      badge={editable ? "Append only" : "Read mode"}
      badgeTone={editable ? "info" : "neutral"}
      testId="trade-csv-import"
    >
      <p className="fso-trade-csv-note">
        Each row becomes a new descriptive journal entry. Import is atomic — if
        any row is invalid, nothing is written. Columns match the export.
      </p>
      {!editable ? (
        <p className="fso-trade-csv-disabled" data-testid="trade-csv-disabled">
          Live database session required to import entries.
        </p>
      ) : null}
      <label className="fso-trade-csv-file">
        <span>Choose CSV…</span>
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={onFile}
          disabled={!editable}
        />
      </label>
      <textarea
        className="fso-trade-csv-text"
        value={csvText}
        onChange={(e) => {
          setCsvText(e.target.value);
          setResult(null);
        }}
        placeholder="trade_date,ticker,side,amount,reason&#10;2026-05-01,NVDA,LONG,4200000,Aligned with checklist."
        rows={4}
        disabled={!editable}
        data-testid="trade-csv-textarea"
      />
      <div className="fso-trade-csv-actions">
        <button
          type="button"
          onClick={onPreview}
          disabled={!editable || busy || csvText.trim() === ""}
          data-testid="trade-csv-preview"
        >
          Preview import
        </button>
        {canApply ? (
          <button
            type="button"
            onClick={onApply}
            disabled={busy}
            data-testid="trade-csv-apply"
          >
            Append {result.valid} entr{result.valid === 1 ? "y" : "ies"}
          </button>
        ) : null}
      </div>
      {result ? (
        <div
          className={`fso-trade-csv-result fso-trade-csv-result--${result.status.toLowerCase()}`}
          data-testid="trade-csv-result"
        >
          <strong>{result.status}</strong>
          <span>{result.detail}</span>
        </div>
      ) : null}
      {result && result.invalid > 0 ? (
        <ul className="fso-trade-csv-errors" data-testid="trade-csv-errors">
          {result.errors.slice(0, 8).map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      ) : null}
      {error ? (
        <p className="fso-trade-csv-error" data-testid="trade-csv-network-error">
          {error}
        </p>
      ) : null}
    </Panel>
  );
}
