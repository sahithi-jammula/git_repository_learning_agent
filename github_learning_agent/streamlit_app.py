from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import streamlit as st
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from github_learning_agent import pipelines
from github_learning_agent.config import gemini_model, github_token, google_api_key
from github_learning_agent.github_service import GitHubService
from github_learning_agent.schemas import RepoRecommendations, SearchPlan

PHASES = ("Goal", "Discover", "Select", "Overview", "Q&A")
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo.png"
CARD_ACCENTS = (
    ("#FF6B6B", "#FF8E53", "#FFF1F0"),
    ("#7C3AED", "#A855F7", "#F5F3FF"),
    ("#14B8A6", "#06B6D4", "#F0FDFA"),
)


def _inject_styles() -> None:
    st.markdown(
        """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

  html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
  }

  #MainMenu, footer, header { visibility: hidden; }
  .block-container {
    padding-top: 1rem;
    max-width: 1140px;
    background: linear-gradient(180deg, #F8FAFF 0%, #FFF7ED 45%, #F0FDFA 100%);
  }

  .stApp {
    background: linear-gradient(160deg, #EEF2FF 0%, #FFF7ED 40%, #ECFDF5 100%);
  }

  /* Animated primary buttons */
  @keyframes shimmer {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
  @keyframes floaty {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-2px); }
  }
  @keyframes pulse-ring {
    0% { box-shadow: 0 0 0 0 rgba(124, 58, 237, 0.45); }
    70% { box-shadow: 0 0 0 10px rgba(124, 58, 237, 0); }
    100% { box-shadow: 0 0 0 0 rgba(124, 58, 237, 0); }
  }

  div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(120deg, #7C3AED, #EC4899, #F97316, #7C3AED) !important;
    background-size: 300% 300% !important;
    animation: shimmer 4s ease infinite, floaty 2.4s ease-in-out infinite;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 14px !important;
    padding: 0.62rem 1.25rem !important;
    box-shadow: 0 10px 25px rgba(124, 58, 237, 0.35) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
  }
  div[data-testid="stButton"] > button[kind="primary"]:hover {
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 0 14px 30px rgba(236, 72, 153, 0.45) !important;
  }
  div[data-testid="stButton"] > button[kind="secondary"] {
    background: white !important;
    color: #7C3AED !important;
    border: 2px solid #E9D5FF !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
  }
  div[data-testid="stButton"] > button[kind="secondary"]:hover {
    border-color: #7C3AED !important;
    background: #FAF5FF !important;
    transform: translateY(-2px) !important;
  }

  .gha-hero {
    background: linear-gradient(135deg, #FFFFFF 0%, #FDF4FF 50%, #FFF7ED 100%);
    border: 1px solid #E9D5FF;
    border-radius: 24px;
    padding: 1.35rem 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 20px 50px rgba(124, 58, 237, 0.08);
    position: relative;
    overflow: hidden;
  }
  .gha-hero::before {
    content: "";
    position: absolute;
    top: -40px; right: -40px;
    width: 140px; height: 140px;
    background: radial-gradient(circle, #FDE68A88, transparent 70%);
    pointer-events: none;
  }
  .gha-hero h1 {
    font-size: 2rem;
    font-weight: 800;
    margin: 0 0 0.4rem 0;
    letter-spacing: -0.03em;
    background: linear-gradient(90deg, #7C3AED, #EC4899, #F97316);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .gha-hero p { color: #64748B; margin: 0; font-size: 0.98rem; line-height: 1.5; }
  .gha-badge {
    display: inline-block;
    border-radius: 999px;
    padding: 0.2rem 0.7rem;
    font-size: 0.72rem;
    font-weight: 700;
    margin-right: 0.35rem;
    margin-bottom: 0.45rem;
  }
  .gha-badge-1 { background: #EDE9FE; color: #6D28D9; border: 1px solid #DDD6FE; }
  .gha-badge-2 { background: #FFE4E6; color: #E11D48; border: 1px solid #FECDD3; }
  .gha-badge-3 { background: #CCFBF1; color: #0F766E; border: 1px solid #99F6E4; }
  .gha-steps { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 1rem; }
  .gha-step {
    flex: 1; min-width: 76px; text-align: center;
    padding: 0.5rem 0.4rem; border-radius: 12px;
    font-size: 0.72rem; font-weight: 700;
    color: #94A3B8; background: #F8FAFC; border: 1px solid #E2E8F0;
    transition: all 0.25s ease;
  }
  .gha-step.active {
    color: #7C3AED; border-color: #C4B5FD;
    background: linear-gradient(180deg, #FAF5FF, #FFFFFF);
    box-shadow: 0 4px 14px rgba(124, 58, 237, 0.15);
    transform: translateY(-2px);
  }
  .gha-step.done { color: #0D9488; border-color: #99F6E4; background: #F0FDFA; }

  .gha-panel {
    background: rgba(255,255,255,0.92);
    border: 1px solid #E2E8F0;
    border-radius: 20px;
    padding: 1.2rem 1.35rem 0.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  }
  .gha-panel h3 {
    margin: 0 0 0.65rem 0;
    font-size: 1.05rem;
    font-weight: 700;
    color: #334155;
  }

  .repo-card {
    border-radius: 18px;
    padding: 1rem 1.05rem;
    min-height: 210px;
    margin-bottom: 0.35rem;
    border: 2px solid var(--card-border);
    background: linear-gradient(160deg, #FFFFFF 0%, var(--card-bg) 100%);
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
  }
  .repo-card:hover { transform: translateY(-4px); box-shadow: 0 16px 36px rgba(15, 23, 42, 0.1); }
  .repo-card.selected {
    border-color: var(--card-accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--card-accent) 25%, transparent),
                0 16px 36px color-mix(in srgb, var(--card-accent) 20%, transparent);
  }
  .repo-rank {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 800;
    padding: 0.15rem 0.5rem;
    border-radius: 999px;
    background: var(--card-accent);
    color: white;
    margin-bottom: 0.45rem;
  }
  .repo-name {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.88rem;
    color: #4F46E5;
    font-weight: 700;
    margin-bottom: 0.35rem;
    word-break: break-all;
  }
  .repo-label {
    font-size: 0.67rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #94A3B8;
    margin-top: 0.55rem;
    margin-bottom: 0.1rem;
    font-weight: 700;
  }
  .repo-text { font-size: 0.82rem; color: #475569; line-height: 1.5; }

  .section-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: #1E293B;
    margin: 1.25rem 0 0.35rem;
  }
  .section-caption { color: #64748B; margin-bottom: 0.75rem; }

  div[data-testid="stChatMessage"] {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 0.55rem 0.85rem;
    margin-bottom: 0.55rem;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
  }
  .stTextArea textarea {
    border-radius: 14px !important;
    border: 2px solid #E9D5FF !important;
    background: #FEFCFF !important;
  }
  .stTextArea textarea:focus {
    border-color: #A855F7 !important;
    box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.2) !important;
  }
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFFFFF, #FAF5FF) !important;
    border-right: 1px solid #EDE9FE;
  }
</style>
        """,
        unsafe_allow_html=True,
    )


