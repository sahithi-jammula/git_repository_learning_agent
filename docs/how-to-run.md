# How to run

## 1. Clone and open the project

```powershell
git clone https://github.com/sahithi-jammula/github_repository_learning_agent.git
cd github_repository_learning_agent
```

(Use your actual repo URL if different.)

## 2. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 3. Install dependencies

```powershell
pip install -e .
```

## 4. Configure environment

```powershell
copy .env.example .env
```

Edit `.env`:

```env
GOOGLE_API_KEY=your_key_from_aistudio
GITHUB_TOKEN=your_github_pat_optional
GEMINI_MODEL=gemini-2.0-flash

# Windows + corporate proxy (recommended)
SSL_USE_SYSTEM_STORE=1
```

Get a Gemini key: [Google AI Studio](https://aistudio.google.com/apikey)

## 5. Start the app

**With venv activated:**

```powershell
streamlit run github_learning_agent\streamlit_app.py
```

**Without activating venv:**

```powershell
.\.venv\Scripts\python.exe -m streamlit run github_learning_agent\streamlit_app.py
```

Open the URL shown (usually `http://localhost:8501`).

## 6. Use the UI

1. Enter a **learning goal**
2. Click **Search GitHub & rank top 3**
3. Pick a repo card → **Build learning overview**
4. Ask questions in **Ask about the code**

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini API key (or `GEMINI_API_KEY`) |
| `GITHUB_TOKEN` | No | GitHub PAT for better rate limits |
| `GEMINI_MODEL` | No | Default `gemini-2.0-flash` |
| `SSL_USE_SYSTEM_STORE` | No | Set `1` on Windows if TLS fails behind corporate proxy |

## Troubleshooting

| Symptom | See |
|---------|-----|
| `streamlit` not recognized | Activate `.venv` or use `python -m streamlit` |
| `CERTIFICATE_VERIFY_FAILED` | [Hurdles — SSL](hurdles-and-solutions.md#ssl-certificate-errors-corporate-proxy) |
| `429 RESOURCE_EXHAUSTED` | [Hurdles — Gemini quota](hurdles-and-solutions.md#gemini-api-quota-429) |
| `Repository not found` on `git push` | Fix remote URL; create empty repo on GitHub first |
