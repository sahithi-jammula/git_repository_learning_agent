# Hurdles & solutions

Problems encountered while building and running GitHub Learning Agent, and how we addressed them.

---

## SSL certificate errors (corporate proxy)

**Symptom**

```
Discovery failed: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
unable to get local issuer certificate
```

**Cause**

- Many corporate networks use an **SSL-inspecting proxy**
- The proxy’s root CA is in the **Windows certificate store**, not in Python’s **certifi** bundle
- Setting `SSL_CERT_FILE` to certifi’s `cacert.pem` made things **worse** — it forced clients to ignore the OS store

**Fix**

1. Set `SSL_USE_SYSTEM_STORE=1` in `.env`
2. **Remove** `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE` if they point at certifi
3. App uses `ssl.create_default_context()` and passes it to **httpx** (GitHub) and **Gemini** (`client_args`)
4. Restart Streamlit after changing `.env`

**Lesson:** On Windows behind a proxy, prefer the **OS trust store**, not certifi alone.

---

## Gemini API quota (429)

**Symptom**

```
429 RESOURCE_EXHAUSTED ... quota exceeded ... gemini-2.0-flash
```

**Cause**

Free-tier limits per model / per minute / per day.

**Mitigations**

- Wait and retry
- Try another model in `.env`: `GEMINI_MODEL=gemini-2.5-flash`
- Confirm the API key is valid in [Google AI Studio](https://aistudio.google.com/apikey)
- Check usage: [AI dev rate limits](https://ai.dev/rate-limit)

**Lesson:** A 429 after fixing SSL means **connectivity works** — the blocker is quota, not TLS.

---

## `streamlit` command not found

**Symptom**

```
streamlit : The term 'streamlit' is not recognized
```

**Cause**

Virtual environment not activated; Streamlit is installed inside `.venv`, not globally.

**Fix**

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run github_learning_agent\streamlit_app.py
```

Or:

```powershell
.\.venv\Scripts\python.exe -m streamlit run github_learning_agent\streamlit_app.py
```

---

## Git push failures

**Symptom**

- `remote origin already exists`
- `Repository not found` when pushing to `YOUR-NEW-REPO-NAME.git`

**Cause**

Placeholder remote URL was added first; real repo URL not set.

**Fix**

```powershell
git remote set-url origin https://github.com/sahithi-jammula/github_repository_learning_agent.git
git push -u origin main
```

Ensure the GitHub repo exists (empty, no README) before pushing.

---

## Accidentally pushing unwanted files

**Symptom**

`.env`, `.venv`, or other local-only files ended up in git history or staging.

**Fix**

- Use [`.gitignore`](../.gitignore) — excludes `.env`, `.venv`, and local editor folders
- Remove from tracking without deleting locally:

  ```powershell
  git rm -r --cached path/to/unwanted/folder
  ```

- Fresh start: delete `.git`, `git init`, commit only intended files

**Lesson:** Always run `git status` before `git commit`.

---

## UI looked identical to another Streamlit app

**Symptom**

Default Streamlit layout (title, sidebar, chat) felt the same as a RAG assistant.

**Fix**

- Custom light theme in `.streamlit/config.toml`
- Custom CSS (hero, workflow steps, colorful repo cards, animated buttons)
- Logo in `github_learning_agent/assets/logo.png`
- Chat UI only in the final Q&A phase

---

## Search quality limitations

**Symptom**

Recommendations sometimes miss the “best” repo or include stale forks.

**Cause**

GitHub search is keyword-driven; ranking uses heuristics (stars, recency, description) plus LLM judgment.

**Mitigations (MVP)**

- Gemini plans multiple diverse queries
- Rubric asks for tutorial / examples / practical diversity
- Caveats surfaced explicitly in the UI

**Future:** See [Roadmap](roadmap.md) for scoring CLI and local indexing.
