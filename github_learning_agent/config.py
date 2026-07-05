from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from github_learning_agent.ssl_setup import configure_ssl_bundle

configure_ssl_bundle()


def google_api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "Missing GOOGLE_API_KEY (or GEMINI_API_KEY). "
            "Copy .env.example to .env and add your key from Google AI Studio."
        )
    return key


def github_token() -> str | None:
    return os.getenv("GITHUB_TOKEN") or None


def gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
