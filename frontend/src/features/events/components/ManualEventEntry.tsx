import type { ChangeEvent, FormEvent } from "react";
import { useState } from "react";
import { Panel } from "@/shared/ui";
import {
  runEventSeedSampleEvents,
  submitManualEvent,
} from "../api";
import type {
  EventDateStatus,
  ManualEventInput,
  ManualEventResult,
  ManualEventRules,
  SeedEventsResult,
} from "../types";
import "./manual-event-entry.css";

const DATE_STATUSES: EventDateStatus[] = [
  "TENTATIVE",
  "WINDOW",
  "REPORTED",
  "SPECULATIVE",
  "CONFIRMED",
];

const EVENT_TYPES = [
  "EARNINGS",
  "CENTRAL_BANK",
  "INFLATION",
  "PRODUCT_EVENT",
  "LAUNCH_EVENT",
  "IPO_WINDOW",
  "REGULATORY",
] as const;

interface FormState {
  title: string;
  eventType: string;
  dateStatus: EventDateStatus;
  startDate: string;
  endDate: string;
  source: string;
  sourceUrl: string;
  description: string;
  importanceScore: string;
  ticker: string;
  sector: string;
  theme: string;
  eventKey: string;
}

const emptyState = (rules: ManualEventRules): FormState => ({
  title: "",
  eventType: "EARNINGS",
  dateStatus: rules.defaultDateStatus,
  startDate: "",
  endDate: "",
  source: "",
  sourceUrl: "",
  description: "",
  importanceScore: "1.0",
  ticker: "",
  sector: "",
  theme: "",
  eventKey: "",
});

export interface ManualEventEntryProps {
  rules: ManualEventRules;
}

/**
 * Manual event entry form. ``date_status`` defaults to TENTATIVE; the
 * Slice 11 EventService rejects CONFIRMED + manual_seed source. The
 * "Seed sample data" action stays idempotent via the existing
 * EventService.seed_sample_events helper.
 */
