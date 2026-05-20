export type CatalystTone = "info" | "warning" | "danger" | "neutral" | "purple";

export interface CatalystSummary {
  daysToEvent: number | null;
  title: string;
  subtitle: string;
  tag: string;
  tone: CatalystTone;
}
