from __future__ import annotations

import json
import re
from typing import Any

import httpx
from anthropic import Anthropic
from openai import OpenAI

from ..prompts.generation import build_generation_prompt
from ..types import (
    GenerationInput,
    GenerationProviderConfig,
    GeneratedContent,
    GeneratedCoverLetter,
    GeneratedResume,
    GeneratedResumeEducation,
    GeneratedResumeExperience,
    GeneratedResumeSection,
)
from ..utils.logging import get_logger
from .schema import GenerationModel

logger = get_logger(__name__)


class LLMGenerator:
    def __init__(self, config: GenerationProviderConfig) -> None:
        self.config = config

    def generate(self, payload: GenerationInput) -> GeneratedContent:
        prompt = build_generation_prompt(payload)
        raw = self._dispatch(prompt)
        parsed = self._parse_json(raw)
        model = GenerationModel.model_validate(parsed)
        resume = GeneratedResume(
            summary=model.resume.summary,
            skills=model.resume.skills,
            experiences=[
                GeneratedResumeExperience(
                    title=item.title,
                    company=item.company,
                    start_date=item.startDate,
                    end_date=item.endDate,
                    highlights=item.highlights,
                )
                for item in model.resume.experiences
            ],
            education=[
                GeneratedResumeEducation(
                    school=item.school,
                    degree=item.degree,
                    end_date=item.endDate,
                )
                for item in model.resume.education
            ],
            additional_sections=[
                GeneratedResumeSection(heading=section.heading, bullets=section.bullets)
                for section in model.resume.additionalSections
            ],
        )
        cover_letter = GeneratedCoverLetter(
            header=model.coverLetter.header,
            body=model.coverLetter.body,
            closing=model.coverLetter.closing,
        )
        return GeneratedContent(resume=resume, cover_letter=cover_letter, raw_model_response=raw)

    def _dispatch(self, prompt: str) -> str:
        provider = self.config.provider.lower()
        if provider == "openai":
            return self._call_openai(prompt)
        if provider == "anthropic":
            return self._call_anthropic(prompt)
        if provider == "azure-openai":
            return self._call_azure_openai(prompt)
        if provider == "mock":
            return self._mock_response(prompt)
        raise ValueError(f"Unsupported generation provider: {self.config.provider}")

    def _call_openai(self, prompt: str) -> str:
        if not self.config.api_key:
            raise ValueError("GENERATION_API_KEY is required for OpenAI provider")
        client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            organization=self.config.organization,
        )
        response = client.chat.completions.create(
            model=self.config.model,
            temperature=self.config.temperature or 0.4,
            max_tokens=self.config.max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": "You are a meticulous career coach that only replies with strict JSON and never apologises.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        if isinstance(content, list):
            text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        else:
            text = content or ""
        if not text:
            raise RuntimeError("OpenAI response did not contain any text")
        return text

    def _call_anthropic(self, prompt: str) -> str:
        if not self.config.api_key:
            raise ValueError("GENERATION_API_KEY is required for Anthropic provider")
        client = Anthropic(api_key=self.config.api_key)
        response = client.messages.create(
            model=self.config.model,
            temperature=self.config.temperature or 0.2,
            max_tokens=self.config.max_tokens or 2048,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(part.text for part in response.content if hasattr(part, "text"))
        if not text:
            raise RuntimeError("Anthropic response did not contain text content")
        return text

    def _call_azure_openai(self, prompt: str) -> str:
        if not self.config.api_key or not self.config.base_url:
            raise ValueError("GENERATION_API_KEY and GENERATION_BASE_URL are required for Azure OpenAI")
        api_version = self.config.api_version or "2024-02-15-preview"
        url = f"{self.config.base_url}/openai/deployments/{self.config.model}/chat/completions"
        params = {"api-version": api_version}
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a meticulous career coach that only replies with strict JSON and never apologises.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.config.temperature or 0.3,
            "max_tokens": self.config.max_tokens or 2048,
        }
        headers = {
            "Content-Type": "application/json",
            "api-key": self.config.api_key,
        }
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, params=params, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        message = data.get("choices", [{}])[0].get("message", {})
        text = message.get("content", "")
        if isinstance(text, list):
            text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
        if not text:
            raise RuntimeError("Azure OpenAI response missing text content")
        return text

    def _mock_response(self, prompt: str) -> str:
        logger.warning("Using mock generator; output will be placeholder", extra={"prompt_length": len(prompt)})
        return json.dumps(
            {
                "resume": {
                    "summary": "Seasoned professional with tailored experience for the role.",
                    "skills": ["Placeholder Skill"],
                    "experiences": [
                        {
                            "title": "Mock Engineer",
                            "company": "Example Corp",
                            "startDate": "2021",
                            "highlights": [
                                "Delivered sample project demonstrating automation capabilities",
                                "Collaborated with team to refine AI-generated documents",
                            ],
                        }
                    ],
                    "education": [
                        {
                            "school": "Mock University",
                            "degree": "BSc Computer Science",
                            "endDate": "2018",
                        }
                    ],
                    "additionalSections": [],
                },
                "coverLetter": {
                    "header": ["Hiring Manager", "Example Corp"],
                    "body": [
                        "I am excited to apply for this opportunity.",
                        "My automation experience aligns with the role's goals.",
                        "I would welcome the chance to discuss further.",
                    ],
                    "closing": ["Sincerely", "Mock Candidate"],
                },
            },
            indent=2,
        )

    def _parse_json(self, raw: str) -> Any:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Model output was not valid JSON: {exc}" ) from exc
            raise ValueError("Model output did not contain valid JSON")
