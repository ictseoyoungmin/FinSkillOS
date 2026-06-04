import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";
import { Panel } from "@/shared/ui";
import { formatKrw } from "@/shared/lib/format";
import {
  clearPositions,
  createPosition,
  deletePosition,
  updatePosition,
  updateSnapshotBaseline,
} from "../api";
import type {
  MissionControlData,
  PortfolioReconciliation,
  PositionInput,
  PositionRow,
} from "../types";
import "./portfolio-editor-panel.css";

export interface PortfolioEditorPanelProps {
  positions: PositionRow[];
  reconciliation?: PortfolioReconciliation;
  totalValue: MissionControlData["portfolio"]["totalValue"];
  cashValue: MissionControlData["portfolio"]["cashValue"];
  /** Live editing requires a DB session; fixture/offline disables the controls. */
  editable: boolean;
  /** Called with the refreshed snapshot after each successful mutation. */
  onMutated: (next: MissionControlData) => void;
}

interface PositionFormState {
  ticker: string;
  quantity: string;
  marketValue: string;
  averageCost: string;
  sector: string;
  theme: string;
  strategyType: string;
  thesis: string;
}

const emptyForm = (): PositionFormState => ({
  ticker: "",
  quantity: "",
  marketValue: "",
  averageCost: "",
  sector: "",
  theme: "",
  strategyType: "swing",
  thesis: "",
});

const numericToString = (value: PositionRow["quantity"] | null): string =>
  value === null || value === undefined ? "" : String(value);

const fromRow = (row: PositionRow): PositionFormState => ({
  ticker: row.ticker,
  quantity: numericToString(row.quantity),
  marketValue: numericToString(row.marketValue),
  averageCost: numericToString(row.averageCost),
  sector: row.sector ?? "",
  theme: row.theme ?? "",
  strategyType: row.strategyType || "swing",
  thesis: row.thesis ?? "",
});

/**
 * Descriptive holdings editor (Slice 158). Add / edit / delete positions and
 * the stored snapshot baseline. This is portfolio bookkeeping, not execution —
 * there are no order or trade-direction controls.
 */