export function ManualEventEntry({ rules }: ManualEventEntryProps) {
  const [form, setForm] = useState<FormState>(() => emptyState(rules));
  const [result, setResult] = useState<ManualEventResult | null>(null);
  const [seedResult, setSeedResult] = useState<SeedEventsResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [seeding, setSeeding] = useState(false);

  const onChange =
    (key: keyof FormState) =>
    (
      event: ChangeEvent<
        HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
      >,
    ) => {
      setForm((prev) => ({ ...prev, [key]: event.target.value }));
    };

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setResult(null);
    const payload: ManualEventInput = {
      title: form.title.trim(),
      eventType: form.eventType,
      dateStatus: form.dateStatus,
      startDate: form.startDate.trim(),
      endDate: form.endDate.trim() || null,
      source: form.source.trim() || null,
      sourceUrl: form.sourceUrl.trim() || null,
      description: form.description.trim() || null,
      importanceScore: form.importanceScore.trim() || "1.0",
      ticker: form.ticker.trim().toUpperCase() || null,
      sector: form.sector.trim() || null,
      theme: form.theme.trim() || null,
      eventKey: form.eventKey.trim() || null,
    };
    try {
      const next = await submitManualEvent(payload);
      setResult(next);
      if (next.status === "OK") {
        setForm(emptyState(rules));
      }
    } catch (error) {
      setResult({
        status: "ERROR",
        message: "Submission failed at the network layer. No event was stored.",
        detail: error instanceof Error ? error.name : "network_error",
        eventId: null,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const onSeed = async () => {
    setSeeding(true);
    setSeedResult(null);
    try {
      const next = await runEventSeedSampleEvents();
      setSeedResult(next);
    } catch (error) {
      setSeedResult({
        status: "ERROR",
        message: "Sample event seed failed at the network layer.",
        detail: error instanceof Error ? error.name : "network_error",
        createdCount: 0,
        ranAt: new Date().toISOString(),
      });
    } finally {
      setSeeding(false);
    }
  };

  return (
    <Panel
      title="Manual Event Entry"
      badge="Tentative by default"
      badgeTone="warning"
      testId="event-manual-entry"
    >
      <p
        className="fso-manual-event-disclaimer"
        data-testid="event-manual-entry-disclaimer"
      >
        {rules.disclaimer}
      </p>
      <form className="fso-manual-event-form" onSubmit={onSubmit} noValidate>
        <label className="fso-manual-event-field">
          <span>Title</span>
          <input
            type="text"
            value={form.title}
            onChange={onChange("title")}
            required
          />
        </label>
        <div className="fso-manual-event-row">
          <label className="fso-manual-event-field">
            <span>Event type</span>
            <select value={form.eventType} onChange={onChange("eventType")}>
              {EVENT_TYPES.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label className="fso-manual-event-field">
            <span>Date status</span>
            <select value={form.dateStatus} onChange={onChange("dateStatus")}>
              {DATE_STATUSES.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="fso-manual-event-row">
          <label className="fso-manual-event-field">
            <span>Start date</span>
            <input
              type="date"
              value={form.startDate}
              onChange={onChange("startDate")}
              required
            />
          </label>
          <label className="fso-manual-event-field">
            <span>End date (optional)</span>
            <input
              type="date"
              value={form.endDate}
              onChange={onChange("endDate")}
            />
          </label>
        </div>
        <div className="fso-manual-event-row">
          <label className="fso-manual-event-field">
            <span>Source</span>
            <input
              type="text"
              value={form.source}
              onChange={onChange("source")}
              placeholder="Reuters / IR / …"
            />
          </label>
          <label className="fso-manual-event-field">
            <span>Source URL</span>
            <input
              type="text"
              value={form.sourceUrl}
              onChange={onChange("sourceUrl")}
            />
          </label>
        </div>
        <div className="fso-manual-event-row">
          <label className="fso-manual-event-field">
            <span>Ticker</span>
            <input
              type="text"
              value={form.ticker}
              onChange={onChange("ticker")}
              placeholder="TSLA"
            />
          </label>
          <label className="fso-manual-event-field">
            <span>Sector</span>
            <input
              type="text"
              value={form.sector}
              onChange={onChange("sector")}
            />
          </label>
          <label className="fso-manual-event-field">
            <span>Theme</span>
            <input
              type="text"
              value={form.theme}
              onChange={onChange("theme")}
            />
          </label>
          <label className="fso-manual-event-field">
            <span>Event key</span>
            <input
              type="text"
              value={form.eventKey}
              onChange={onChange("eventKey")}
            />
          </label>
        </div>
        <label className="fso-manual-event-field">
          <span>Description</span>
          <textarea
            value={form.description}
            onChange={onChange("description")}
            rows={3}
          />
        </label>
        <div className="fso-manual-event-row">
          <label className="fso-manual-event-field">
            <span>Importance score (0–5)</span>
            <input
              type="text"
              value={form.importanceScore}
              onChange={onChange("importanceScore")}
            />
          </label>
        </div>
        <div className="fso-manual-event-actions">
          <button
            type="button"
            className="fso-manual-event-btn fso-manual-event-btn--ghost"
            onClick={onSeed}
            disabled={seeding}
            data-testid="event-seed-sample-events-button"
          >
            {seeding ? "Seeding…" : "Seed sample data"}
          </button>
          <button
            type="submit"
            className="fso-manual-event-btn"
            disabled={submitting}
            data-testid="event-manual-entry-submit"
          >
            {submitting ? "Saving…" : "Save event"}
          </button>
        </div>
      </form>
      {result ? (
        <div
          className={`fso-manual-event-result fso-manual-event-result--${result.status.toLowerCase()}`}
          data-testid="event-manual-entry-result"
        >
          <strong>{result.status}</strong>
          <span>{result.message}</span>
        </div>
      ) : null}
      {seedResult ? (
        <div
          className={`fso-manual-event-result fso-manual-event-result--${seedResult.status.toLowerCase()}`}
          data-testid="event-seed-sample-events-result"
        >
          <strong>{seedResult.status}</strong>
          <span>{seedResult.message}</span>
        </div>
      ) : null}
    </Panel>
  );
}
