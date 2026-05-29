import { useState } from "react";
import { Card } from "@/shared/ui";
import type {
  ProtocolCard,
  ProtocolDetailEvidence,
  ProtocolRunResult,
  ProtocolTone,
} from "../types";
import "./protocol-card-item.css";

export interface ProtocolCardItemProps {
  protocol: ProtocolCard;
  onRun: () => Promise<ProtocolRunResult>;
}

type DialogPhase = "idle" | "confirm" | "running" | "done" | "error";

const TONE_COLOR: Record<ProtocolTone, string> = {
  info: "var(--fso-cyan)",
  warning: "var(--fso-amber)",
  neutral: "var(--fso-text-muted-2)",
  success: "var(--fso-green)",
};

/**
 * One System Ops protocol row. Surfaces a safe-wording button; the
 * confirm dialog (a stateful inline expansion, no portal) quotes the
 * idempotency note before allowing the request. Status / result are
 * rendered descriptively — no execution language ever appears.
 */
export function ProtocolCardItem({ protocol, onRun }: ProtocolCardItemProps) {
  const [phase, setPhase] = useState<DialogPhase>("idle");
  const [result, setResult] = useState<ProtocolRunResult | null>(null);
  const tone = TONE_COLOR[protocol.tone];
  const testId = `system-ops-protocol-${protocol.key.replace(/_/g, "-")}`;

  const reset = () => {
    setPhase("idle");
    setResult(null);
  };

  const handleConfirm = async () => {
    setPhase("running");
    try {
      const next = await onRun();
      setResult(next);
      setPhase("done");
    } catch (error) {
      setResult({
        protocol: protocol.key,
        status: "ERROR",
        message:
          "Protocol request failed at the network layer. Stored data was not modified.",
        detail: error instanceof Error ? error.name : "network_error",
        detailEvidence: [],
        ranAt: new Date().toISOString(),
      });
      setPhase("error");
    }
  };

  const evidence = result
    ? (result.detailEvidence?.length ?? 0) > 0
      ? result.detailEvidence
      : parseProtocolDetail(result.detail)
    : [];

  return (
    <Card testId={testId}>
      <div className="fso-protocol-card">
        <div className="fso-protocol-card-head">
          <span
            className="fso-protocol-card-dot"
            style={{ background: tone, borderColor: tone }}
            aria-hidden
          />
          <div className="fso-protocol-card-titles">
            <div className="fso-protocol-card-title">{protocol.title}</div>
            <p className="fso-protocol-card-desc">{protocol.description}</p>
          </div>
        </div>
        <p
          className="fso-protocol-card-idem"
          data-testid={`${testId}-idempotency`}
        >
          {protocol.idempotencyNote}
        </p>
        <div className="fso-protocol-card-actions">
          {protocol.lastRunAt ? (
            <span className="fso-protocol-card-last-run">
              Last run · {protocol.lastRunAt}
            </span>
          ) : (
            <span className="fso-protocol-card-last-run">
              Never run in this session.
            </span>
          )}
          <button
            type="button"
            className="fso-protocol-card-btn"
            data-testid={`${testId}-button`}
            onClick={() => setPhase("confirm")}
            disabled={phase === "running"}
          >
            {protocol.buttonLabel}
          </button>
        </div>

        {phase === "confirm" ? (
          <div
            className="fso-protocol-card-confirm"
            role="dialog"
            aria-labelledby={`${testId}-confirm-title`}
            data-testid={`${testId}-confirm`}
          >
            <p
              id={`${testId}-confirm-title`}
              className="fso-protocol-card-confirm-text"
            >
              Confirm protocol · {protocol.idempotencyNote}
            </p>
            <div className="fso-protocol-card-confirm-actions">
              <button
                type="button"
                className="fso-protocol-card-btn fso-protocol-card-btn--ghost"
                onClick={reset}
              >
                Cancel
              </button>
              <button
                type="button"
                className="fso-protocol-card-btn"
                data-testid={`${testId}-confirm-button`}
                onClick={handleConfirm}
              >
                {protocol.confirmLabel}
              </button>
            </div>
          </div>
        ) : null}

        {phase === "running" ? (
          <p className="fso-protocol-card-status">Protocol running…</p>
        ) : null}

        {result ? (
          <div
            className={`fso-protocol-card-result fso-protocol-card-result--${result.status.toLowerCase()}`}
            data-testid={`${testId}-result`}
          >
            <div className="fso-protocol-card-result-main">
              <strong>{result.status}</strong>
              <span>{result.message}</span>
            </div>
            <div
              className="fso-protocol-card-result-meta"
              data-testid={`${testId}-result-meta`}
            >
              <span>ran_at</span>
              <b>{result.ranAt}</b>
            </div>
            {evidence.length > 0 ? (
              <dl
                className="fso-protocol-card-result-evidence"
                data-testid={`${testId}-result-evidence`}
              >
                {evidence.map((item) => (
                  <div
                    className="fso-protocol-card-result-chip"
                    key={`${item.key}-${item.value}`}
                  >
                    <dt>{item.key}</dt>
                    <dd>{item.value}</dd>
                  </div>
                ))}
              </dl>
            ) : null}
          </div>
        ) : null}
      </div>
    </Card>
  );
}

function parseProtocolDetail(detail: string): ProtocolDetailEvidence[] {
  return detail
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => {
      const [key, ...valueParts] = item.split("=");
      const value = valueParts.join("=").trim();
      if (!value) {
        return { key: "detail", value: key.trim() };
      }
      return { key: key.trim(), value };
    });
}
