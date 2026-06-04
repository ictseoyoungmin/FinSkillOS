import { useState } from "react";
import { Panel } from "@/shared/ui";
import "./review-prompts-panel.css";

export interface ReviewPromptsPanelProps {
  prompts: string[];
}

/**
 * Reflection prompts checklist (Slice 162). Descriptive guiding questions for
 * the weekly review; checked state is local (a working aid, not persisted).
 */
export function ReviewPromptsPanel({ prompts }: ReviewPromptsPanelProps) {
  const [checked, setChecked] = useState<Record<number, boolean>>({});
  if (prompts.length === 0) {
    return null;
  }
  const done = Object.values(checked).filter(Boolean).length;
  const toggle = (index: number) =>
    setChecked((prev) => ({ ...prev, [index]: !prev[index] }));

  return (
    <Panel
      title="Review Prompts"
      badge={`${done}/${prompts.length}`}
      badgeTone={done === prompts.length ? "success" : "info"}
      testId="review-prompts"
    >
      <p className="fso-review-prompts-note">
        Work through these while reviewing — a process aid, not stored data.
      </p>
      <ul className="fso-review-prompts-list">
        {prompts.map((prompt, index) => (
          <li key={prompt}>
            <label>
              <input
                type="checkbox"
                checked={Boolean(checked[index])}
                onChange={() => toggle(index)}
                data-testid={`review-prompt-${index}`}
              />
              <span data-checked={Boolean(checked[index])}>{prompt}</span>
            </label>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
