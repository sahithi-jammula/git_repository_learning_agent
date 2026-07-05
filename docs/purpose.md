# Purpose

## Project goal

Help you **learn a technology from real GitHub repositories** — not from generic summaries alone.

You describe a learning goal (for example: *“I want to learn LangGraph”*). The app then:

1. **Plans GitHub searches** with Gemini (LangChain)
2. **Queries the GitHub REST API** and merges candidates
3. **Ranks exactly three repositories** with why / caveats / best-for
4. **Builds a structured overview** from README, root tree, and manifest files
5. **Answers questions** by reading files from the selected public repo (file-grounded Q&A)

## Who is it for?

- Developers exploring a new library or framework
- Learners who want **curated repo picks** instead of scrolling search results
- Anyone who wants **evidence-based answers** tied to actual repository files

## What it is not

- Not a hosted multi-user product (runs locally via Streamlit)
- Not guaranteed to find the “best” repos (heuristic search + LLM judgment)
- Not a full codebase indexer (breadth-first overview; depth via Q&A)

Run the app: [How to run](how-to-run.md)