export function PortfolioEditorPanel({
  positions,
  reconciliation,
  totalValue,
  cashValue,
  editable,
  onMutated,
}: PortfolioEditorPanelProps) {
  const [form, setForm] = useState<PositionFormState>(() => emptyForm());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [baseline, setBaseline] = useState({ totalValue: "", cashValue: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isEditing = editingId !== null;

  useEffect(() => {
    setBaseline({
      totalValue: numericToString(totalValue),
      cashValue: numericToString(cashValue),
    });
  }, [totalValue, cashValue]);

  const onField =
    (key: keyof PositionFormState) =>
    (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      const value = event.target.value;
      setForm((prev) => ({ ...prev, [key]: value }));
    };

  const resetForm = () => {
    setForm(emptyForm());
    setEditingId(null);
    setError(null);
  };

  const startEdit = (row: PositionRow) => {
    setForm(fromRow(row));
    setEditingId(row.id);
    setError(null);
  };

  const requiredReady =
    form.ticker.trim() !== "" &&
    form.quantity.trim() !== "" &&
    form.marketValue.trim() !== "";

  const run = async (
    action: () => Promise<MissionControlData>,
    onDone?: () => void,
  ) => {
    setBusy(true);
    setError(null);
    try {
      const next = await action();
      onMutated(next);
      onDone?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setBusy(false);
    }
  };

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!requiredReady) {
      setError("Ticker, quantity, and market value are required.");
      return;
    }
    const payload: PositionInput = {
      ticker: form.ticker.trim().toUpperCase(),
      quantity: form.quantity.trim(),
      marketValue: form.marketValue.trim(),
      averageCost: form.averageCost.trim() || null,
      sector: form.sector.trim() || null,
      theme: form.theme.trim() || null,
      strategyType: form.strategyType.trim() || "swing",
      thesis: form.thesis.trim() || null,
    };
    await run(
      () =>
        editingId
          ? updatePosition(editingId, payload)
          : createPosition(payload),
      resetForm,
    );
  };

  const onDelete = async (row: PositionRow) => {
    await run(() => deletePosition(row.id), () => {
      if (editingId === row.id) resetForm();
    });
  };

  const onClear = async () => {
    await run(() => clearPositions(), resetForm);
  };

  const onSaveBaseline = async () => {
    await run(() =>
      updateSnapshotBaseline({
        totalValue: baseline.totalValue.trim() || null,
        cashValue: baseline.cashValue.trim() || null,
      }),
    );
  };

  return (
    <Panel
      title="Portfolio Editor"
      badge={editable ? "Manual entry" : "Read mode"}
      badgeTone={editable ? "info" : "neutral"}
      testId="portfolio-editor"
    >
      <p className="fso-portfolio-editor-note">
        Descriptive holdings bookkeeping — enter the positions you hold and the
        stored snapshot baseline. No order or execution controls.
      </p>
      {!editable ? (
        <p
          className="fso-portfolio-editor-disabled"
          data-testid="portfolio-editor-disabled"
        >
          Live database session required to edit holdings. Showing the current
          read-only snapshot.
        </p>
      ) : null}

      <div className="fso-portfolio-editor-table-wrap">
        <table
          className="fso-portfolio-editor-table"
          data-testid="portfolio-editor-table"
        >
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Qty</th>
              <th>Market value</th>
              <th>Sector</th>
              <th>Theme</th>
              <th aria-label="actions" />
            </tr>
          </thead>
          <tbody>
            {positions.length === 0 ? (
              <tr>
                <td colSpan={6} className="fso-portfolio-editor-empty">
                  No holdings recorded yet.
                </td>
              </tr>
            ) : (
              positions.map((row) => (
                <tr
                  key={row.id}
                  data-editing={row.id === editingId}
                  data-testid={`portfolio-editor-row-${row.ticker}`}
                >
                  <td>{row.ticker}</td>
                  <td>{numericToString(row.quantity)}</td>
                  <td>{formatKrw(row.marketValue)}</td>
                  <td>{row.sector ?? "—"}</td>
                  <td>{row.theme ?? "—"}</td>
                  <td className="fso-portfolio-editor-row-actions">
                    <button
                      type="button"
                      onClick={() => startEdit(row)}
                      disabled={!editable || busy}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="fso-portfolio-editor-danger"
                      onClick={() => onDelete(row)}
                      disabled={!editable || busy}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <form
        className="fso-portfolio-editor-form"
        onSubmit={onSubmit}
        noValidate
        data-testid="portfolio-editor-form"
      >
        <div className="fso-portfolio-editor-form-grid">
          <label>
            <span>Ticker</span>
            <input
              type="text"
              value={form.ticker}
              onChange={onField("ticker")}
              disabled={!editable}
              required
            />
          </label>
          <label>
            <span>Quantity</span>
            <input
              type="text"
              inputMode="decimal"
              value={form.quantity}
              onChange={onField("quantity")}
              disabled={!editable}
              required
            />
          </label>
          <label>
            <span>Market value</span>
            <input
              type="text"
              inputMode="decimal"
              value={form.marketValue}
              onChange={onField("marketValue")}
              disabled={!editable}
              required
            />
          </label>
          <label>
            <span>Average cost</span>
            <input
              type="text"
              inputMode="decimal"
              value={form.averageCost}
              onChange={onField("averageCost")}
              disabled={!editable}
            />
          </label>
          <label>
            <span>Sector</span>
            <input
              type="text"
              value={form.sector}
              onChange={onField("sector")}
              disabled={!editable}
            />
          </label>
          <label>
            <span>Theme</span>
            <input
              type="text"
              value={form.theme}
              onChange={onField("theme")}
              disabled={!editable}
            />
          </label>
          <label>
            <span>Strategy</span>
            <input
              type="text"
              value={form.strategyType}
              onChange={onField("strategyType")}
              disabled={!editable}
            />
          </label>
          <label className="fso-portfolio-editor-wide">
            <span>Thesis</span>
            <input
              type="text"
              value={form.thesis}
              onChange={onField("thesis")}
              disabled={!editable}
            />
          </label>
        </div>
        <div className="fso-portfolio-editor-actions">
          <button
            type="button"
            onClick={resetForm}
            disabled={!editable || busy}
          >
            {isEditing ? "Cancel edit" : "Reset"}
          </button>
          <button
            type="submit"
            disabled={!editable || busy || !requiredReady}
            data-testid="portfolio-editor-submit"
          >
            {busy
              ? "Saving…"
              : isEditing
                ? "Update position"
                : "Add position"}
          </button>
        </div>
      </form>

      <div className="fso-portfolio-editor-baseline">
        <h4>Snapshot baseline</h4>
        <p>
          The stored account value used by the reconciliation check
          {reconciliation ? ` (currently ${reconciliation.status}).` : "."}
        </p>
        <div className="fso-portfolio-editor-baseline-grid">
          <label>
            <span>Total value</span>
            <input
              type="text"
              inputMode="decimal"
              value={baseline.totalValue}
              onChange={(e) =>
                setBaseline((prev) => ({ ...prev, totalValue: e.target.value }))
              }
              disabled={!editable}
            />
          </label>
          <label>
            <span>Cash value</span>
            <input
              type="text"
              inputMode="decimal"
              value={baseline.cashValue}
              onChange={(e) =>
                setBaseline((prev) => ({ ...prev, cashValue: e.target.value }))
              }
              disabled={!editable}
            />
          </label>
          <button
            type="button"
            onClick={onSaveBaseline}
            disabled={!editable || busy}
            data-testid="portfolio-editor-baseline-save"
          >
            Save baseline
          </button>
        </div>
      </div>

      <div className="fso-portfolio-editor-footer">
        <button
          type="button"
          className="fso-portfolio-editor-danger"
          onClick={onClear}
          disabled={!editable || busy || positions.length === 0}
          data-testid="portfolio-editor-clear"
        >
          Clear sample
        </button>
        <small>Removes every recorded holding for the account.</small>
      </div>

      {error ? (
        <p
          className="fso-portfolio-editor-error"
          data-testid="portfolio-editor-error"
        >
          {error}
        </p>
      ) : null}
    </Panel>
  );
}