def _current_phase(has_plan: bool, has_recs: bool, has_overview: bool, has_qa: bool) -> int:
    if has_qa and has_overview:
        return 4
    if has_overview:
        return 3
    if has_recs:
        return 2
    if has_plan:
        return 1
    return 0


def _render_hero(phase_idx: int) -> None:
    steps_html = []
    for i, name in enumerate(PHASES):
        cls = "gha-step"
        if i < phase_idx:
            cls += " done"
        elif i == phase_idx:
            cls += " active"
        steps_html.append(f'<div class="{cls}">{i + 1}. {name}</div>')

    left, right = st.columns([1, 4], gap="medium")
    with left:
        if LOGO_PATH.is_file():
            st.image(str(LOGO_PATH), width=120)
        else:
            st.markdown("### 🐙📚")
    with right:
        st.markdown(
            f"""
<div class="gha-hero">
  <span class="gha-badge gha-badge-1">Repo discovery</span>
  <span class="gha-badge gha-badge-2">Gemini ranked</span>
  <span class="gha-badge gha-badge-3">File-grounded Q&A</span>
  <h1>Learn from GitHub repositories</h1>
  <p>Describe what you want to learn — we search GitHub, pick three repos, summarize one, then answer from real files.</p>
  <div class="gha-steps">{"".join(steps_html)}</div>
</div>
            """,
            unsafe_allow_html=True,
        )


