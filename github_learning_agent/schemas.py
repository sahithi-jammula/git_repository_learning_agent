from __future__ import annotations

from pydantic import BaseModel, Field


class SearchPlan(BaseModel):
    """LLM output: how to search GitHub for learning repos."""

    goal_restated: str = Field(description="One-sentence restatement of the learning goal.")
    keywords: list[str] = Field(description="Topic keywords for ranking context.")
    queries: list[str] = Field(
        min_length=2,
        max_length=5,
        description="2–5 GitHub repository search query strings (GitHub q syntax).",
    )


class RepoRecommendation(BaseModel):
    full_name: str = Field(description="owner/repo exactly as on GitHub.")
    why: str = Field(description="Why this repo helps the learning goal.")
    caveats: str = Field(description="Risks: staleness, difficulty, scope mismatch, etc.")
    best_for: str = Field(description="e.g. beginners after X, intermediate, reference-only.")


class RepoRecommendations(BaseModel):
    recommendations: list[RepoRecommendation] = Field(
        min_length=3,
        max_length=3,
        description="Exactly three ranked repositories.",
    )


class ImportantFile(BaseModel):
    path: str
    why: str


class RepoOverview(BaseModel):
    purpose: str
    tech_stack: str
    key_concepts: list[str] = Field(default_factory=list)
    important_files: list[ImportantFile] = Field(default_factory=list)
    learning_path: list[str] = Field(default_factory=list)
