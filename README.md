# LinkedIn MCP Server (Python)

This repository hosts a Python implementation of a [Model Context Protocol](https://modelcontextprotocol.io/) server that automates LinkedIn "Easy Apply" job submissions. Give the server one or more job posting URLs and it will:

1. Visit each posting with Playwright, capture structured job details, and store them locally.
2. Ask a configurable LLM (OpenAI, Anthropic Claude, Azure OpenAI, or a deterministic mock) to craft a tailored resume and cover letter.
3. Render the generated artefacts as PDFs and persist them under `output/<job-id>/` alongside metadata and raw model output.
4. Optionally reopen the posting, upload the documents, answer mapped form questions, and drive the Easy Apply wizard to completion.

The server exposes MCP tools so you can orchestrate the workflow from Claude Desktop, GitHub Copilot, or ChatGPT MCP integrations.

## Prerequisites

- Python 3.10+
- A LinkedIn account that can use Easy Apply
- API credentials for your preferred LLM provider
- Playwright browsers (install via `python -m playwright install`)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e .
python -m playwright install chromium
```

## Configure credentials and profile data

1. Create personal copies of the sample data:
   ```bash
   cp data/user_profile.example.json data/user_profile.json
   cp data/form_mapping.example.json data/form_mapping.json
   cp .env.example .env
   ```
2. Edit `data/user_profile.json` with your real experience. Field names use camelCase to match LinkedIn exports.
3. Update `data/form_mapping.json` with keywords/value templates that should auto-fill Easy Apply questions.
4. Populate `.env` with LinkedIn credentials, LLM provider settings, and any optional overrides.

> **Tip:** Set `PLAYWRIGHT_HEADLESS=false` and run the server once to complete MFA or captcha challenges. The authenticated state is cached in `data/linkedin.storage.json` for future headless runs.

## Running the MCP server

```bash
source .venv/bin/activate
linkedin-mcp  # or: python -m linkedin_mcp.mcp_server
```

The server listens on stdio and responds to MCP clients that connect to it. Logs stream to stdout by default. Set `LOG_LEVEL=DEBUG` for verbose diagnostics.

## Available MCP tools

| Tool | Description |
|------|-------------|
| `prepare_linkedin_applications` | Input: `{ "job_urls": string[], "regenerate"?: boolean }`. Scrapes each job, generates PDFs, and returns file paths. |
| `submit_linkedin_applications` | Input: `{ "job_urls"?: string[], "job_ids"?: string[], "skip_when_already_applied"?: boolean }`. Uses existing artefacts or regenerates before submitting Easy Apply. |
| `list_prepared_applications` | Lists metadata for all prepared applications on disk. |

Each tool response is JSON so MCP clients can display progress, review documents, or trigger subsequent actions.

## Project structure

```
linkedin_mcp/
  config.py            # Environment + JSON config loading
  documents/           # PDF generation utilities (ReportLab)
  generation/          # Prompt building and LLM integrations
  linkedin/            # Playwright automation for scraping & Easy Apply
  services/orchestrator.py  # High-level workflow coordinator
  mcp_server.py        # FastMCP server wiring and tool definitions
```

Generated files live under `output/<job-id>/`:
- `resume-*.pdf`
- `cover-letter-*.pdf`
- `generation-*.json`
- `metadata.json`

## Notes & cautions

- Automating LinkedIn may violate their terms of service. Proceed at your own risk.
- Generated PDFs and metadata contain personal information; protect the `output/` directory.
- Easy Apply steps sometimes include company-specific questions. Extend `data/form_mapping.json` with additional keywords to prefill common answers.
- For dry runs, set `GENERATION_PROVIDER=mock` in `.env` to skip external API calls.

## Troubleshooting

- Set `PLAYWRIGHT_SLOWMO=250` and `PLAYWRIGHT_HEADLESS=false` to inspect the Easy Apply flow interactively.
- Delete `data/linkedin.storage.json` if LinkedIn rejects the cached session.
- Use `LOG_LEVEL=DEBUG` for detailed scraping and form-filling traces.
