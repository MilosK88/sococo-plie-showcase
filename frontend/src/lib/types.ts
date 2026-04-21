export interface SampleLead {
  company_name: string;
  contact_name: string;
  domain: string;
}

export interface UploadResponse {
  status: string;
  message: string;
}

export interface BatchTriggerResponse {
  status: string;
  job_id: string;
  message: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: "queued" | "processing" | "complete" | "failed";
  total: number;
  completed: number;
  error?: string | null;
}

export interface EnrichedLead {
  company_name: string;
  domain: string;
  plie_score: number;
  headcount_current: number;
  funding_stage: string;
  intent_score: number;
  message_draft_a: string;
  message_draft_b: string;
  message_draft_c: string;
}

export type AppState =
  | { phase: "idle" }
  | { phase: "uploading" }
  | { phase: "processing"; jobId: string }
  | { phase: "complete"; leads: EnrichedLead[] }
  | { phase: "failed"; error: string }
  | { phase: "empty_batch" };
