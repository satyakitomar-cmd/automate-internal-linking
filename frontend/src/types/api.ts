export interface InsertionHint {
  paragraph_index: number;
  sentence_index: number;
  anchor_start: number;
  anchor_end: number;
  dom_path: string;
}

export interface ScoreBreakdown {
  lexical: number;
  semantic: number;
  context: number;
  quality: number;
}

export interface Suggestion {
  source_url: string;
  target_url: string;
  anchor_text: string;
  anchor_variants: string[];
  context_snippet: string;
  match_reason: string;
  confidence_score: number;
  risk_flags: string[];
  scores: ScoreBreakdown;
  insertion_hint?: InsertionHint;
}

export type JobStatus = "pending" | "running" | "completed" | "failed";

export interface JobStats {
  urls_submitted: number;
  urls_fetched: number;
  sources_with_suggestions: number;
  total_suggestions: number;
  elapsed_seconds: number;
}

export interface JobInfo {
  job_id: string;
  status: JobStatus;
  progress: string;
  stats: JobStats;
  errors: string[];
  results: Record<string, Suggestion[]> | null;
}

export interface SiteRules {
  domain?: string;
  max_links_per_source_page?: number;
  max_links_per_target_page?: number;
  anchor_length_min_words?: number;
  anchor_length_max_words?: number;
  avoid_sections?: string[];
  existing_link_policy?: "skip" | "allow_different_anchor";
}

export interface PipelineConfig {
  weight_lexical?: number;
  weight_semantic?: number;
  weight_context?: number;
  weight_quality?: number;
  score_threshold?: number;
  max_suggestions_per_source?: number;
  mmr_lambda?: number;
  site_rules?: SiteRules;
}

export interface AnalyzeRequest {
  urls: string[];
  config?: PipelineConfig;
  site_rules?: SiteRules;
}

export interface ParsedProgress {
  stage: string;
  percentage: number;
  detail: string;
}
