from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from ..types import GeneratedCoverLetter, GeneratedResume, JobDetails, UserProfile
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DocumentBuilder:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_resume_pdf(
        self,
        resume: GeneratedResume,
        profile: UserProfile,
        job: JobDetails,
        file_path: str | Path,
    ) -> Path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        c = canvas.Canvas(str(path), pagesize=LETTER)
        text = c.beginText()
        text.setTextOrigin(0.75 * inch, 10.5 * inch)
        text.setFont("Helvetica-Bold", 18)
        text.textLine(profile.full_name)
        text.setFont("Helvetica", 12)
        text.textLine(f"{profile.title} | {profile.location}")
        text.textLine(f"{profile.email} | {profile.phone}")
        if profile.websites:
            text.textLine(" | ".join(profile.websites))
        text.textLine("")

        text.setFont("Helvetica-Bold", 13)
        text.textLine("Professional Summary")
        text.setFont("Helvetica", 11)
        for line in _wrap_text(resume.summary, 95):
            text.textLine(line)
        text.textLine("")

        text.setFont("Helvetica-Bold", 13)
        text.textLine("Core Skills")
        text.setFont("Helvetica", 11)
        text.textLine(", ".join(resume.skills))
        text.textLine("")

        text.setFont("Helvetica-Bold", 13)
        text.textLine("Experience")
        text.setFont("Helvetica", 11)
        for exp in resume.experiences:
            text.setFont("Helvetica-Bold", 12)
            text.textLine(f"{exp.title} • {exp.company}")
            text.setFont("Helvetica-Oblique", 10)
            time_range = f"{exp.start_date} – {exp.end_date or 'Present'}"
            text.textLine(time_range)
            text.setFont("Helvetica", 11)
            for bullet in exp.highlights:
                for line in _wrap_text(f"• {bullet}", 95, indent=4):
                    text.textLine(line)
            text.textLine("")

        if resume.education:
            text.setFont("Helvetica-Bold", 13)
            text.textLine("Education")
            text.setFont("Helvetica", 11)
            for edu in resume.education:
                text.setFont("Helvetica-Bold", 12)
                text.textLine(edu.school)
                text.setFont("Helvetica", 11)
                details = ", ".join(filter(None, [edu.degree, edu.end_date]))
                if details:
                    text.textLine(details)
                text.textLine("")

        if resume.additional_sections:
            for section in resume.additional_sections:
                text.setFont("Helvetica-Bold", 13)
                text.textLine(section.heading)
                text.setFont("Helvetica", 11)
                for bullet in section.bullets:
                    for line in _wrap_text(f"• {bullet}", 95, indent=4):
                        text.textLine(line)
                text.textLine("")

        text.setFont("Helvetica-Oblique", 8)
        text.textLine("")
        text.textLine(f"Generated for {job.company} – {job.title}")

        c.drawText(text)
        c.showPage()
        c.save()
        logger.info("Resume PDF generated", extra={"path": str(path)})
        return path

    def create_cover_letter_pdf(
        self,
        cover_letter: GeneratedCoverLetter,
        profile: UserProfile,
        job: JobDetails,
        file_path: str | Path,
    ) -> Path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        c = canvas.Canvas(str(path), pagesize=LETTER)
        text = c.beginText()
        text.setTextOrigin(0.75 * inch, 10.5 * inch)
        text.setFont("Helvetica-Bold", 18)
        text.textLine(profile.full_name)
        text.setFont("Helvetica", 11)
        text.textLine(profile.location)
        text.textLine(f"{profile.email} | {profile.phone}")
        text.textLine("")

        text.setFont("Helvetica", 11)
        text.textLine(_today_string())
        text.textLine("")

        for line in cover_letter.header:
            for wrapped in _wrap_text(line, 95):
                text.textLine(wrapped)
        text.textLine("")

        for paragraph in cover_letter.body:
            for wrapped in _wrap_text(paragraph, 95):
                text.textLine(wrapped)
            text.textLine("")

        text.setFont("Helvetica-Bold", 11)
        for line in cover_letter.closing:
            text.textLine(line)

        text.setFont("Helvetica-Oblique", 8)
        text.textLine("")
        text.textLine(f"Generated for {job.company} – {job.title}")

        c.drawText(text)
        c.showPage()
        c.save()
        logger.info("Cover letter PDF generated", extra={"path": str(path)})
        return path

    def write_generation_payload(self, file_path: str | Path, content: Any) -> Path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content, indent=2), encoding="utf-8")
        return path


def _wrap_text(text: str, width: int, *, indent: int = 0) -> Iterable[str]:
    import textwrap

    wrapper = textwrap.TextWrapper(width=width)
    if indent:
        wrapper.subsequent_indent = " " * indent

    lines = wrapper.wrap(text)
    for line in lines:
        yield line


def _today_string() -> str:
    from datetime import date

    return date.today().strftime("%B %d, %Y")
