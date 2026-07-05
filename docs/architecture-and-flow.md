# Architecture, flow & agents

This document explains **how the app works end-to-end**, **why each framework was chosen**, and **how the LLM “agents” behave** at each step.

---

## High-level picture

```mermaid
flowchart TB
  subgraph ui [Streamlit UI]
    goal[Learning goal input]
    discover[Search GitHub and rank top 3]
    pick[Select repo card]
    overview[Build learning overview]
    qa[Ask about the code]
  end

  subgraph llm [LangChain + Gemini]
    plan[Goal Analyzer — SearchPlan]
    rank[Repository Evaluator — RepoRecommendations]
    summarize[Repository Analyzer — RepoOverview]
    mentor[Q&A Agent — tool loop]
  end

  subgraph github [GitHub REST API]
    search[/search/repositories]
    readme[/repos/.../readme]
    contents[/repos/.../contents/...]
  end

  goal --> discover
  discover --> plan
  plan --> search
  search --> rank
  rank --> pick
  pick --> overview
  overview --> readme
  overview --> contents
  readme --> summarize
  contents --> summarize
  summarize --> qa
  qa --> mentor
  mentor --> contents
```

The app is **not** a single long-running autonomous agent. It is a **pipeline of focused LLM steps** (plus one tool-using loop for Q&A), orchestrated by Python in `github_learning_agent/pipelines.py` and triggered from the Streamlit UI.

---

## Step-by-step flow

### Step 1 — Goal (UI only)

**What happens**

- User enters a natural-language learning goal, e.g. *“I want to learn LangGraph”*.
- Stored in Streamlit session state (`learning_goal`).

**Why no LLM yet**

- Keeps the first interaction instant and avoids an API call before the user commits to a search.

---

### Step 2 — Discover (Goal Analyzer + GitHub Search)

**Trigger:** User clicks **Search GitHub & rank top 3**.

#### 2a. Goal Analyzer (`plan_searches`)

| | |
|---|---|
| **Code** | `pipelines.plan_searches()` |
| **Input** | Raw learning goal string |
| **Output** | `SearchPlan` (Pydantic) |
| **LLM** | Gemini via `ChatGoogleGenerativeAI.with_structured_output(SearchPlan)` |

The model returns:

- `goal_restated` — one-sentence interpretation of the goal
- `keywords` — topic terms for later ranking context
- `queries` — 2–5 GitHub search strings (`q` syntax), e.g. `langgraph topic:langgraph`, `langchain-ai langgraph examples`

**Design intent:** GitHub search is keyword-driven. A single naive query often misses tutorials, official repos, or example repos. The LLM acts as a **search strategist**, not a code reader.

#### 2b. Repository Searcher (`collect_candidates`)

| | |
|---|---|
| **Code** | `pipelines.collect_candidates()` + `GitHubService.search_repositories()` |
| **Input** | List of query strings from `SearchPlan` |
| **Output** | Merged, de-duplicated list of repo metadata dicts |
| **LLM** | None — deterministic HTTP calls |

For each query:

1. `GET https://api.github.com/search/repositories?q=...&sort=stars`
2. Up to 15 results per query
3. De-duplicate by `full_name`

Failed queries are skipped (network/rate limit) so one bad query does not block the whole run.

#### 2c. Repository Evaluator (`rank_top_three`)

| | |
|---|---|
| **Code** | `pipelines.rank_top_three()` |
| **Input** | Learning goal, restated goal, up to 40 compact candidates |
| **Output** | `RepoRecommendations` — **exactly 3** `RepoRecommendation` objects |
| **LLM** | Gemini with structured output |

Each recommendation includes:

- `full_name` — must exist in the candidate list (anti-hallucination)
- `why` — fit for the learning goal
- `caveats` — staleness, difficulty, scope mismatch
- `best_for` — audience / use case

**Safety nets (no LLM):**

- Filter picks to repos that actually appeared in search results
- If fewer than 3 valid picks, fill from star-sorted candidates
- If still short, `_fallback_recommendations()` uses top stars only

**Design intent:** Stars and recency alone are poor teachers. The LLM applies a **mentor rubric** (diversity: official / examples / practical) while staying tied to real search results.

---

### Step 3 — Select (UI only)

**What happens**

- UI shows three repo cards.
- User picks one and clicks **Build learning overview**.
- Selected `full_name` is stored in session state.

**Why no LLM**

- Human choice avoids the system assuming the “best” repo for the user’s level and intent.

---

### Step 4 — Overview (Repository Analyzer)

**Trigger:** **Build learning overview**.

#### 4a. Context gathering (`build_overview_context`)

| | |
|---|---|
| **Code** | `pipelines.build_overview_context()` + `GitHubService` |
| **Input** | `owner/repo` |
| **Output** | Single text bundle for the LLM |
| **LLM** | None |

Fetched from GitHub:

1. **README** (raw text, truncated ~25k chars)
2. **Root directory listing** (file/folder names)
3. **Manifest snippets** if present at root: `package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`, `Cargo.toml`, `pom.xml`, `Gemfile` (up to ~20k chars each)

**Design intent:** Breadth-first snapshot — enough to explain purpose, stack, and entry points without cloning the whole repo.

#### 4b. Summarization (`generate_overview`)

| | |
|---|---|
| **Code** | `pipelines.generate_overview()` |
| **Input** | Learning goal, repo name, context bundle |
| **Output** | `RepoOverview` (structured) → markdown via `overview_to_markdown()` |
| **LLM** | Gemini with structured output |

