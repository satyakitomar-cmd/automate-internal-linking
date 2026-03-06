import type { AnalyzeRequest, JobInfo } from "@/types/api";

const BASE_URL = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API error ${response.status}: ${body}`);
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  analyze(body: AnalyzeRequest): Promise<{ job_id: string; status: string }> {
    return request("/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getResults(jobId: string): Promise<JobInfo> {
    return request(`/results/${jobId}`);
  },

  health(): Promise<{ status: string; node_api: string }> {
    return request("/health");
  },
};
