from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..config import (
    ProjectConfig,
    create_job_subdir,
    load_form_mapping,
    load_project_config,
    load_user_profile,
    write_metadata,
)
from ..documents.builder import DocumentBuilder
from ..generation.llm import LLMGenerator
from ..linkedin.client import LinkedInClient
from ..types import (
    ApplicationMetadata,
    DocumentPaths,
    GenerationInput,
    JobDetails,
    PreparedApplication,
    SubmitOptions,
    UserProfile,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ApplicationOrchestrator:
    def __init__(
        self,
        config: ProjectConfig,
        profile: UserProfile,
        generator: LLMGenerator,
        documents: DocumentBuilder,
        client: LinkedInClient,
    ) -> None:
        self.config = config
        self.profile = profile
        self.generator = generator
        self.documents = documents
        self.client = client

    @classmethod
    def create(cls) -> ApplicationOrchestrator:
        config = load_project_config()
        profile = load_user_profile(config.profile_path)
        generator = LLMGenerator(config.generation)
        documents = DocumentBuilder(config.output_dir)
        form_mapping = load_form_mapping(config.form_mapping_path)
        client = LinkedInClient(config.credentials, config.options, form_mapping)
        client.start()
        return cls(config, profile, generator, documents, client)

    def close(self) -> None:
        self.client.close()

    def prepare(self, job_url: str, regenerate: bool = False) -> PreparedApplication:
        job = self.client.fetch_job_details(job_url)
        if not regenerate:
            existing = self.load_prepared(job.id)
            if existing:
                logger.info("Reusing existing prepared artefacts", extra={"job_id": job.id})
                return existing
        logger.info("Generating tailored documents", extra={"job_id": job.id})
        generation_input = GenerationInput(profile=self.profile, job=job)
        content = self.generator.generate(generation_input)

        job_dir = create_job_subdir(self.config.output_dir, job.id)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        resume_path = job_dir / f"resume-{timestamp}.pdf"
        cover_path = job_dir / f"cover-letter-{timestamp}.pdf"
        llm_output_path = job_dir / f"generation-{timestamp}.json"
        metadata_path = job_dir / "metadata.json"

        self.documents.create_resume_pdf(content.resume, self.profile, job, resume_path)
        self.documents.create_cover_letter_pdf(content.cover_letter, self.profile, job, cover_path)
        llm_output_path.write_text(json.dumps(asdict(content), indent=2), encoding="utf-8")

        metadata = ApplicationMetadata(
            job=job,
            profile_name=self.profile.full_name,
            generated_at=datetime.utcnow().isoformat(),
            resume_path=str(resume_path),
            cover_letter_path=str(cover_path),
            llm_output_path=str(llm_output_path),
            submission_status="pending",
        )
        write_metadata(metadata_path, metadata)

        documents = DocumentPaths(
            resume_path=str(resume_path),
            cover_letter_path=str(cover_path),
            metadata_path=str(metadata_path),
            llm_output_path=str(llm_output_path),
        )
        return PreparedApplication(job=job, documents=documents, metadata=metadata)

    def submit(self, job_url: str, options: Optional[SubmitOptions] = None) -> PreparedApplication:
        options = options or SubmitOptions()
        prepared = self.prepare(job_url)
        result = self.client.submit_easy_apply(prepared.job, prepared.documents, self.profile, options)
        metadata = ApplicationMetadata(
            job=prepared.job,
            profile_name=prepared.metadata.profile_name,
            generated_at=prepared.metadata.generated_at,
            resume_path=prepared.documents.resume_path,
            cover_letter_path=prepared.documents.cover_letter_path,
            llm_output_path=prepared.documents.llm_output_path,
            submission_status="success" if result.success else "failed",
            submission_details=result.message,
        )
        write_metadata(Path(prepared.documents.metadata_path), metadata)
        return PreparedApplication(job=prepared.job, documents=prepared.documents, metadata=metadata)

    def submit_prepared(self, prepared: PreparedApplication, options: Optional[SubmitOptions] = None) -> PreparedApplication:
        options = options or SubmitOptions()
        result = self.client.submit_easy_apply(prepared.job, prepared.documents, self.profile, options)
        metadata = ApplicationMetadata(
            job=prepared.job,
            profile_name=prepared.metadata.profile_name,
            generated_at=prepared.metadata.generated_at,
            resume_path=prepared.documents.resume_path,
            cover_letter_path=prepared.documents.cover_letter_path,
            llm_output_path=prepared.documents.llm_output_path,
            submission_status="success" if result.success else "failed",
            submission_details=result.message,
        )
        write_metadata(Path(prepared.documents.metadata_path), metadata)
        return PreparedApplication(job=prepared.job, documents=prepared.documents, metadata=metadata)

    def list_prepared(self) -> List[PreparedApplication]:
        output_dir = Path(self.config.output_dir)
        if not output_dir.exists():
            return []
        prepared: List[PreparedApplication] = []
        for entry in sorted(output_dir.iterdir()):
            metadata_path = entry / "metadata.json"
            if not metadata_path.exists():
                continue
            metadata = self._load_metadata(metadata_path)
            documents = DocumentPaths(
                resume_path=metadata.resume_path,
                cover_letter_path=metadata.cover_letter_path,
                metadata_path=str(metadata_path),
                llm_output_path=metadata.llm_output_path or str(entry / "generation.json"),
            )
            prepared.append(PreparedApplication(job=metadata.job, documents=documents, metadata=metadata))
        prepared.sort(key=lambda item: item.metadata.generated_at or "", reverse=True)
        return prepared

    def load_prepared(self, job_id: str) -> Optional[PreparedApplication]:
        entry = Path(self.config.output_dir) / job_id
        metadata_path = entry / "metadata.json"
        if not metadata_path.exists():
            return None
        metadata = self._load_metadata(metadata_path)
        documents = DocumentPaths(
            resume_path=metadata.resume_path,
            cover_letter_path=metadata.cover_letter_path,
            metadata_path=str(metadata_path),
            llm_output_path=metadata.llm_output_path or str(entry / "generation.json"),
        )
        return PreparedApplication(job=metadata.job, documents=documents, metadata=metadata)

    def _load_metadata(self, path: Path) -> ApplicationMetadata:
        data = json.loads(path.read_text(encoding="utf-8"))
        job_data = data.get("job", {})
        job = self._job_from_dict(job_data)
        metadata = ApplicationMetadata(
            job=job,
            profile_name=data.get("profile_name") or data.get("profileName", ""),
            generated_at=data.get("generated_at") or data.get("generatedAt", ""),
            resume_path=data.get("resume_path") or data.get("resumePath", ""),
            cover_letter_path=data.get("cover_letter_path") or data.get("coverLetterPath", ""),
            llm_output_path=data.get("llm_output_path") or data.get("llmOutputPath"),
            submission_status=data.get("submission_status") or data.get("submissionStatus"),
            submission_details=data.get("submission_details") or data.get("submissionDetails"),
        )
        return metadata

    def _job_from_dict(self, data: dict) -> JobDetails:
        return JobDetails(
            id=data.get("id", ""),
            url=data.get("url", ""),
            title=data.get("title", ""),
            company=data.get("company", ""),
            location=data.get("location"),
            description=data.get("description", ""),
            workplace_type=data.get("workplace_type") or data.get("workplaceType"),
            seniority_level=data.get("seniority_level") or data.get("seniorityLevel"),
            employment_type=data.get("employment_type") or data.get("employmentType"),
            job_function=data.get("job_function") or data.get("jobFunction"),
            industries=data.get("industries", []),
            scraped_at=data.get("scraped_at") or data.get("scrapedAt", ""),
        )
