export interface JudgmentHeaderData {
  eyebrow: string;
  title: string;
  accent: string;
  summary: string;
  confidence: number;
}

export interface EvidenceDriverData {
  score: string;
  title: string;
  note: string;
}

export interface EvidenceConflictData {
  title: string;
  note: string;
}

export interface EvidenceWatchpointData {
  title: string;
  note: string;
}

export interface IntegratedInterpretationData {
  verdict: string;
  whyItMatters: string;
  whatRemainsUncertain: string;
}

