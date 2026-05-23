import type { ChangeEvent, FormEvent } from "react";
import { useState } from "react";
import { Panel } from "@/shared/ui";
import { submitManualArticle } from "../api";
import type {
  ManualArticleInput,
  ManualArticleResult,
  NewsManualEntryRules,
  RiskLevel,
  SentimentLabel,
} from "../types";
import "./manual-article-entry.css";

export interface ManualArticleEntryProps {
  rules: NewsManualEntryRules;
}

const SENTIMENTS: SentimentLabel[] = [
  "UNKNOWN",
  "POSITIVE",
  "NEUTRAL",
  "MIXED",
  "NEGATIVE",
];
const RISK_LEVELS: RiskLevel[] = ["UNKNOWN", "GREEN", "YELLOW", "ORANGE", "RED"];

interface FormState {
  title: string;
  source: string;
  url: string;
  publishedAt: string;
  summary: string;
  affectedTickers: string;
  theme: string;
  eventKey: string;
  sentiment: SentimentLabel;
  riskLevel: RiskLevel;
}

const EMPTY: FormState = {
  title: "",
  source: "",
  url: "",
  publishedAt: "",
  summary: "",
  affectedTickers: "",
  theme: "",
  eventKey: "",
  sentiment: "UNKNOWN",
  riskLevel: "UNKNOWN",
};

/**
 * Manual article entry form. The summary input is hard-capped at the
 * server-side ``MAX_SUMMARY_CHARS`` so the user cannot paste a full
 * copyrighted body. The disclaimer reinforces the descriptive-only
 * contract.
 */
export function ManualArticleEntry({ rules }: ManualArticleEntryProps) {
  const [form, setForm] = useState<FormState>(EMPTY);
  const [result, setResult] = useState<ManualArticleResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const charsRemaining = rules.maxSummaryChars - form.summary.length;

  const onChange =
    (key: keyof FormState) =>
    (
      event: ChangeEvent<
        HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
      >,
    ) => {
      const value = event.target.value;
      setForm((prev) => ({ ...prev, [key]: value }));
    };

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setResult(null);
    const payload: ManualArticleInput = {
      title: form.title.trim(),
      source: form.source.trim(),
      url: form.url.trim(),
      publishedAt: form.publishedAt.trim() || new Date().toISOString(),
      summary: form.summary.trim(),
      affectedTickers: form.affectedTickers
        .split(",")
        .map((ticker) => ticker.trim().toUpperCase())
        .filter(Boolean),
      theme: form.theme.trim() || null,
      eventKey: form.eventKey.trim() || null,
      sentiment: form.sentiment,
      riskLevel: form.riskLevel,
    };
    try {
      const next = await submitManualArticle(payload);
      setResult(next);
      if (next.status === "OK") {
        setForm(EMPTY);
      }
    } catch (error) {
      setResult({
        status: "ERROR",
        message:
          "Submission failed at the network layer. No article was stored.",
        detail: error instanceof Error ? error.name : "network_error",
        articleId: null,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Panel
      title="Manual Article Entry"
      badge="Short summary only"
      badgeTone="info"
      testId="manual-article-entry"
    >
      <p
        className="fso-manual-article-disclaimer"
        data-testid="news-manual-article-disclaimer"
      >
        {rules.disclaimer}
      </p>
      <form className="fso-manual-article-form" onSubmit={onSubmit} noValidate>
        <label className="fso-manual-article-field">
          <span>Title</span>
          <input
            type="text"
            value={form.title}
            onChange={onChange("title")}
            required
            maxLength={300}
          />
        </label>
        <div className="fso-manual-article-row">
          <label className="fso-manual-article-field">
            <span>Source</span>
            <input
              type="text"
              value={form.source}
              onChange={onChange("source")}
              required
              maxLength={120}
            />
          </label>
          <label className="fso-manual-article-field">
            <span>Published at (ISO)</span>
            <input
              type="text"
              placeholder="2026-05-20T12:00:00+00:00"
              value={form.publishedAt}
              onChange={onChange("publishedAt")}
            />
          </label>
        </div>
        <label className="fso-manual-article-field">
          <span>URL</span>
          <input
            type="text"
            value={form.url}
            onChange={onChange("url")}
            required
            maxLength={1024}
          />
        </label>
        <label className="fso-manual-article-field">
          <span>
            Short summary{" "}
            <em
              className="fso-manual-article-counter"
              data-testid="news-manual-article-counter"
            >
              ({charsRemaining} chars left)
            </em>
          </span>
          <textarea
            value={form.summary}
            onChange={onChange("summary")}
            maxLength={rules.maxSummaryChars}
            rows={4}
            required
            data-testid="news-manual-article-summary"
          />
        </label>
        <div className="fso-manual-article-row">
          <label className="fso-manual-article-field">
            <span>Affected tickers (comma)</span>
            <input
              type="text"
              value={form.affectedTickers}
              onChange={onChange("affectedTickers")}
              placeholder="NVDA, TSLA"
            />
          </label>
          <label className="fso-manual-article-field">
            <span>Theme</span>
            <input
              type="text"
              value={form.theme}
              onChange={onChange("theme")}
              placeholder="AI"
            />
          </label>
          <label className="fso-manual-article-field">
            <span>Event key</span>
            <input
              type="text"
              value={form.eventKey}
              onChange={onChange("eventKey")}
              placeholder="FED_DECISION"
            />
          </label>
        </div>
        <div className="fso-manual-article-row">
          <label className="fso-manual-article-field">
            <span>Sentiment</span>
            <select value={form.sentiment} onChange={onChange("sentiment")}>
              {SENTIMENTS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label className="fso-manual-article-field">
            <span>Risk level</span>
            <select value={form.riskLevel} onChange={onChange("riskLevel")}>
              {RISK_LEVELS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="fso-manual-article-actions">
          <button
            type="submit"
            disabled={submitting}
            data-testid="news-manual-article-submit"
          >
            {submitting ? "Saving…" : "Save article"}
          </button>
        </div>
      </form>
      {result ? (
        <div
          className={`fso-manual-article-result fso-manual-article-result--${result.status.toLowerCase()}`}
          data-testid="news-manual-article-result"
        >
          <strong>{result.status}</strong>
          <span>{result.message}</span>
        </div>
      ) : null}
    </Panel>
  );
}
