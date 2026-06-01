export type StateVectorTone =
  | "info"
  | "warning"
  | "danger"
  | "neutral"
  | "success";

export interface StateVectorCell {
  label: string;
  value: string;
  tone: StateVectorTone;
}

export interface OperatingState {
  title: string;
  regime: string;
  decisionMode: string;
  preparationScore: number;
  tags: string[];
  summary: string;
  stateVector: StateVectorCell[];
}
