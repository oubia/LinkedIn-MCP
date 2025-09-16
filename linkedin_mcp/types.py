from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence


@dataclass
class LinkedInCredentials:
    username: str
    password: str
    session_cookie: Optional[str] = None


@dataclass
class LinkedInOptions:
    headless: bool = True
    slow_mo: Optional[int] = None
    storage_state_path: str = "data/linkedin.storage.json"


@dataclass
class JobDetails:
    id: str
    url: str
    title: str
    company: str
    location: Optional[str]
    description: str
    workplace_type: Optional[str] = None
    seniority_level: Optional[str] = None
    employment_type: Optional[str] = None
    job_function: Optional[str] = None
    industries: Sequence[str] = field(default_factory=list)
    scraped_at: str = ""


@dataclass
class ProfileExperience:
    title: str
    company: str
    start_date: str
    end_date: Optional[str] = None
    location: Optional[str] = None
    achievements: List[str] = field(default_factory=list)


@dataclass
class ProfileEducation:
    school: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    achievements: List[str] = field(default_factory=list)


@dataclass
class UserProfile:
    full_name: str
    title: str
    email: str
    phone: str
    location: str
    summary: str
    skills: List[str]
    languages: List[str] = field(default_factory=list)
    websites: List[str] = field(default_factory=list)
    experiences: List[ProfileExperience] = field(default_factory=list)
    education: List[ProfileEducation] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)


@dataclass
class GenerationProviderConfig:
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    organization: Optional[str] = None
    api_version: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


@dataclass
class GenerationInput:
    profile: UserProfile
    job: JobDetails


@dataclass
class GeneratedResumeExperience:
    title: str
    company: str
    start_date: str
    end_date: Optional[str]
    highlights: List[str]


@dataclass
class GeneratedResumeEducation:
    school: str
    degree: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class GeneratedResumeSection:
    heading: str
    bullets: List[str]


@dataclass
class GeneratedResume:
    summary: str
    skills: List[str]
    experiences: List[GeneratedResumeExperience]
    education: List[GeneratedResumeEducation]
    additional_sections: List[GeneratedResumeSection] = field(default_factory=list)


@dataclass
class GeneratedCoverLetter:
    header: List[str]
    body: List[str]
    closing: List[str]


@dataclass
class GeneratedContent:
    resume: GeneratedResume
    cover_letter: GeneratedCoverLetter
    raw_model_response: str


@dataclass
class DocumentPaths:
    resume_path: str
    cover_letter_path: str
    metadata_path: str
    llm_output_path: str


@dataclass
class ApplicationMetadata:
    job: JobDetails
    profile_name: str
    generated_at: str
    resume_path: str
    cover_letter_path: str
    llm_output_path: Optional[str] = None
    submission_status: Optional[str] = None
    submission_details: Optional[str] = None


@dataclass
class PreparedApplication:
    job: JobDetails
    documents: DocumentPaths
    metadata: ApplicationMetadata


@dataclass
class FormFieldMapping:
    keywords: List[str]
    value: str


@dataclass
class FormMappingConfig:
    mappings: List[FormFieldMapping]
    default_resume_path: Optional[str] = None
    default_cover_letter_path: Optional[str] = None


@dataclass
class ApplicationRequest:
    job_urls: List[str]
    profile_path: Optional[str] = None
    regenerate: bool = False
    submit: bool = False


@dataclass
class SubmitOptions:
    upload_resume: Optional[str] = None
    upload_cover_letter: Optional[str] = None
    skip_when_already_applied: bool = True
