/** TypeScript types mirroring the Python data models. */

export interface InsertionHint {
  paragraph_index: number;
  sentence_index: number;
  anchor_start: number;
  anchor_end: number;
  dom_path: string;
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
  scores: {
    lexical: number;
    semantic: number;
    context: number;
    quality: number;
  };
  insertion_hint?: InsertionHint;
}

export interface SiteRules {
  domain?: string;
  allowed_subdomains?: string[];
  max_links_per_source_page?: number;
  max_links_per_target_page?: number;
  anchor_length_min_words?: number;
  anchor_length_max_words?: number;
  avoid_sections?: string[];
  existing_link_policy?: "skip" | "allow_different_anchor";
  language?: string | null;
}

export interface PipelineConfig {
  fetch_timeout_seconds?: number;
  fetch_max_concurrent?: number;
  embedding_model?: string;
  top_k_targets_per_source?: number;
  near_duplicate_threshold?: number;
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

export type JobStatus = "pending" | "running" | "completed" | "failed";

export interface JobInfo {
  job_id: string;
  status: JobStatus;
  progress: string;
  stats: Record<string, unknown>;
  errors: string[];
  results: Record<string, Suggestion[]> | null;
}
