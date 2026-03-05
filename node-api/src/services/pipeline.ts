/**
 * Service that communicates with the Python FastAPI backend
 * via HTTP or spawns the Python CLI as a subprocess.
 */

import { AnalyzeRequest, JobInfo } from "../types";

const PYTHON_API_BASE = process.env.PYTHON_API_URL || "http://localhost:8000";

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`Python API error ${resp.status}: ${body}`);
  }
  return resp.json() as Promise<T>;
}

export async function submitAnalysis(request: AnalyzeRequest): Promise<JobInfo> {
  return fetchJSON<JobInfo>(`${PYTHON_API_BASE}/api/analyze`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getJobResults(jobId: string): Promise<JobInfo> {
  return fetchJSON<JobInfo>(`${PYTHON_API_BASE}/api/results/${jobId}`);
}

export async function healthCheck(): Promise<{ status: string; version: string }> {
  return fetchJSON<{ status: string; version: string }>(
    `${PYTHON_API_BASE}/api/health`
  );
}
