from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .types import (
    ApplicationMetadata,
    FormFieldMapping,
    FormMappingConfig,
    GenerationProviderConfig,
    LinkedInCredentials,
    LinkedInOptions,
    ProfileEducation,
    ProfileExperience,
    UserProfile,
)

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass
class ProjectConfig:
    credentials: LinkedInCredentials
    options: LinkedInOptions
    generation: GenerationProviderConfig
    profile_path: Path
    output_dir: Path
    form_mapping_path: Path


class ProfileExperienceModel(BaseModel):
    title: str
    company: str
    startDate: str = Field(alias="startDate")
    endDate: str | None = Field(default=None, alias="endDate")
    location: str | None = None
    achievements: list[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class ProfileEducationModel(BaseModel):
    school: str
    degree: str | None = None
    fieldOfStudy: str | None = Field(default=None, alias="fieldOfStudy")
    startDate: str | None = Field(default=None, alias="startDate")
    endDate: str | None = Field(default=None, alias="endDate")
    achievements: list[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class UserProfileModel(BaseModel):
    fullName: str = Field(alias="fullName")
    title: str
    email: str
    phone: str
    location: str
    summary: str
    skills: list[str]
    languages: list[str] = Field(default_factory=list)
    websites: list[str] = Field(default_factory=list)
    experiences: list[ProfileExperienceModel] = Field(default_factory=list)
    education: list[ProfileEducationModel] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class FormFieldMappingModel(BaseModel):
    keywords: list[str]
    value: str


class FormMappingModel(BaseModel):
    mappings: list[FormFieldMappingModel]
    defaultResumePath: str | None = Field(default=None, alias="defaultResumePath")
    defaultCoverLetterPath: str | None = Field(default=None, alias="defaultCoverLetterPath")

    class Config:
        populate_by_name = True


def load_project_config() -> ProjectConfig:
    storage_state = os.getenv("LINKEDIN_STORAGE_STATE_PATH", "data/linkedin.storage.json")

    credentials = LinkedInCredentials(
        username=_env_required("LINKEDIN_USERNAME"),
        password=_env_required("LINKEDIN_PASSWORD"),
        session_cookie=os.getenv("LINKEDIN_SESSION_COOKIE"),
    )

    options = LinkedInOptions(
        headless=os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() != "false",
        slow_mo=int(os.getenv("PLAYWRIGHT_SLOWMO", "0")) or None,
        storage_state_path=_resolve_path(storage_state),
    )

    provider = os.getenv("GENERATION_PROVIDER", "openai")
    model = os.getenv("GENERATION_MODEL", _default_model_for_provider(provider))

    generation = GenerationProviderConfig(
        provider=provider,
        model=model,
        api_key=os.getenv("GENERATION_API_KEY"),
        base_url=os.getenv("GENERATION_BASE_URL"),
        organization=os.getenv("OPENAI_ORGANIZATION"),
        api_version=_resolve_api_version(provider),
        temperature=float(os.getenv("GENERATION_TEMPERATURE", "0") or 0) or None,
        max_tokens=int(os.getenv("GENERATION_MAX_TOKENS", "0") or 0) or None,
    )

    profile_path = _resolve_path(os.getenv("USER_PROFILE_PATH", "data/user_profile.json"))
    output_dir = _resolve_path(os.getenv("OUTPUT_DIR", "output"))
    form_mapping_path = _resolve_path(os.getenv("FORM_MAPPING_PATH", "data/form_mapping.json"))

    return ProjectConfig(
        credentials=credentials,
        options=options,
        generation=generation,
        profile_path=profile_path,
        output_dir=output_dir,
        form_mapping_path=form_mapping_path,
    )


def load_user_profile(path: Path) -> UserProfile:
    if not path.exists():
        raise FileNotFoundError(f"User profile file not found at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    model = UserProfileModel.model_validate(data)
    return UserProfile(
        full_name=model.fullName,
        title=model.title,
        email=model.email,
        phone=model.phone,
        location=model.location,
        summary=model.summary,
        skills=model.skills,
        languages=model.languages,
        websites=model.websites,
        experiences=[
            ProfileExperience(
                title=exp.title,
                company=exp.company,
                start_date=exp.startDate,
                end_date=exp.endDate,
                location=exp.location,
                achievements=exp.achievements,
            )
            for exp in model.experiences
        ],
        education=[
            ProfileEducation(
                school=edu.school,
                degree=edu.degree,
                field_of_study=edu.fieldOfStudy,
                start_date=edu.startDate,
                end_date=edu.endDate,
                achievements=edu.achievements,
            )
            for edu in model.education
        ],
        certifications=model.certifications,
        interests=model.interests,
    )


def load_form_mapping(path: Path) -> FormMappingConfig:
    if not path.exists():
        raise FileNotFoundError(f"Form mapping file not found at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    model = FormMappingModel.model_validate(data)
    mappings = [FormFieldMapping(keywords=item.keywords, value=item.value) for item in model.mappings]
    return FormMappingConfig(
        mappings=mappings,
        default_resume_path=model.defaultResumePath,
        default_cover_letter_path=model.defaultCoverLetterPath,
    )


def create_job_subdir(output_dir: Path, job_id: str) -> Path:
    job_dir = output_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def write_metadata(metadata_path: Path, metadata: ApplicationMetadata) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    payload = _dataclass_to_dict(metadata)
    metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _dataclass_to_dict(obj: Any) -> Any:
    if isinstance(obj, list):
        return [_dataclass_to_dict(item) for item in obj]
    if hasattr(obj, "__dataclass_fields__"):
        return {key: _dataclass_to_dict(value) for key, value in vars(obj).items()}
    return obj


def _resolve_path(relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        return candidate
    return (ROOT_DIR / candidate).resolve()


def _env_required(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Missing required environment variable {key}")
    return value


def _default_model_for_provider(provider: str) -> str:
    mapping = {
        "openai": "gpt-4o",
        "anthropic": "claude-3-opus-20240229",
        "azure-openai": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
        "mock": "mock-model",
    }
    return mapping.get(provider.lower(), "gpt-4o")


def _resolve_api_version(provider: str) -> str | None:
    if provider.lower() == "azure-openai":
        return os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    return os.getenv("GENERATION_API_VERSION")
