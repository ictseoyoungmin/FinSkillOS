import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";
import { Panel } from "@/shared/ui";
import { submitTradeEntry, updateTradeEntry } from "../api";
import type {
  EntryTemplate,
  TradeEntryInput,
  TradeEntryResult,
  TradeEntryVM,
  TradeFormRules,
  TradeSide,
} from "../types";
import "./trade-entry-form.css";

export interface TradeEntryFormProps {
  rules: TradeFormRules;
  onSaved?: (result: TradeEntryResult) => void | Promise<void>;
  /** When set, the form edits this entry (PUT) instead of appending (POST). */
  editEntry?: TradeEntryVM | null;
  onCancelEdit?: () => void;
  /** Quick-fill presets (Slice 162); omitted (fixture) hides the chip row. */
  templates?: EntryTemplate[];
}

interface FormState {
  tradeDate: string;
  ticker: string;
  side: TradeSide;
  strategyType: string;
  amount: string;
  marketRegime: string;
  emotionState: string;
  resultPnl: string;
  resultPnlPct: string;
  rMultiple: string;
  catalyst: string;
  thesis: string;
  reason: string;
  notes: string;
  sector: string;
  theme: string;
  eventKey: string;
  mistakeTags: string[];
}

const empty = (rules: TradeFormRules): FormState => ({
  tradeDate: todayIso(),
  ticker: "",
  side: rules.allowedSides[0] ?? "LONG",
  strategyType: "swing",
  amount: "",
  marketRegime: "",
  emotionState: "",
  resultPnl: "",
  resultPnlPct: "",
  rMultiple: "",
  catalyst: "",
  thesis: "",
  reason: "",
  notes: "",
  sector: "",
  theme: "",
  eventKey: "",
  mistakeTags: [],
});

const numericToString = (value: TradeEntryVM["amount"]): string =>
  value === null || value === undefined ? "" : String(value);

const fromEntry = (entry: TradeEntryVM, rules: TradeFormRules): FormState => ({
  tradeDate: entry.tradeDate,
  ticker: entry.ticker,
  side: (rules.allowedSides.includes(entry.side as TradeSide)
    ? (entry.side as TradeSide)
    : rules.allowedSides[0] ?? "LONG") as TradeSide,
  strategyType: entry.strategyType ?? "",
  amount: numericToString(entry.amount),
  marketRegime: entry.marketRegime ?? "",
  emotionState: entry.emotionState ?? "",
  resultPnl: numericToString(entry.resultPnl),
  resultPnlPct: numericToString(entry.resultPnlPct),
  rMultiple: numericToString(entry.rMultiple),
  catalyst: entry.catalyst ?? "",
  thesis: entry.thesis ?? "",
  reason: entry.reason ?? "",
  notes: entry.notes ?? "",
  sector: entry.sector ?? "",
  theme: entry.theme ?? "",
  eventKey: "",
  mistakeTags: [...entry.mistakeTags],
});

/**
 * Trade journal entry form. The side selector is restricted to the
 * Slice-12 reflection vocabulary; the disclaimer reinforces that this
 * is a process-review surface, not an execution control.
 */
