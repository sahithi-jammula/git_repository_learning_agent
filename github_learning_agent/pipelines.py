from __future__ import annotations

import json
import uuid
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from github_learning_agent.config import gemini_model, google_api_key
from github_learning_agent.github_service import GitHubService
from github_learning_agent.schemas import RepoOverview, RepoRecommendation, RepoRecommendations, SearchPlan
from github_learning_agent.ssl_setup import ssl_verify_context


def _chat() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=gemini_model(),
        google_api_key=google_api_key(),
        temperature=0.2,
        client_args={"verify": ssl_verify_context()},
    )


def plan_searches(learning_goal: str) -> SearchPlan:
    llm = _chat().with_structured_output(SearchPlan)
    prompt = (
        "You help learners find GitHub repositories. Given a learning goal, output a search plan.\n"
        "Rules:\n"
        "- Produce 2–5 GitHub `q` strings for the REST repository search endpoint.\n"
        "- Prefer queries that surface tutorials, examples, official orgs, and hands-on repos.\n"
        "- Include at least one query with a topic filter when relevant (e.g. topic:langgraph).\n"
        "- Avoid overly narrow queries that return <3 results unless necessary.\n\n"
        f"Learning goal:\n{learning_goal.strip()}"
    )
    return llm.invoke(prompt)


def collect_candidates(gh: GitHubService, queries: list[str], cap_per_query: int = 15) -> list[dict[str, Any]]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for q in queries:
        try:
            items = gh.search_repositories(q, per_page=cap_per_query)
        except Exception:
            continue
        for it in items:
            fn = it.get("full_name")
            if not fn or fn in seen:
                continue
            seen.add(fn)
            merged.append(it)
    return merged


def _compact_repo(it: dict[str, Any]) -> dict[str, Any]:
    return {
        "full_name": it.get("full_name"),
        "html_url": it.get("html_url"),
        "description": it.get("description"),
        "stargazers_count": it.get("stargazers_count"),
        "language": it.get("language"),
        "updated_at": it.get("updated_at"),
        "topics": it.get("topics") or [],
        "default_branch": it.get("default_branch"),
    }


def _fallback_recommendations(candidates: list[dict[str, Any]]) -> RepoRecommendations:
    top = sorted(
        candidates,
        key=lambda c: int(c.get("stargazers_count") or 0),
        reverse=True,
    )[:3]
    return RepoRecommendations(
        recommendations=[
            RepoRecommendation(
                full_name=it.get("full_name") or "",
                why="High stars among search results; verify docs fit your goal.",
                caveats="Heuristic fallback: model did not return 3 valid picks.",
                best_for="Quick start; skim README before committing time.",
            )
            for it in top
        ]
    )


def rank_top_three(learning_goal: str, goal_restated: str, candidates: list[dict[str, Any]]) -> RepoRecommendations:
    if not candidates:
        raise ValueError(
            "No repository candidates found. Try a broader learning goal or check GitHub API limits."
        )
    llm = _chat().with_structured_output(RepoRecommendations)
    payload = [_compact_repo(c) for c in candidates[:40]]
    prompt = (
        "You are a technical mentor choosing GitHub repositories for learning.\n"
        "Pick EXACTLY 3 repositories from the candidate JSON list.\n"
        "Rules:\n"
        "- Only use repos that appear in the candidate list (use exact full_name).\n"
        "- Prefer diversity when possible: official/tutorial, examples/cookbook, and a smaller real-world style repo.\n"
        "- Use stars, updated_at, description, topics as signals; call out staleness in caveats.\n"
        "- Be honest: if a repo is advanced, say so.\n\n"
        f"Learning goal (raw): {learning_goal}\n"
        f"Learning goal (restated): {goal_restated}\n\n"
        f"Candidates (JSON):\n{json.dumps(payload, indent=2)}"
    )
    result: RepoRecommendations = llm.invoke(prompt)
    valid = {c.get("full_name") for c in candidates if c.get("full_name")}
    filtered = [r for r in result.recommendations if r.full_name in valid]
    if len(filtered) >= 3:
        return RepoRecommendations(recommendations=filtered[:3])
    # Fill from remaining valid model picks, then star order
    used = {r.full_name for r in filtered}
    for c in sorted(candidates, key=lambda x: int(x.get("stargazers_count") or 0), reverse=True):
        fn = c.get("full_name")
        if not fn or fn in used:
            continue
        filtered.append(
            RepoRecommendation(
                full_name=fn,
                why="Added to reach 3 picks based on popularity among candidates.",
                caveats="Less tailored than primary recommendations.",
                best_for="Explore README to confirm fit.",
            )
        )
        used.add(fn)
        if len(filtered) >= 3:
            break
    if len(filtered) < 3:
        return _fallback_recommendations(candidates)
    return RepoRecommendations(recommendations=filtered[:3])


