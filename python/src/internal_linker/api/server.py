"""FastAPI server for the internal linking engine."""

from __future__ import annotations

import asyncio
import logging
import uuid
from enum import Enum
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..config import PipelineConfig, SiteRules
from ..pipeline.orchestrator import PipelineResult, _run_pipeline_async

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Internal Linker API",
    description="NLP-powered internal link suggestion engine",
    version="0.1.0",
)


# ── Request / Response models ─────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    urls: list[str] = Field(..., min_length=2, max_length=500)
    config: PipelineConfig | None = None
    site_rules: SiteRules | None = None


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobInfo(BaseModel):
    job_id: str
    status: JobStatus
    progress: str = ""
    stats: dict[str, Any] = {}
    errors: list[str] = []
    results: dict[str, Any] | None = None


# ── In-memory job store ───────────────────────────────────────────────

_jobs: dict[str, JobInfo] = {}
_job_results: dict[str, PipelineResult] = {}


# ── Background task ───────────────────────────────────────────────────

async def _run_job(job_id: str, urls: list[str], config: PipelineConfig) -> None:
    """Run the pipeline as a background task."""
    job = _jobs[job_id]
    job.status = JobStatus.RUNNING

    def progress_cb(stage: str, current: int, total: int, detail: str = "") -> None:
        pct = int(current / total * 100) if total else 0
        job.progress = f"{stage}: {pct}% - {detail}"

    try:
        result = await _run_pipeline_async(urls, config, on_progress=progress_cb)
        _job_results[job_id] = result
        job.status = JobStatus.COMPLETED
        job.stats = result.stats
        job.errors = result.errors
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        job.status = JobStatus.FAILED
        job.errors.append(str(exc))


# ── Endpoints ─────────────────────────────────────────────────────────

@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/analyze", response_model=JobInfo)
async def analyze(request: AnalyzeRequest, background_tasks: BackgroundTasks) -> JobInfo:
    """Submit URLs for analysis. Returns a job ID to poll for results."""
    job_id = str(uuid.uuid4())

    config = request.config or PipelineConfig()
    if request.site_rules:
        config.site_rules = request.site_rules

    job = JobInfo(job_id=job_id, status=JobStatus.PENDING)
    _jobs[job_id] = job

    background_tasks.add_task(_run_job, job_id, request.urls, config)

    return job


@app.get("/api/results/{job_id}", response_model=JobInfo)
async def get_results(job_id: str) -> JobInfo:
    """Get the status and results of a job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _jobs[job_id]

    # Attach results if completed
    if job.status == JobStatus.COMPLETED and job_id in _job_results:
        result = _job_results[job_id]
        job.results = result.to_dict().get("results")

    return job


@app.get("/api/jobs")
async def list_jobs() -> list[dict[str, Any]]:
    """List all jobs with their statuses."""
    return [
        {"job_id": j.job_id, "status": j.status, "progress": j.progress}
        for j in _jobs.values()
    ]


def start_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the FastAPI server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)
