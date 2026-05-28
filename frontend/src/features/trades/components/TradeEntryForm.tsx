import type { ChangeEvent, FormEvent } from "react";
import { useState } from "react";
import { Panel } from "@/shared/ui";
import { submitTradeEntry } from "../api";
import type {
  TradeEntryInput,
  TradeEntryResult,
  TradeFormRules,
  TradeSide,
} from "../types";
import "./trade-entry-form.css";

export interface TradeEntryFormProps {
  rules: TradeFormRules;
  onSaved?: (result: TradeEntryResult) => void | Promise<void>;
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
  tradeDate: "",
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

/**
 * Trade journal entry form. The side selector is restricted to the
 * Slice-12 reflection vocabulary; the disclaimer reinforces that this
 * is a process-review surface, not an execution control.
 */
export function TradeEntryForm({ rules, onSaved }: TradeEntryFormProps) {
  const [form, setForm] = useState<FormState>(() => empty(rules));
  const [result, setResult] = useState<TradeEntryResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

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
      const next = await submitTradeEntry(payload);
      setResult(next);
      if (next.status === "OK") {
        setForm(empty(rules));
        await onSaved?.(next);
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

  return (
    <Panel
      title="Add Journal Entry"
      badge="Reflection only"
      badgeTone="info"
      testId="trade-entry-form"
    >
      <p
        className="fso-trade-entry-disclaimer"
        data-testid="trade-entry-form-disclaimer"
      >
        {rules.disclaimer}
      </p>
      <form className="fso-trade-entry-form" onSubmit={onSubmit} noValidate>
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
          <button
            type="submit"
            disabled={submitting}
            data-testid="trade-entry-form-submit"
          >
            {submitting ? "Saving…" : "Save entry"}
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
