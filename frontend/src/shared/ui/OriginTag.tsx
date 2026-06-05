import "./origin-tag.css";

/**
 * Data-origin marker (v3 Phase 7 / Slice 180). Makes a value's provenance
 * explicit where it could be mistaken for a stored fact:
 *
 * - `live`    — a stored DB fact
 * - `derived` — computed from live facts (e.g. a weight % or a reconciliation)
 * - `sample`  — seeded / fixture sample (must only appear in fixture mode)
 * - `empty`   — no data yet (an explicit empty marker, never a fabricated 0)
 *
 * Tiny by design; complements the existing source/state chips rather than
 * replacing them.
 */
export type DataOrigin = "live" | "derived" | "sample" | "empty";

const LABEL: Record<DataOrigin, string> = {
  live: "Live",
  derived: "Derived",
  sample: "Sample",
  empty: "No data",
};

export interface OriginTagProps {
  origin: DataOrigin;
  /** Optional override label (defaults to the origin's word). */
  label?: string;
  testId?: string;
}

export function OriginTag({ origin, label, testId }: OriginTagProps) {
  return (
    <span
      className={`fso-origin-tag fso-origin-${origin}`}
      data-origin={origin}
      data-testid={testId}
      title={`Data origin: ${LABEL[origin]}`}
    >
      {label ?? LABEL[origin]}
    </span>
  );
}
