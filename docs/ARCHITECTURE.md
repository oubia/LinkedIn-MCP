# LinkedIn MCP Architecture (Python)

This project implements a Python-based [Model Context Protocol](https://modelcontextprotocol.io/) server that automates the LinkedIn Easy Apply workflow.

## High-level flow

1. **Input** – an MCP client invokes the `prepare_linkedin_applications` or `submit_linkedin_applications` tool with one or more job URLs.
2. **Scraping** – `linkedin_mcp.linkedin.client.LinkedInClient` launches Playwright, signs in, and scrapes job metadata plus the full description.
3. **Content generation** – `linkedin_mcp.generation.llm.LLMGenerator` constructs a prompt (`linkedin_mcp.prompts.generation`) and calls the configured LLM provider (OpenAI, Anthropic, Azure OpenAI, or a mock) to obtain resume + cover letter JSON.
4. **Document production** – `linkedin_mcp.documents.builder.DocumentBuilder` renders the generated content into PDF files using ReportLab and writes the raw LLM output.
5. **Persistence** – metadata and artefacts are saved under `output/<job-id>/` and can be reused later.
6. **Submission (optional)** – if requested, the client re-opens the posting and drives the Easy Apply modal, uploading the PDFs and answering mapped questions.
7. **Response** – the MCP tool returns JSON with file paths, submission status, and other telemetry so the calling assistant can continue the workflow.

## Key modules

| Module | Responsibility |
|--------|----------------|
| `linkedin_mcp/config.py` | Loads environment variables, reads profile/form mapping JSON (via Pydantic models), and persists metadata. |
| `linkedin_mcp/types.py` | Dataclasses for credentials, job descriptions, generated content, and application metadata. |
| `linkedin_mcp/generation/*` | Prompt builder and LLM dispatcher with schema validation for model outputs. |
| `linkedin_mcp/documents/builder.py` | PDF creation helpers for resumes and cover letters using ReportLab. |
| `linkedin_mcp/linkedin/client.py` | Playwright automation for login, scraping, and Easy Apply wizard orchestration. |
| `linkedin_mcp/services/orchestrator.py` | Coordinates scraping, generation, document storage, metadata management, and submissions. |
| `linkedin_mcp/mcp_server.py` | Wires everything into a FastMCP server, exposing MCP tools and managing orchestrator lifecycle. |

## Dependent services

- **LLM providers** – OpenAI (`openai` package), Anthropic (`anthropic` package), Azure OpenAI (via `httpx` REST call). The mock provider returns deterministic JSON for testing.
- **Playwright** – Chromium is used for LinkedIn automation. Session storage can be cached for headless runs.
- **ReportLab** – Generates lightweight PDFs without requiring external binaries.

## Security considerations

- `.env` holds sensitive API keys and LinkedIn credentials; never commit it.
- LinkedIn session state persists at `data/linkedin.storage.json`. Delete it if security posture requires.
- Generated PDFs and raw JSON include personal data—treat the `output/` directory as confidential.
- Robust error handling in MCP tools ensures human-readable messages reach the client UI.

## Extensibility hints

- Extend `data/form_mapping.json` with additional keywords to answer bespoke application questions.
- Add new providers by implementing another branch in `LLMGenerator._dispatch`.
- Instrument additional analytics or notifications by enhancing `ApplicationOrchestrator` progress logging.