def _repo_card_html(r: Any, index: int, selected: bool) -> str:
    accent, accent2, bg = CARD_ACCENTS[index % len(CARD_ACCENTS)]
    cls = "repo-card selected" if selected else "repo-card"
    return f"""
<div class="{cls}" style="--card-accent:{accent};--card-border:{accent2}44;--card-bg:{bg};">
  <span class="repo-rank">#{index + 1} pick</span>
  <div class="repo-name">{r.full_name}</div>
  <div class="repo-label">Why</div>
  <div class="repo-text">{r.why}</div>
  <div class="repo-label">Caveats</div>
  <div class="repo-text">{r.caveats}</div>
  <div class="repo-label">Best for</div>
  <div class="repo-text">{r.best_for}</div>
</div>
    """


def _ensure_gh() -> GitHubService:
    if "gh_client" not in st.session_state:
        st.session_state.gh_client = GitHubService(github_token())
    return cast(GitHubService, st.session_state.gh_client)


def _html_url(candidates: list[dict[str, Any]], full_name: str) -> str | None:
    for c in candidates:
        if c.get("full_name") == full_name:
            return c.get("html_url")
    return None


def _render_transcript(transcript: list[BaseMessage]) -> None:
    for m in transcript:
        if isinstance(m, HumanMessage):
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(m.content)
        elif isinstance(m, AIMessage):
            content = m.content or ""
            if isinstance(content, list):
                content = "".join(str(p) for p in content)
            if content.strip():
                with st.chat_message("assistant", avatar="✨"):
                    st.markdown(str(content))
            tcs = getattr(m, "tool_calls", None) or []
            if tcs:
                names = ", ".join(tc.get("name", "") for tc in tcs)
                st.caption(f"Read from repo: {names}")
        elif isinstance(m, ToolMessage):
            with st.expander("File excerpt", expanded=False):
                st.code(m.content[:8000] + ("…" if len(str(m.content)) > 8000 else ""), language="text")


