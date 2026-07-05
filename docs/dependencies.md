# Dependencies

## System requirements

| Requirement | Version / notes |
|-------------|-----------------|
| **Python** | 3.11+ |
| **OS** | Windows, macOS, or Linux (tested on Windows with corporate proxy) |
| **Network** | HTTPS access to `api.github.com` and Google Generative Language API |

## Python packages

Defined in [`pyproject.toml`](../pyproject.toml). Install with `pip install -e .`.

| Package | Role |
|---------|------|
| `streamlit` | Web UI |
| `langchain` / `langchain-core` | LLM orchestration, tools, messages |
| `langchain-google-genai` | Gemini chat model + structured output |
| `httpx` | GitHub REST API client |
| `certifi` | CA bundle helper (fallback; Windows often uses OS trust store) |
| `pydantic` | Schemas for search plans, recommendations, overview |
| `python-dotenv` | Load `.env` configuration |

Optional dev dependency: `ruff` (linting).

## External APIs & keys

| Service | Required? | Purpose |
|---------|-----------|---------|
| **Google AI Studio (Gemini)** | Yes | Search planning, ranking, overview, Q&A |
| **GitHub REST API** | Yes (anonymous OK) | Repo search, README, file contents |
| **GitHub personal access token** | Recommended | Higher rate limits for search and file reads |

## Environment variables

See [How to run](how-to-run.md#configuration). Summary:

- `GOOGLE_API_KEY` — required
- `GITHUB_TOKEN` — optional but recommended
- `GEMINI_MODEL` — optional (default `gemini-2.0-flash`)
- `SSL_USE_SYSTEM_STORE` — optional on Windows behind SSL-inspecting proxies

## Files not committed to Git

These stay local (see [`.gitignore`](../.gitignore)):

- `.env` — secrets
- `.venv/` — virtual environment
