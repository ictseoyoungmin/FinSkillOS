import { useState } from "react";
import { Panel } from "@/shared/ui";
import "./weekly-markdown-export.css";

export interface WeeklyMarkdownExportProps {
  markdown: string;
}

/**
 * Copyable markdown block — same shape that
 * ``TradeMemoryViewModel.weekly_review_markdown`` produces. The textarea
 * is read-only and a single "Copy" button writes the block to the
 * clipboard. No execution semantics, just process review.
 */
export function WeeklyMarkdownExport({ markdown }: WeeklyMarkdownExportProps) {
  const [copied, setCopied] = useState(false);
  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };
  return (
    <Panel
      title="Weekly Review Markdown"
      badge="Copyable"
      badgeTone="info"
      testId="trade-weekly-markdown"
    >
      <textarea
        className="fso-weekly-markdown"
        value={markdown}
        readOnly
        rows={Math.min(18, Math.max(6, markdown.split("\n").length + 1))}
        data-testid="trade-weekly-markdown-textarea"
      />
      <div className="fso-weekly-markdown-actions">
        <button
          type="button"
          className="fso-weekly-markdown-btn"
          onClick={onCopy}
          data-testid="trade-weekly-markdown-copy"
        >
          {copied ? "Copied!" : "Copy to clipboard"}
        </button>
      </div>
    </Panel>
  );
}
