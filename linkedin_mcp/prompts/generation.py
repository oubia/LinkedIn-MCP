from __future__ import annotations

from ..types import GenerationInput


def build_generation_prompt(payload: GenerationInput) -> str:
    profile = payload.profile
    job = payload.job

    experiences_text = "\n".join(
        (
            f"- {exp.title} at {exp.company} ({exp.start_date}"
            f"{' - ' + exp.end_date if exp.end_date else ''})"
            f"{' in ' + exp.location if exp.location else ''}\n"
            f"  Achievements: {'; '.join(exp.achievements)}"
        )
        for exp in profile.experiences
    )

    education_text = "\n".join(
        (
            f"- {edu.school}"
            f"{', ' + edu.degree if edu.degree else ''}"
            f"{', ' + edu.field_of_study if edu.field_of_study else ''}"
            f"{f' ({edu.end_date})' if edu.end_date else ''}"
        )
        for edu in profile.education
    )

    profile_text = (
        "Applicant Profile:\n"
        f"Name: {profile.full_name}\n"
        f"Title: {profile.title}\n"
        f"Location: {profile.location}\n"
        f"Email: {profile.email}\n"
        f"Phone: {profile.phone}\n"
        f"Summary: {profile.summary}\n"
        f"Skills: {', '.join(profile.skills)}\n"
        f"Experiences:\n{experiences_text if experiences_text else 'None listed'}\n"
        f"Education:\n{education_text if education_text else 'None listed'}\n"
    )

    if profile.certifications:
        profile_text += f"Certifications: {', '.join(profile.certifications)}\n"
    if profile.languages:
        profile_text += f"Languages: {', '.join(profile.languages)}\n"
    if profile.interests:
        profile_text += f"Interests: {', '.join(profile.interests)}\n"

    job_text = (
        "Job Posting:\n"
        f"Title: {job.title}\n"
        f"Company: {job.company}\n"
        f"Location: {job.location or 'Unknown'}\n"
        f"Seniority Level: {job.seniority_level or 'Unknown'}\n"
        f"Employment Type: {job.employment_type or 'Unknown'}\n"
        f"Job Function: {job.job_function or 'Unknown'}\n"
        f"Industries: {', '.join(job.industries) if job.industries else 'Unknown'}\n"
        f"Description:\n{job.description}\n"
    )

    instructions = (
        "You are an expert technical recruiter and professional CV writer. "
        "Create a tailored resume and cover letter that aligns the applicant with the job requirements. "
        "Focus on measurable achievements and relevant skills while remaining truthful to the applicant profile.\n\n"
        "Return strictly valid JSON matching this schema:\n"
        "{\n"
        "  \"resume\": {\n"
        "    \"summary\": string,\n"
        "    \"skills\": string[],\n"
        "    \"experiences\": Array<{\"title\": string, \"company\": string, \"startDate\": string, \"endDate\"?: string, \"highlights\": string[]}>,\n"
        "    \"education\": Array<{\"school\": string, \"degree\"?: string, \"endDate\"?: string}>,\n"
        "    \"additionalSections\"?: Array<{\"heading\": string, \"bullets\": string[]}>\n"
        "  },\n"
        "  \"coverLetter\": {\n"
        "    \"header\": string[],\n"
        "    \"body\": string[],\n"
        "    \"closing\": string[]\n"
        "  }\n"
        "}\n\n"
        "Ensure bullet points start with an action verb and include metrics when available. "
        "Keep each bullet under 30 words. The cover letter body should have 3-4 paragraphs, each in a separate array entry.\n\n"
    )

    return f"{instructions}{profile_text}\n{job_text}"
