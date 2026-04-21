import { useState, useEffect, useRef } from "react";
import { pollJobStatus } from "@/lib/api";
import { JobStatusResponse } from "@/lib/types";

export interface LiveJobState {
  status: JobStatusResponse["status"];
  total: number;
  completed: number;
  error?: string | null;
  elapsedMs: number;
}

interface PollerOptions {
  onComplete?: (elapsedMs: number) => void;
  onFail?: (error: string) => void;
}

export function useJobPoller(jobId: string, options: PollerOptions = {}) {
  const [jobState, setJobState] = useState<LiveJobState>({
    status: "queued",
    total: 0,
    completed: 0,
    elapsedMs: 0,
  });

  const hasFinished = useRef(false);

  useEffect(() => {
    // Reset the ref whenever the jobId changes
    hasFinished.current = false;

    if (!jobId || jobId === "initializing") return;

    const startTime = Date.now();
    let intervalId: NodeJS.Timeout;

    const fetchStatus = async () => {
      if (hasFinished.current) return;

      try {
        const res = await pollJobStatus(jobId);
        const elapsedMs = Date.now() - startTime;
        
        setJobState((prev) => ({
          ...prev,
          status: res.status,
          total: res.total,
          completed: res.completed,
          error: res.error,
          elapsedMs,
        }));

        if (res.status === "complete") {
          hasFinished.current = true;
          clearInterval(intervalId);
          console.log("[POLLER] Firing onComplete callback");
          options.onComplete?.(elapsedMs);
        } else if (res.status === "failed") {
          hasFinished.current = true;
          clearInterval(intervalId);
          options.onFail?.(res.error || "Job failed");
        }
      } catch (err: any) {
        if (!hasFinished.current) {
          hasFinished.current = true;
          clearInterval(intervalId);
          options.onFail?.(err.message || "Failed to poll job status");
        }
      }
    };

    fetchStatus();
    intervalId = setInterval(fetchStatus, 1000);

    return () => clearInterval(intervalId);
  }, [jobId, options.onComplete, options.onFail]);

  return jobState;
}
