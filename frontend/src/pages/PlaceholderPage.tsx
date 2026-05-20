import { EmptyState, SectionHeader } from "@/shared/ui";

export interface PlaceholderPageProps {
  eyebrow: string;
  title: string;
  message: string;
  testId?: string;
}

/**
 * Reusable "coming soon" page shell. Slice 13.6 ships these for every
 * route other than Control Room so navigation never lands on a 404
 * and the safety story stays intact (no execution controls anywhere).
 */
export function PlaceholderPage({
  eyebrow,
  title,
  message,
  testId,
}: PlaceholderPageProps) {
  return (
    <div data-testid={testId ?? "placeholder-page"}>
      <SectionHeader eyebrow={eyebrow} title={title} />
      <EmptyState
        title="Module shell ready · UI implementation deferred"
        message={message}
      />
    </div>
  );
}
