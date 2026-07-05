# GitHub Learning Agent

Learn a technology from **real GitHub repositories**: discover three ranked repos with Gemini, get a structured overview of the one you pick, then ask **file-grounded questions** about its code (LangChain + Gemini + GitHub REST).

📚 **Documentation:** [`docs/`](docs/README.md) — purpose, dependencies, how to run, hurdles, roadmap.

## Project goal

Help learners go from *“I want to learn X”* to *“I understand this repo”* in four steps:

1. **Goal** — You describe what you want to learn.
2. **Discover** — Gemini plans GitHub searches; the app merges results and ranks **exactly three** repos (why / caveats / best for).
3. **Overview** — You pick one repo; the app reads README, root tree, and manifests and summarizes it.
4. **Q&A** — You ask questions; Gemini reads files from the repo before answering.

---

## Quick start

### Prerequisites

- Python **3.11+**
- [Google AI Studio](https://aistudio.google.com/apikey) API key
- Optional: GitHub personal access token (higher API rate limits)

### Setup

```powershell
cd c:\github-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
copy .env.example .env
# Edit .env: GOOGLE_API_KEY=... and optionally GITHUB_TOKEN=...
```

### Run

```powershell
.\.venv\Scripts\python.exe -m streamlit run github_learning_agent\streamlit_app.py
```

See [docs/how-to-run.md](docs/how-to-run.md) for full setup and troubleshooting.

### Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini API key (or `GEMINI_API_KEY`) |
| `GITHUB_TOKEN` | No | GitHub PAT for REST search/contents |
| `GEMINI_MODEL` | No | Default `gemini-2.0-flash` |
| `SSL_USE_SYSTEM_STORE` | No | Set `1` on Windows if TLS fails behind a corporate proxy |

---

## Limitations

- Search and ranking are **heuristic** — no guarantee of “best” repos.
- **Public repos** work best; private repos need a token with access.
- Large files are **truncated** when read via the API.

---

## Repository layout

```text
docs/                      # Project documentation
github_learning_agent/     # App (LangChain + Gemini + Streamlit)
  assets/logo.png
  streamlit_app.py
  pipelines.py
  github_service.py
  ...
.streamlit/config.toml
pyproject.toml
.env.example
```

## License

Add a license file if you intend to distribute this repository.
