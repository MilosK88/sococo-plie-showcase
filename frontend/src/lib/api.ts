import { 
  UploadResponse, 
  BatchTriggerResponse, 
  JobStatusResponse, 
  EnrichedLead 
} from "./types";

export async function uploadCsv(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("/api/upload", {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Upload failed");
  }

  return res.json();
}

export async function triggerBatch(): Promise<BatchTriggerResponse> {
  const res = await fetch("/api/batch", {
    method: "POST",
  });

  if (!res.ok) {
    const err = await res.json();
    // 409 Conflict handled here if thrown from the proxy
    throw new Error(err.error || "Batch trigger failed");
  }

  return res.json();
}

export async function pollJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`/api/job-status/${jobId}`);

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Failed to poll job status");
  }

  return res.json();
}

export async function fetchResults(): Promise<EnrichedLead[]> {
  const res = await fetch("/api/results");

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Failed to fetch results");
  }

  return res.json();
}
