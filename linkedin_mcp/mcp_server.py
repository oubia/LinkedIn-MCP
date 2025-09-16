from __future__ import annotations

import atexit
from typing import Annotated, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .services.orchestrator import ApplicationOrchestrator
from .types import PreparedApplication, SubmitOptions
from .utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

server = FastMCP(
    name="linkedin-mcp-python",
    instructions=(
        "Automate LinkedIn Easy Apply: scrape job descriptions, generate tailored resumes and cover letters, "
        "and optionally submit applications."
    ),
)

_orchestrator: ApplicationOrchestrator | None = None


def get_orchestrator() -> ApplicationOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        logger.info("Initialising orchestrator")
        _orchestrator = ApplicationOrchestrator.create()
    return _orchestrator


JobUrlList = Annotated[List[str], Field(min_length=1, description="List of LinkedIn job URLs")]


@server.tool(
    name="prepare_linkedin_applications",
    description="Scrape LinkedIn jobs, generate tailored PDFs, and store artefacts on disk.",
)
def prepare_linkedin_applications(job_urls: JobUrlList, regenerate: bool = False) -> dict:
    orchestrator = get_orchestrator()
    applications = []
    for url in job_urls:
        prepared = orchestrator.prepare(url, regenerate=regenerate)
        applications.append(_prepared_to_dict(prepared))
    return {"applications": applications}


@server.tool(
    name="submit_linkedin_applications",
    description="Submit Easy Apply applications using generated documents or previously prepared artefacts.",
)
def submit_linkedin_applications(
    job_urls: Optional[List[str]] = None,
    job_ids: Optional[List[str]] = None,
    skip_when_already_applied: bool = True,
) -> dict:
    orchestrator = get_orchestrator()
    results = []

    prepared_targets: List[PreparedApplication] = []
    if job_ids:
        for job_id in job_ids:
            prepared = orchestrator.load_prepared(job_id)
            if prepared:
                prepared_targets.append(prepared)
            else:
                results.append(
                    {
                        "jobId": job_id,
                        "status": "missing",
                        "details": "No prepared application found",
                    }
                )
    for prepared in prepared_targets:
        updated = orchestrator.submit_prepared(prepared, SubmitOptions(skip_when_already_applied=skip_when_already_applied))
        results.append(_submission_result(updated))

    for url in job_urls or []:
        updated = orchestrator.submit(url, SubmitOptions(skip_when_already_applied=skip_when_already_applied))
        results.append(_submission_result(updated))

    return {"results": results}


@server.tool(
    name="list_prepared_applications",
    description="List prepared LinkedIn application artefacts saved on disk.",
)
def list_prepared_applications() -> dict:
    orchestrator = get_orchestrator()
    prepared = orchestrator.list_prepared()
    return {"applications": [_prepared_to_dict(item) for item in prepared]}


def _prepared_to_dict(prepared: PreparedApplication) -> dict:
    return {
        "jobId": prepared.job.id,
        "jobTitle": prepared.job.title,
        "company": prepared.job.company,
        "generatedAt": prepared.metadata.generated_at,
        "resumePath": prepared.documents.resume_path,
        "coverLetterPath": prepared.documents.cover_letter_path,
        "metadataPath": prepared.documents.metadata_path,
        "llmOutputPath": prepared.documents.llm_output_path,
        "submissionStatus": prepared.metadata.submission_status,
        "submissionDetails": prepared.metadata.submission_details,
    }


def _submission_result(prepared: PreparedApplication) -> dict:
    return {
        "jobId": prepared.job.id,
        "jobTitle": prepared.job.title,
        "company": prepared.job.company,
        "status": prepared.metadata.submission_status or "pending",
        "details": prepared.metadata.submission_details or "",
        "metadataPath": prepared.documents.metadata_path,
    }


def run() -> None:
    try:
        server.run("stdio")
    finally:
        if _orchestrator is not None:
            _orchestrator.close()


def _shutdown() -> None:
    if _orchestrator is not None:
        _orchestrator.close()


atexit.register(_shutdown)


if __name__ == "__main__":
    run()
