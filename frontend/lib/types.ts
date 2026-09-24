export interface EvidenceItem {
  id: string;
  source: string;
  line: number;
  quote: string;
  timestamp: string;
  type: 'Log' | 'Document' | 'Telemetry';
  relevance: number;
}

export interface TimelineEvent {
  time: string;
  title: string;
  severity: 'info' | 'warning' | 'critical';
  detail: string;
}

export interface Hypothesis {
  id: string;
  title: string;
  status: 'VERIFIED' | 'DISPROVED' | 'INVESTIGATING';
  confidence: number;
  evidence_ids: string[];
  rationale: string;
}

export interface Contradiction {
  claim: string;
  counter_evidence: string;
  severity: string;
  resolution: string;
}

export interface ReflectionStep {
  step: string;
  detail: string;
}

export interface InvestigationResult {
  query: string;
  response: string;
  route: string;
  evidence_chain: EvidenceItem[];
  timeline: TimelineEvent[];
  hypotheses: Hypothesis[];
  contradictions: Contradiction[];
  reflection_trace: ReflectionStep[];
  confidence: number;
  status: string;
}

export interface IncidentRecord {
  id: string;
  filename: string;
  title: string;
  severity: 'P1' | 'P2' | 'P3';
  component: string;
  status: string;
  date: string;
  preview: string;
  full_content: string;
}

export interface SystemHealth {
  status: string;
  groq_model: string;
  langsmith_active: boolean;
  langsmith_project: string;
  rag_documents_indexed: number;
  vector_dim: number;
  version: string;
}
