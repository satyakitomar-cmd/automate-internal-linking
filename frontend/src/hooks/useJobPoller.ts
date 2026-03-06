import { useEffect, useRef, useState, useCallback } from "react";
import { apiClient } from "@/api/client";
import type { JobInfo } from "@/types/api";

interface UseJobPollerOptions {
  intervalMs?: number;
  onCompleted?: (job: JobInfo) => void;
  onFailed?: (job: JobInfo) => void;
}

export function useJobPoller(
  jobId: string | null,
  options: UseJobPollerOptions = {}
) {
  const { intervalMs = 2000, onCompleted, onFailed } = options;
  const [jobInfo, setJobInfo] = useState<JobInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onCompletedRef = useRef(onCompleted);
  const onFailedRef = useRef(onFailed);

  onCompletedRef.current = onCompleted;
  onFailedRef.current = onFailed;

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!jobId) return;

    let active = true;

    const poll = async () => {
      try {
        const info = await apiClient.getResults(jobId);
        if (!active) return;
        setJobInfo(info);
        setError(null);

        if (info.status === "completed") {
          stopPolling();
          onCompletedRef.current?.(info);
        } else if (info.status === "failed") {
          stopPolling();
          onFailedRef.current?.(info);
        }
      } catch (err) {
        if (!active) return;
        setError(String(err));
      }
    };

    poll();
    intervalRef.current = setInterval(poll, intervalMs);

    return () => {
      active = false;
      stopPolling();
    };
  }, [jobId, intervalMs, stopPolling]);

  return { jobInfo, error, stopPolling };
}