`RepoOverview` fields:

- `purpose`, `tech_stack`, `key_concepts`
- `important_files` (path + why)
- `learning_path` (ordered steps)

Prompt rule: **use only provided context**; say unknown if not inferable.

---

### Step 5 — Q&A (Q&A Agent with tools)

**Trigger:** User message in chat after overview exists.

| | |
|---|---|
| **Code** | `pipelines.qa_turn()` → `run_tool_loop()` |
| **Input** | Learning goal, overview markdown, chat history, user question |
| **Output** | Assistant reply + updated message history |
| **LLM** | Gemini with `read_github_file` tool bound |

#### How the Q&A agent works

1. **System prompt** sets mentor behavior: read files before claiming code facts; cite paths in backticks.
2. **Tool:** `read_github_file(path)` → `GitHubService.get_file_text(owner, repo, path)`.
3. **Tool loop** (`run_tool_loop`, max 8 steps):
   - Gemini responds (may include `tool_calls`)
   - For each call, execute `read_github_file`, append `ToolMessage` with file content
   - Repeat until Gemini returns a final answer with no more tool calls
4. **History** persisted in session (everything after the system message) for multi-turn Q&A.

**Design intent:** Overview is shallow; Q&A is **depth on demand**. The model cannot invent file contents — it must call the tool first (same pattern as RAG, but retrieval is **targeted per question** via the LLM choosing paths).

---

## Why these frameworks?

| Choice | Role in this project | Why it was chosen |
|--------|----------------------|-------------------|
| **Streamlit** | Web UI, session state, chat widget | Fast to build a local demo; no separate frontend/backend; good for MVP and data/ML-style apps |
| **LangChain** | LLM calls, structured output, tools, message types | Unified API for chat models, `with_structured_output()`, `bind_tools()`, and `ToolMessage` / `AIMessage` loops without custom protocol code |
| **langchain-google-genai** | Gemini integration | Native Gemini support in LangChain; structured output maps cleanly to Pydantic schemas |
| **Gemini** | All reasoning steps | Strong instruction-following, JSON/structured output, tool calling; single API key from Google AI Studio |
| **Pydantic** | `SearchPlan`, `RepoRecommendations`, `RepoOverview` | Validates LLM outputs; fixes shape of data before UI renders; documents fields explicitly |
| **httpx** | GitHub REST client | Simple sync HTTP; explicit TLS/`verify` control (needed for corporate proxies on Windows) |
| **python-dotenv** | Config from `.env` | Keeps API keys out of code; standard local dev pattern |

### What we deliberately did **not** use (MVP)

| Omitted | Reason |
|---------|--------|
| **LangGraph** | Pipeline is linear + one tool loop; a graph framework adds complexity without clear benefit at MVP size |
| **Vector DB / embeddings** | No bulk indexing; file reads are on-demand via GitHub API |
| **GitHub MCP** | Direct REST works everywhere; no Cursor/MCP dependency for end users |
| **Custom FastAPI/React** | Streamlit is enough for a learning tool run locally |

---

## “Agents” in this project

In marketing terms the steps are “agents”; in code they are **phases** with different prompts and capabilities:

| Phase | Agent name | Autonomy | Tools | Structured output |
|-------|------------|----------|-------|-------------------|
| 2a | Goal Analyzer | Single LLM call | None | `SearchPlan` |
| 2b | Repository Searcher | Deterministic | None | N/A |
| 2c | Repository Evaluator | Single LLM call | None | `RepoRecommendations` |
| 4a | Context fetcher | Deterministic | None | N/A |
| 4b | Repository Analyzer | Single LLM call | None | `RepoOverview` |
| 5 | Q&A Agent | Multi-step loop | `read_github_file` | Free text reply |

Only **Step 5** is a classic **agentic loop** (model decides which files to read, then answers). Earlier steps are **single-shot LLM calls** with strict schemas — cheaper, more predictable, easier to debug.

```text
User goal
    → [LLM] search plan
    → [GitHub] candidates
    → [LLM] pick 3
    → user selects 1
    → [GitHub] README + manifests
    → [LLM] overview
    → [LLM + tool loop] Q&A with file reads
```

---

## Key files map

| File | Responsibility |
|------|----------------|
| `streamlit_app.py` | UI, session state, calls into pipelines |
| `pipelines.py` | All LLM steps and Q&A tool loop |
| `github_service.py` | GitHub REST: search, README, contents |
| `schemas.py` | Pydantic models for structured LLM outputs |
| `config.py` | API keys, model name, env loading |
| `ssl_setup.py` | TLS context for corporate Windows networks |

---

## Data and trust boundaries

| Data source | Used for | Trust rule |
|-------------|----------|------------|
| GitHub search metadata | Ranking | Only repos from search results can be recommended |
| README / manifests | Overview | Model told to use only provided context |
| Arbitrary file paths | Q&A | Model must call `read_github_file` before file-specific claims |
| User’s learning goal | All LLM steps | Passed as context in every prompt |

---

## Limits (by design)

- **Public repos** work best; private repos need `GITHUB_TOKEN` with access.
- **Large files** truncated at read time.
- **No clone** — very large repos may be hard to explore via API alone.
- **Heuristic search** — not guaranteed “best” repos; caveats are surfaced in UI.

---

See also: [Purpose](purpose.md) · [Dependencies](dependencies.md) · [How to run](how-to-run.md) · [Roadmap](roadmap.md)
