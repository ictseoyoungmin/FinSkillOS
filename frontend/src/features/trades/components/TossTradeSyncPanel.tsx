import { useState } from "react";

import { syncTossTrades } from "@/features/agent/api";
import type { TradeSyncResponse } from "@/features/agent/types";

/**
 * Imports executed Toss orders into the trade journal (read-only on the broker;
 * no order placement). Replaces the manual entry form as the trade source.
 * Shows PENDING_TOSS while Toss has not yet enabled executed-order history.
 */
export function TossTradeSyncPanel({ onSynced }: { onSynced: () => void }) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<TradeSyncResponse | null>(null);
  const [failed, setFailed] = useState(false);

  const onSync = async () => {
    setBusy(true);
    setFailed(false);
    try {
      const res = await syncTossTrades();
      setResult(res);
      if (res.status === "APPLIED" && res.added > 0) onSynced();
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="fso-panel" data-testid="toss-trade-sync">
      <div className="fso-panel-head">
        <span className="fso-panel-title">Sync trades from Toss</span>
      </div>
      <div className="fso-panel-body">
        <p className="fso-trade-csv-note">
          Import your executed Toss orders into the journal. Read-only — no orders
          are placed. Past trades require Toss to enable executed-order history.
        </p>
        <div className="fso-trade-csv-actions">
          <button
            type="button"
            disabled={busy}
            onClick={() => void onSync()}
            data-testid="toss-trade-sync-button"
          >
            {busy ? "Syncing…" : "Sync trades"}
          </button>
        </div>
        {failed ? (
          <p
            className="fso-trade-csv-error"
            data-testid="toss-trade-sync-error"
          >
            Couldn't reach Toss to sync trades.
          </p>
        ) : null}
        {result ? (
          <p className="fso-trade-csv-note" data-testid="toss-trade-sync-result">
            {result.note}
          </p>
        ) : null}
      </div>
    </section>
  );
}
