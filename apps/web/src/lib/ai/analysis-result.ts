export type AnalysisType =
  | 'domain_cashflow'
  | 'domain_marketing'
  | 'synthesis_risk'
  | 'executive_summary'
  | 'unknown';

export type AnalysisSection = Record<string, unknown>;

export type AnalysisResult = {
  type: 'analysis-result';
  company_id: string;
  company_name?: string | null;
  analysis_type: AnalysisType;
  selected_agents: string[];
  sections: Record<string, AnalysisSection>;
  agent_run_id?: string | null;
};

export function isAnalysisResult(value: unknown): value is AnalysisResult {
  if (!value || typeof value !== 'object') return false;

  const record = value as Partial<AnalysisResult>;

  return (
    record.type === 'analysis-result' &&
    typeof record.company_id === 'string' &&
    typeof record.analysis_type === 'string' &&
    Array.isArray(record.selected_agents) &&
    Boolean(record.sections) &&
    typeof record.sections === 'object'
  );
}
