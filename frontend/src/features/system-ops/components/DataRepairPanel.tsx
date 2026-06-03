import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Panel } from "@/shared/ui";
import { runDataRepair } from "../api";
import type { DataRepairResult } from "../types";

/**
 * Data repair (Slice 155). Removes synthetic (mock/test) bars + orphan indicator
 * snapshots — exactly what the Provenance (152) and Invariant (153) panels flag.
 * **Dry-run first, then an explicit confirm** before anything is deleted; real
 * (yfinance/csv) bars are never touched.
 */
export function DataRepairPanel(): JSX.Element {
  const queryClient = useQueryClient();
  const [preview, setPreview] = useState<DataRepairResult | null>(null);
  const [applied, setApplied] = useState<DataRepairResult | null>(null);

  const dryRun = useMutation({
    mutationFn: () => runDataRepair(false),
    onSuccess: (result) => {
      setPreview(result);
      setApplied(null);
    },
  });
  const confirmRun = useMutation({
    mutationFn: () => runDataRepair(true),
    onSuccess: (result) => {
      setApplied(result);
      setPreview(null);
      // Refresh the audits that this just changed.
      queryClient.invalidateQueries({ queryKey: ["data-provenance"] });
      queryClient.invalidateQueries({ queryKey: ["data-invariants"] });
      queryClient.invalidateQueries({ queryKey: ["system-ops"] });
    },
  });

  const nothingToRemove =
    preview !== null &&
    preview.syntheticBarCount === 0 &&
    preview.orphanSnapshotCount === 0;
  const busy = dryRun.isPending || confirmRun.isPending;

  return (
    <Panel title="Data Repair" badge="dry-run first" badgeTone="neutral">
      <p className="fso-provenance-detail">
        Removes synthetic (mock/test) bars and orphan indicator snapshots. Preview
        first; nothing is deleted until you confirm. Back up the DB before applying.
      </p>

      <div className="fso-repair-actions">
        <button
          type="button"
          className="fso-repair-preview"
          disabled={busy}
          data-testid="data-repair-preview"
          onClick={() => dryRun.mutate()}
        >
          {dryRun.isPending ? "Previewing…" : "Preview cleanup (dry-run)"}
        </button>
        {preview && !nothingToRemove ? (
          <button
            type="button"
            className="fso-repair-confirm"
            disabled={busy}
            data-testid="data-repair-confirm"
            onClick={() => confirmRun.mutate()}
          >
            {confirmRun.isPending
              ? "Deleting…"
              : `Delete ${preview.syntheticBarCount} bars + ${preview.orphanSnapshotCount} snapshots`}
          </button>
        ) : null}
      </div>

      {preview ? (
        <p
          className="fso-provenance-detail"
          data-tone={nothingToRemove ? "success" : "warning"}
          data-testid="data-repair-preview-detail"
        >
          {preview.detail}
          {preview.syntheticTickers.length > 0
            ? ` Tickers: ${preview.syntheticTickers.join(", ")}.`
            : ""}
        </p>
      ) : null}
      {applied ? (
        <p
          className="fso-provenance-detail"
          data-tone="success"
          data-testid="data-repair-applied-detail"
        >
          {applied.detail}
        </p>
      ) : null}
      {dryRun.isError || confirmRun.isError ? (
        <p className="fso-provenance-detail" data-tone="error" role="status">
          Data repair request failed.
        </p>
      ) : null}
    </Panel>
  );
}
