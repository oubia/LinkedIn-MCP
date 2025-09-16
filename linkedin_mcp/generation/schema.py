from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ResumeExperienceModel(BaseModel):
    title: str
    company: str
    startDate: str = Field(alias="startDate")
    endDate: Optional[str] = Field(default=None, alias="endDate")
    highlights: List[str]

    class Config:
        populate_by_name = True


class ResumeEducationModel(BaseModel):
    school: str
    degree: Optional[str] = None
    endDate: Optional[str] = Field(default=None, alias="endDate")

    class Config:
        populate_by_name = True


class ResumeAdditionalSectionModel(BaseModel):
    heading: str
    bullets: List[str]


class ResumeModel(BaseModel):
    summary: str
    skills: List[str]
    experiences: List[ResumeExperienceModel]
    education: List[ResumeEducationModel]
    additionalSections: List[ResumeAdditionalSectionModel] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class CoverLetterModel(BaseModel):
    header: List[str]
    body: List[str]
    closing: List[str]


class GenerationModel(BaseModel):
    resume: ResumeModel
    coverLetter: CoverLetterModel

    class Config:
        populate_by_name = True