export function TradeEntryForm({
  rules,
  onSaved,
  editEntry,
  onCancelEdit,
  templates,
}: TradeEntryFormProps) {
  const [form, setForm] = useState<FormState>(() => empty(rules));
  const [result, setResult] = useState<TradeEntryResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const isEditing = Boolean(editEntry);
  const requiredReady = form.tradeDate.trim() !== "" && form.ticker.trim() !== "";

  useEffect(() => {
    if (editEntry) {
      setForm(fromEntry(editEntry, rules));
      setResult(null);
    }
  }, [editEntry, rules]);

  const onChange =
    (key: keyof Omit<FormState, "mistakeTags">) =>
    (
      event: ChangeEvent<
        HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
      >,
    ) => {
      const value = event.target.value;
      setForm((prev) => ({ ...prev, [key]: value }));
    };

  const toggleTag = (tag: string) => {
    setForm((prev) => {
      if (prev.mistakeTags.includes(tag)) {
        return {
          ...prev,
          mistakeTags: prev.mistakeTags.filter((t) => t !== tag),
        };
      }
      return { ...prev, mistakeTags: [...prev.mistakeTags, tag] };
    });
  };

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!requiredReady) {
      setResult({
        status: "REJECTED",
        message: "Trade date and ticker are required for a journal entry.",
        detail: "missing_required_fields",
        entryId: null,
      });
      return;
    }
    setSubmitting(true);
    setResult(null);
    const payload: TradeEntryInput = {
      tradeDate: form.tradeDate,
      ticker: form.ticker.trim().toUpperCase(),
      side: form.side,
      strategyType: form.strategyType.trim() || null,
      amount: form.amount.trim() || null,
      marketRegime: form.marketRegime.trim() || null,
      emotionState: form.emotionState.trim() || null,
      resultPnl: form.resultPnl.trim() || null,
      resultPnlPct: form.resultPnlPct.trim() || null,
      rMultiple: form.rMultiple.trim() || null,
      catalyst: form.catalyst.trim() || null,
      thesis: form.thesis.trim() || null,
      reason: form.reason.trim() || null,
      notes: form.notes.trim() || null,
      sector: form.sector.trim() || null,
      theme: form.theme.trim() || null,
      eventKey: form.eventKey.trim() || null,
      mistakeTags: form.mistakeTags,
    };
    try {
      const next = editEntry
        ? await updateTradeEntry(editEntry.id, payload)
        : await submitTradeEntry(payload);
      setResult(next);
      if (next.status === "OK") {
        setForm(empty(rules));
        await onSaved?.(next);
        onCancelEdit?.();
      }
    } catch (error) {
      setResult({
        status: "ERROR",
        message: "Submission failed at the network layer. Entry was not stored.",
        detail: error instanceof Error ? error.name : "network_error",
        entryId: null,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setForm(empty(rules));
    setResult(null);
    onCancelEdit?.();
  };

  const applyTemplate = (template: EntryTemplate) => {
    setForm((prev) => ({
      ...prev,
      side: rules.allowedSides.includes(template.side)
        ? template.side
        : prev.side,
      strategyType: template.strategyType ?? prev.strategyType,
      reason: template.reason ?? prev.reason,
      thesis: template.thesis ?? prev.thesis,
      mistakeTags:
        template.mistakeTags.length > 0
          ? [...template.mistakeTags]
          : prev.mistakeTags,
    }));
    setResult(null);
  };

  return (
    <Panel
      title={isEditing ? "Edit Journal Entry" : "Add Journal Entry"}
      badge={isEditing ? "Editing" : "Reflection only"}
      badgeTone="info"
      testId="trade-entry-form"
    >
      <p
        className="fso-trade-entry-disclaimer"
        data-testid="trade-entry-form-disclaimer"
      >
        {rules.disclaimer}
      </p>
      {templates && templates.length > 0 ? (
        <div
          className="fso-trade-entry-templates"
          data-testid="trade-entry-templates"
        >
          <span>Templates</span>
          {templates.map((template) => (
            <button
              key={template.label}
              type="button"
              onClick={() => applyTemplate(template)}
              disabled={submitting}
              data-testid={`trade-entry-template-${template.label}`}
            >
              {template.label}
            </button>
          ))}
        </div>
      ) : null}
      <div className="fso-trade-entry-state" data-testid="trade-entry-form-state">
        <span data-ready={requiredReady}>Required {requiredReady ? "ready" : "missing"}</span>
        <span>{form.mistakeTags.length} tags</span>
        <span>{form.side}</span>
      </div>
      <form className="fso-trade-entry-form" onSubmit={onSubmit} noValidate>
        <fieldset className="fso-trade-entry-section">
          <legend>Entry context</legend>
          <div className="fso-trade-entry-row">
          <label className="fso-trade-entry-field">
            <span>Trade date</span>
            <input
              type="date"
              value={form.tradeDate}
              onChange={onChange("tradeDate")}
              required
            />
          </label>
          <label className="fso-trade-entry-field">
            <span>Ticker</span>
            <input
              type="text"
              value={form.ticker}
              onChange={onChange("ticker")}
              required
            />
          </label>
          <label className="fso-trade-entry-field">
            <span>Side</span>
            <select
              value={form.side}
              onChange={onChange("side")}
              data-testid="trade-entry-form-side"
            >
              {rules.allowedSides.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          </div>
        </fieldset>

        <fieldset className="fso-trade-entry-section">
          <legend>Setup tags</legend>
          <div className="fso-trade-entry-row">
          <label className="fso-trade-entry-field">
            <span>Strategy</span>
            <input
              type="text"
              value={form.strategyType}
              onChange={onChange("strategyType")}
            />
          </label>
          <label className="fso-trade-entry-field">
            <span>Amount</span>
            <input
              type="text"
              value={form.amount}
              onChange={onChange("amount")}
            />
          </label>
          <label className="fso-trade-entry-field">
            <span>Regime</span>
            <input
              type="text"
              value={form.marketRegime}
              onChange={onChange("marketRegime")}
              placeholder="HEALTHY_BULL"
            />
          </label>
          <label className="fso-trade-entry-field">
            <span>Emotion</span>
            <input
              type="text"
              value={form.emotionState}
              onChange={onChange("emotionState")}
            />
          </label>
          </div>
        </fieldset>

        <fieldset className="fso-trade-entry-section">
          <legend>Outcome</legend>
          <div className="fso-trade-entry-row">
          <label className="fso-trade-entry-field">
            <span>Result PnL</span>
            <input
              type="text"
              value={form.resultPnl}
              onChange={onChange("resultPnl")}
            />
          </label>
          <label className="fso-trade-entry-field">
            <span>Result PnL %</span>
            <input
              type="text"
              value={form.resultPnlPct}
              onChange={onChange("resultPnlPct")}
            />
          </label>
          <label className="fso-trade-entry-field">
            <span>R multiple</span>
            <input
              type="text"
              value={form.rMultiple}
              onChange={onChange("rMultiple")}
            />
          </label>
          </div>
        </fieldset>

        <fieldset className="fso-trade-entry-section">
          <legend>Reflection</legend>
          <label className="fso-trade-entry-field">
            <span>Catalyst</span>
            <input
              type="text"
              value={form.catalyst}
              onChange={onChange("catalyst")}
            />
          </label>
          <label className="fso-trade-entry-field">
            <span>Thesis</span>
            <textarea
              value={form.thesis}
              onChange={onChange("thesis")}
              rows={2}
            />
          </label>
          <label className="fso-trade-entry-field">
            <span>Reason</span>
            <textarea
              value={form.reason}
              onChange={onChange("reason")}
              rows={2}
            />
          </label>
          <label className="fso-trade-entry-field">
            <span>Notes</span>
            <textarea
              value={form.notes}
              onChange={onChange("notes")}
              rows={3}
            />
          </label>
          <div className="fso-trade-entry-row">
          <label className="fso-trade-entry-field">
            <span>Sector</span>
            <input
              type="text"
              value={form.sector}
              onChange={onChange("sector")}
            />
          </label>
          <label className="fso-trade-entry-field">
            <span>Theme</span>
            <input
              type="text"
              value={form.theme}
              onChange={onChange("theme")}
            />
          </label>
          <label className="fso-trade-entry-field">
            <span>Event key</span>
            <input
              type="text"
              value={form.eventKey}
              onChange={onChange("eventKey")}
            />
          </label>
          </div>
        </fieldset>
        <fieldset className="fso-trade-entry-tags">
          <legend>Mistake tags</legend>
          {rules.defaultMistakeTags.map((tag) => (
            <label key={tag}>
              <input
                type="checkbox"
                checked={form.mistakeTags.includes(tag)}
                onChange={() => toggleTag(tag)}
              />
              {tag}
            </label>
          ))}
        </fieldset>
        <div className="fso-trade-entry-actions">
          <button type="button" onClick={resetForm} disabled={submitting}>
            {isEditing ? "Cancel edit" : "Reset"}
          </button>
          <button
            type="submit"
            disabled={submitting || !requiredReady}
            data-testid="trade-entry-form-submit"
          >
            {submitting
              ? "Saving…"
              : isEditing
                ? "Update entry"
                : "Save entry"}
          </button>
        </div>
      </form>
      {result ? (
        <div
          className={`fso-trade-entry-result fso-trade-entry-result--${result.status.toLowerCase()}`}
          data-testid="trade-entry-form-result"
        >
          <strong>{result.status}</strong>
          <span>{result.message}</span>
        </div>
      ) : null}
    </Panel>
  );
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}
