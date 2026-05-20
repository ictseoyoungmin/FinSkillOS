import "./section-header.css";

export interface SectionHeaderProps {
  eyebrow?: string;
  title: string;
}

export function SectionHeader({ eyebrow, title }: SectionHeaderProps) {
  return (
    <div className="fso-section-header">
      {eyebrow ? <div className="fso-section-eyebrow">{eyebrow}</div> : null}
      <h2 className="fso-section-title">{title}</h2>
    </div>
  );
}