def build_overview_context(gh: GitHubService, full_name: str) -> str:
    owner, repo = full_name.split("/", 1)
    readme = gh.get_readme_text(owner, repo) or "[No README found]"
    root = gh.list_root_contents(owner, repo)
    root_names = [x.get("name") for x in root if x.get("name")]
    manifests = (
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        "Gemfile",
    )
    manifest_snippets: list[str] = []
    for name in root_names:
        if name in manifests:
            text = gh.get_file_text(owner, repo, name, max_chars=20_000)
            manifest_snippets.append(f"--- {name} ---\n{text}")

    return (
        f"Repository: {full_name}\n\n"
        f"README:\n{readme[:25_000]}\n\n"
        f"Root entries: {', '.join(str(n) for n in root_names)}\n\n"
        + ("\n".join(manifest_snippets) if manifest_snippets else "[No common manifest files at repo root]")
    )


def generate_overview(learning_goal: str, full_name: str, context: str) -> RepoOverview:
    llm = _chat().with_structured_output(RepoOverview)
    prompt = (
        "You summarize a GitHub repository for a learner.\n"
        "Use ONLY the provided context (README, root listing, manifest snippets). "
        "If something is unknown, say so.\n"
        f"Learning goal: {learning_goal}\n"
        f"Repository: {full_name}\n\n"
        f"Context:\n{context}"
    )
    return llm.invoke(prompt)


def overview_to_markdown(full_name: str, html_url: str | None, ov: RepoOverview) -> str:
    if ov.important_files:
        files_md = "\n".join(f"| `{f.path}` | {f.why} |" for f in ov.important_files)
    else:
        files_md = "| _None identified from context_ | _Use Q&A to inspect files._ |"
    concepts = "\n".join(f"- {c}" for c in ov.key_concepts)
    path = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(ov.learning_path))
    link = html_url or f"https://github.com/{full_name}"
    return (
        f"## Repository overview: [{full_name}]({link})\n\n"
        f"### Purpose\n{ov.purpose}\n\n"
        f"### Tech stack\n{ov.tech_stack}\n\n"
        f"### Key concepts\n{concepts}\n\n"
        f"### Important files\n| Path | Why it matters |\n|------|----------------|\n{files_md}\n\n"
        f"### Learning path\n{path}\n"
    )


class ReadFileArgs(BaseModel):
    path: str = Field(description="Repo-relative file path, e.g. README.md or src/app.py")


def make_read_file_tool(gh: GitHubService, owner: str, repo: str) -> StructuredTool:
    def _read(path: str) -> str:
        path = path.lstrip("/")
        return gh.get_file_text(owner, repo, path)

    return StructuredTool.from_function(
        name="read_github_file",
        description=(
            f"Read a text file from {owner}/{repo}. "
            "Use repo-relative paths. Call this before claiming line-level or file-specific facts."
        ),
        func=_read,
        args_schema=ReadFileArgs,
    )


def run_tool_loop(
    messages: list[BaseMessage],
    tool: StructuredTool,
    max_steps: int = 8,
) -> tuple[AIMessage, list[BaseMessage]]:
    llm = _chat().bind_tools([tool])
    ms: list[BaseMessage] = list(messages)
    last_ai = AIMessage(content="")
    for _ in range(max_steps):
        last_ai = llm.invoke(ms)
        ms.append(last_ai)
        tcs = getattr(last_ai, "tool_calls", None) or []
        if not tcs:
            break
        for tc in tcs:
            name = tc.get("name")
            tid = tc.get("id") or str(uuid.uuid4())
            args = tc.get("args") or {}
            if name != tool.name:
                ms.append(ToolMessage(content=f"Unknown tool {name}", tool_call_id=tid))
                continue
            path = (args.get("path") or "").strip()
            try:
                out = tool.invoke({"path": path})
            except Exception as e:
                out = f"[Error reading {path}: {e}]"
            ms.append(ToolMessage(content=str(out), tool_call_id=tid))
    return last_ai, ms


def qa_turn(
    learning_goal: str,
    full_name: str,
    overview_markdown: str,
    history: list[BaseMessage],
    user_message: str,
    gh: GitHubService,
) -> tuple[str, list[BaseMessage]]:
    owner, repo = full_name.split("/", 1)
    read_tool = make_read_file_tool(gh, owner, repo)
    system = SystemMessage(
        content=(
            "You are a patient mentor helping the user learn from a GitHub repository.\n"
            "Rules:\n"
            "- Use the read_github_file tool whenever the user asks about code, files, or behavior.\n"
            "- Never invent file contents or paths; read first, then explain.\n"
            "- Keep answers clear and structured. Reference paths in backticks.\n\n"
            f"Learning goal: {learning_goal}\n"
            f"Selected repository: {full_name}\n\n"
            f"Repository overview (may be incomplete):\n{overview_markdown}"
        )
    )
    ms: list[BaseMessage] = [system, *history, HumanMessage(content=user_message)]
    ai, ms_out = run_tool_loop(ms, read_tool)
    text = ai.content or ""
    if isinstance(text, list):
        text = "".join(str(part) for part in text)
    # Persist everything after the system prompt for the next turn.
    return str(text), ms_out[1:]
