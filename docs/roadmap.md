# Roadmap

## MVP (done)

- [x] Learning goal → Gemini search plan → GitHub REST search
- [x] Rank **exactly 3** repositories (why / caveats / best for)
- [x] User selects repo → structured overview (README, manifests, root tree)
- [x] File-grounded Q&A via `read_github_file` tool
- [x] Streamlit UI with custom theme and workflow steps
- [x] SSL handling for Windows / corporate proxies
- [x] Project documentation (`docs/`)

## Near term

| Item | Description |
|------|-------------|
| **Raise cap to 5 repos** | One-line config change once ranking stabilizes |
| **Better error messages** | Distinguish SSL vs quota vs GitHub rate limit in the UI |
| **Model selector in UI** | Pick Gemini model without editing `.env` |
| **Persist sessions** | Save last goal / selected repo locally |
| **License file** | Add `LICENSE` if distributing publicly |

## Phase 2 (from original plan)

| Item | Description |
|------|-------------|
| **CLI** | `gh` + REST for search/ranking outside Streamlit |
| **Shallow clone** | Local indexer for larger repos |
| **Automated scoring** | Formula for stars/recency; LLM only for prose |
| **Tests** | CI guardrails on schemas and GitHub client mocks |
| **Offline mode** | Clone repo into workspace; Q&A with local tools only |

## Out of scope (for now)

- Multi-user hosting or auth
- Guaranteed “best repo” oracle
- Full architecture analysis without file reads
- Private repo support without user token + access

## Success criteria (recap)

A user with `GOOGLE_API_KEY` (+ optional `GITHUB_TOKEN`) can:

1. Enter a learning goal
2. Get 3 ranked repos with reasons
3. Pick one and see an overview
4. Ask questions answered from real files

---

See also: [Purpose](purpose.md) · [How to run](how-to-run.md) · [Hurdles](hurdles-and-solutions.md)
