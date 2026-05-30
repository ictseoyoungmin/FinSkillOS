import type { ProtocolDetailEvidence } from "./types";

/**
 * Parse a legacy comma-separated `key=value` protocol detail string into
 * structured evidence fragments. A bare token (no `=`) becomes a `detail`
 * row so audit strings without explicit keys still render.
 */
export function parseProtocolDetail(detail: string): ProtocolDetailEvidence[] {
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

/**
 * Resolve the evidence chips for a protocol run or result. Prefers the
 * structured API `detailEvidence` (Slice 76) and falls back to parsing the
 * legacy `detail` string so older audit rows still render chips.
 */
export function deriveProtocolEvidence(run: {
  detailEvidence?: ProtocolDetailEvidence[];
  detail?: string;
}): ProtocolDetailEvidence[] {
  if ((run.detailEvidence?.length ?? 0) > 0) {
    return run.detailEvidence as ProtocolDetailEvidence[];
  }
  return parseProtocolDetail(run.detail ?? "");
}
