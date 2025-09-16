from __future__ import annotations

from pathlib import Path
from typing import Optional

from playwright.sync_api import Browser, BrowserContext, ElementHandle, Page, sync_playwright
from ..types import (
    DocumentPaths,
    FormMappingConfig,
    JobDetails,
    LinkedInCredentials,
    LinkedInOptions,
    SubmitOptions,
    UserProfile,
)
from ..utils.logging import get_logger
from ..utils.slugify import slugify

logger = get_logger(__name__)


class EasyApplyResult(dict):
    @property
    def success(self) -> bool:
        return bool(self.get("success"))

    @property
    def message(self) -> str:
        return str(self.get("message", ""))


class LinkedInClient:
    def __init__(
        self,
        credentials: LinkedInCredentials,
        options: LinkedInOptions,
        form_mapping: FormMappingConfig,
    ) -> None:
        self.credentials = credentials
        self.options = options
        self.form_mapping = form_mapping
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self) -> None:
        if self.browser:
            return
        self._playwright = sync_playwright().start()
        storage_state = None
        storage_path = Path(self.options.storage_state_path)
        if storage_path.exists():
            storage_state = str(storage_path)
        self.browser = self._playwright.chromium.launch(
            headless=self.options.headless,
            slow_mo=self.options.slow_mo,
        )
        self.context = self.browser.new_context(storage_state=storage_state)
        self.page = self.context.new_page()
        logger.info("Playwright browser launched", extra={"headless": self.options.headless})
        self._ensure_logged_in()

    def close(self) -> None:
        try:
            self.page and self.page.close()
        finally:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self._playwright:
                self._playwright.stop()
        self.browser = None
        self.context = None
        self.page = None
        self._playwright = None

    def fetch_job_details(self, url: str) -> JobDetails:
        page = self._require_page()
        logger.info("Fetching LinkedIn job", extra={"url": url})
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.wait_for_selector("div.jobs-details-top-card", timeout=10_000)

        title = page.locator("h1").first.text_content() or ""
        company = self._first_non_empty_text(
            page,
            ["a.top-card-layout__company-url", "span.jobs-unified-top-card__company-name"],
        )
        location = self._first_non_empty_text(
            page,
            ["span.jobs-unified-top-card__bullet", "span.jobs-unified-top-card__subtitle"]
        )
        insights = [
            text.strip()
            for text in page.locator("li.jobs-unified-top-card__job-insight").all_inner_texts()
            if text.strip()
        ]
        description = self._extract_description(page)
        job_id = self._extract_job_id(url) or slugify(f"{company}-{title}")

        job = JobDetails(
            id=job_id,
            url=url,
            title=title.strip(),
            company=company.strip(),
            location=location.strip() or None,
            description=description,
            workplace_type=_match_insight(insights, "workplace"),
            seniority_level=_match_insight(insights, "seniority"),
            employment_type=_match_insight(insights, "employment"),
            job_function=_match_insight(insights, "job function"),
            industries=[
                insight.replace("Industries", "").strip()
                for insight in insights
                if "industr" in insight.lower()
            ],
            scraped_at=_current_timestamp(),
        )
        logger.info("Job scraped", extra={"job_id": job.id})
        return job

    def submit_easy_apply(
        self,
        job: JobDetails,
        docs: DocumentPaths,
        profile: UserProfile,
        options: SubmitOptions,
    ) -> EasyApplyResult:
        page = self._require_page()
        page.goto(job.url, wait_until="networkidle")
        page.wait_for_timeout(1000)

        applied_button = page.locator("button.jobs-apply-button:has-text('Applied')")
        if applied_button.count() > 0 and options.skip_when_already_applied:
            return EasyApplyResult(success=False, message="Already applied to this job")

        apply_button = page.locator("button.jobs-apply-button").first
        if apply_button.count() == 0:
            raise RuntimeError("Easy Apply button not available")
        button_text = (apply_button.inner_text() or "").lower()
        if "easy apply" not in button_text:
            raise RuntimeError("Job does not use Easy Apply flow")
        apply_button.click()
        page.wait_for_selector("div.jobs-easy-apply-content", timeout=10_000)

        return self._fill_easy_apply_wizard(page, profile, docs, options)

    # Internal helpers -------------------------------------------------

    def _ensure_logged_in(self) -> None:
        page = self._require_page()
        page.goto("https://www.linkedin.com/feed/", wait_until="networkidle")
        page.wait_for_timeout(1000)
        if "checkpoint" in page.url:
            logger.warning("LinkedIn sign-in checkpoint encountered", extra={"url": page.url})
        if "/feed" in page.url:
            logger.info("LinkedIn session active")
            return

        logger.info("Logging into LinkedIn")
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        page.fill("input#username", self.credentials.username)
        page.fill("input#password", self.credentials.password)
        with page.expect_navigation(wait_until="networkidle"):
            page.click("button[type='submit']")
        if "/feed" not in page.url:
            raise RuntimeError("LinkedIn login failed; complete MFA manually then retry")

        if self.credentials.session_cookie:
            assert self.context is not None
            self.context.add_cookies(
                [
                    {
                        "name": "li_at",
                        "value": self.credentials.session_cookie,
                        "domain": ".linkedin.com",
                        "path": "/",
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "None",
                    }
                ]
            )
        storage_path = Path(self.options.storage_state_path)
        if self.context and storage_path:
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.context.storage_state(path=str(storage_path))
            logger.info("LinkedIn session stored", extra={"storage": str(storage_path)})

    def _fill_easy_apply_wizard(
        self,
        page: Page,
        profile: UserProfile,
        docs: DocumentPaths,
        options: SubmitOptions,
    ) -> EasyApplyResult:
        step = 1
        while True:
            modal = page.locator("div.jobs-easy-apply-content").first
            if modal.count() == 0:
                break

            self._populate_fields(modal, profile)
            self._handle_file_uploads(modal, docs, options)

            error_bubble = modal.locator("div[data-test-form-element-error]")
            if error_bubble.count() > 0:
                message = error_bubble.first.inner_text()
                return EasyApplyResult(success=False, message=f"Form error: {message}")

            if modal.locator("button:has-text('Submit')").count() > 0:
                modal.locator("button:has-text('Submit')").click()
                page.wait_for_timeout(1000)
                confirmation = page.locator("div[class*='artdeco-modal'] h2:has-text('application sent')")
                if confirmation.count() > 0:
                    message = confirmation.first.inner_text() or "Application submitted"
                    modal.locator("button:has-text('Done')").click(timeout=5000)
                    return EasyApplyResult(success=True, message=message)
                return EasyApplyResult(success=True, message="Application submitted")

            for label in ["Review", "Next", "Continue"]:
                button = modal.locator(f"button:has-text('{label}')")
                if button.count() > 0:
                    button.click()
                    page.wait_for_timeout(600)
                    step += 1
                    break
            else:
                done_button = modal.locator("button:has-text('Done')")
                if done_button.count() > 0:
                    done_button.click()
                    return EasyApplyResult(success=True, message="Application finished")
                logger.warning("Could not find navigation control", extra={"step": step})
                break

        return EasyApplyResult(success=False, message="Easy Apply wizard ended unexpectedly")

    def _populate_fields(self, container, profile: UserProfile) -> None:
        inputs = container.locator("input").element_handles()
        for element in inputs:
            field_type = element.get_attribute("type") or "text"
            if field_type in {"hidden", "checkbox", "radio", "file"}:
                continue
            label = self._label_text(element)
            value = self._resolve_field_value(label, profile)
            if value:
                element.fill(value)

        textareas = container.locator("textarea").element_handles()
        for element in textareas:
            label = self._label_text(element)
            value = self._resolve_field_value(label, profile)
            if value:
                element.fill(value[:2000])

    def _handle_file_uploads(
        self,
        container,
        docs: DocumentPaths,
        options: SubmitOptions,
    ) -> None:
        file_inputs = container.locator("input[type='file']").element_handles()
        for element in file_inputs:
            label = (self._label_text(element) or "").lower()
            upload_path = self._choose_upload_for_label(label, docs, options)
            if upload_path:
                element.set_input_files(upload_path)

    def _choose_upload_for_label(
        self,
        label: str,
        docs: DocumentPaths,
        options: SubmitOptions,
    ) -> Optional[str]:
        if not label:
            return None
        if "cover" in label:
            return options.upload_cover_letter or docs.cover_letter_path
        if "resume" in label or "cv" in label:
            return options.upload_resume or docs.resume_path
        if "attachment" in label and self.form_mapping.default_resume_path:
            return self.form_mapping.default_resume_path
        return None

    def _resolve_field_value(self, label: Optional[str], profile: UserProfile) -> Optional[str]:
        if not label:
            return None
        normalized = label.lower()
        for mapping in self.form_mapping.mappings:
            if any(keyword.lower() in normalized for keyword in mapping.keywords):
                return self._render_template(mapping.value, profile)
        return None

    def _render_template(self, template: str, profile: UserProfile) -> str:
        replacements = {
            "{{profile.fullName}}": profile.full_name,
            "{{profile.title}}": profile.title,
            "{{profile.email}}": profile.email,
            "{{profile.phone}}": profile.phone,
            "{{profile.location}}": profile.location,
            "{{profile.summary}}": profile.summary,
        }
        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)
            result = result.replace(key.lower(), value)
        return result

    def _label_text(self, element: ElementHandle) -> Optional[str]:
        aria_label = element.get_attribute("aria-label")
        if aria_label:
            return aria_label
        element_id = element.get_attribute("id")
        if element_id:
            label = element.evaluate(
                "(el, id) => {\n"
                "  const node = document.querySelector(`label[for='${id}']`);\n"
                "  return node ? node.innerText : null;\n"
                "}",
                element_id,
            )
            if label:
                return label
        placeholder = element.get_attribute("placeholder")
        return placeholder

    def _first_non_empty_text(self, page: Page, selectors: list[str]) -> str:
        for selector in selectors:
            locator = page.locator(selector)
            if locator.count() > 0:
                text = locator.first.text_content()
                if text:
                    return text
        return ""

    def _extract_description(self, page: Page) -> str:
        selectors = [
            "div.jobs-description-content__text",
            "div.jobs-box__html-content",
            "div.jobs-description__container",
        ]
        for selector in selectors:
            locator = page.locator(selector)
            if locator.count() > 0:
                content = locator.first.inner_text()
                if content:
                    return content.strip()
        fallback = page.locator("div.jobs-details__main-content").first.inner_text()
        return (fallback or "").strip()

    def _extract_job_id(self, url: str) -> Optional[str]:
        import re

        match = re.search(r"/view/([0-9]+)", url)
        if match:
            return match.group(1)
        query_match = re.search(r"[?&]currentJobId=([0-9]+)", url)
        if query_match:
            return query_match.group(1)
        return None

    def _require_page(self) -> Page:
        if not self.page:
            raise RuntimeError("LinkedIn browser is not initialised")
        return self.page


def _match_insight(insights: list[str], keyword: str) -> Optional[str]:
    for insight in insights:
        if keyword in insight.lower():
            return insight
    return None


def _current_timestamp() -> str:
    from datetime import datetime

    return datetime.utcnow().isoformat()
