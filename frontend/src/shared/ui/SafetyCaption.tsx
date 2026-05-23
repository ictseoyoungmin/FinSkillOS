import "./safety-caption.css";

export function SafetyCaption({ children }: { children: string }) {
  return (
    <p className="fso-safety-caption" data-testid="safety-caption">
      {children}
    </p>
  );
}

