import "./empty-state.css";

export interface EmptyStateProps {
  title: string;
  message: string;
  testId?: string;
}

export function EmptyState({ title, message, testId }: EmptyStateProps) {
  return (
    <div className="fso-empty" data-testid={testId}>
      <div className="fso-empty-title">{title}</div>
      <p className="fso-empty-msg">{message}</p>
    </div>
  );
}