def _init_session() -> None:
    defaults: dict[str, Any] = {
        "learning_goal": "",
        "search_plan": None,
        "candidates": [],
        "recommendations": None,
        "selected_full_name": None,
        "picked_repo": None,
        "overview_md": None,
        "qa_transcript": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def main() -> None:
    st.set_page_config(
        page_title="GitHub Learning Agent",
        page_icon="🐙",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_styles()

    try:
        google_api_key()
    except ValueError as e:
        st.error(str(e))
        st.info("Copy `.env.example` to `.env` and set `GOOGLE_API_KEY`.")
        return

    _init_session()

    plan = cast(SearchPlan | None, st.session_state.search_plan)
    recs = cast(RepoRecommendations | None, st.session_state.recommendations)
    has_recs = bool(recs and recs.recommendations)
    has_overview = bool(st.session_state.overview_md)
    has_qa = bool(st.session_state.qa_transcript)
    phase_idx = _current_phase(bool(plan), has_recs, has_overview, has_qa)
    _render_hero(phase_idx)

    with st.sidebar:
        if LOGO_PATH.is_file():
            st.image(str(LOGO_PATH), width=72)
        st.markdown("**Session**")
        st.code(gemini_model(), language=None)
        if github_token():
            st.success("GitHub token active")
        else:
            st.warning("No GitHub token")
        if st.button("Start over", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    st.markdown('<div class="gha-panel"><h3>What do you want to learn?</h3>', unsafe_allow_html=True)
    goal = st.text_area(
        "learning_goal_input",
        value=st.session_state.learning_goal,
        height=88,
        placeholder="e.g. I want to learn LangGraph for building agent workflows",
        label_visibility="collapsed",
    )
    st.session_state.learning_goal = goal
    st.markdown("</div>", unsafe_allow_html=True)

    discover = st.button(
        "Search GitHub & rank top 3",
        type="primary",
        disabled=not goal.strip(),
    )

    if discover:
        with st.spinner("Planning searches with Gemini, querying GitHub…"):
            gh = _ensure_gh()
            try:
                new_plan = pipelines.plan_searches(goal)
                st.session_state.search_plan = new_plan
                candidates = pipelines.collect_candidates(gh, new_plan.queries)
                st.session_state.candidates = candidates
                st.session_state.recommendations = pipelines.rank_top_three(
                    goal, new_plan.goal_restated, candidates
                )
                st.session_state.selected_full_name = None
                st.session_state.picked_repo = None
                st.session_state.overview_md = None
                st.session_state.qa_transcript = []
                st.rerun()
            except Exception as e:
                st.error(f"Discovery failed: {e}")
                return

    plan = cast(SearchPlan | None, st.session_state.search_plan)
    if plan:
        with st.expander("How we searched", expanded=False):
            st.markdown(f"**Interpreted as:** {plan.goal_restated}")
            st.markdown("**Keywords:** " + ", ".join(f"`{k}`" for k in plan.keywords))
            for q in plan.queries:
                st.code(q, language="text")

    recs = cast(RepoRecommendations | None, st.session_state.recommendations)
    if recs and recs.recommendations:
        st.markdown('<p class="section-title">Choose a repository</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="section-caption">Three colorful picks — tutorial, examples, and practical.</p>',
            unsafe_allow_html=True,
        )

        if st.session_state.picked_repo is None:
            st.session_state.picked_repo = recs.recommendations[0].full_name

        cols = st.columns(3, gap="medium")
        for i, r in enumerate(recs.recommendations):
            selected = st.session_state.picked_repo == r.full_name
            with cols[i]:
                st.markdown(_repo_card_html(r, i, selected), unsafe_allow_html=True)
                if st.button(
                    "Selected" if selected else "Use this repo",
                    key=f"pick_{i}",
                    use_container_width=True,
                    type="primary" if selected else "secondary",
                ):
                    st.session_state.picked_repo = r.full_name
                    st.rerun()

        st.markdown("")
        if st.button("Build learning overview", type="primary"):
            choice = st.session_state.picked_repo
            if not choice:
                st.error("Pick a repository first.")
            else:
                st.session_state.selected_full_name = choice
                with st.spinner("Reading README & manifests…"):
                    gh = _ensure_gh()
                    url = _html_url(st.session_state.candidates, choice)
                    ctx = pipelines.build_overview_context(gh, choice)
                    ov = pipelines.generate_overview(goal, choice, ctx)
                    st.session_state.overview_md = pipelines.overview_to_markdown(choice, url, ov)
                    st.session_state.qa_transcript = []
                st.rerun()

    if st.session_state.overview_md:
        st.markdown('<p class="section-title">Repository briefing</p>', unsafe_allow_html=True)
        st.markdown(st.session_state.overview_md)
        st.markdown('<p class="section-title">Ask about the code</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="section-caption">Answers are grounded in files from the selected public repo.</p>',
            unsafe_allow_html=True,
        )
        _render_transcript(st.session_state.qa_transcript)

        user_q = st.chat_input("Ask how something works in this repo…")
        if user_q:
            if not st.session_state.selected_full_name:
                st.error("Generate an overview first.")
                return
            with st.spinner("Reading files and answering…"):
                gh = _ensure_gh()
                _, new_transcript = pipelines.qa_turn(
                    learning_goal=goal,
                    full_name=st.session_state.selected_full_name or "",
                    overview_markdown=st.session_state.overview_md,
                    history=st.session_state.qa_transcript,
                    user_message=user_q,
                    gh=gh,
                )
                st.session_state.qa_transcript = new_transcript
            st.rerun()


if __name__ == "__main__":
    main()
