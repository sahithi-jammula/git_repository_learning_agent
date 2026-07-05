from __future__ import annotations

import base64
import json
from typing import Any

import httpx

from github_learning_agent.ssl_setup import ca_bundle_path


class GitHubService:
    """Minimal GitHub REST client for public repo search and file reads."""

    def __init__(self, token: str | None = None) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(
            base_url="https://api.github.com",
            headers=headers,
            timeout=30.0,
            verify=ca_bundle_path(),
        )

    def close(self) -> None:
        self._client.close()

    def search_repositories(self, q: str, per_page: int = 20) -> list[dict[str, Any]]:
        r = self._client.get(
            "/search/repositories",
            params={"q": q, "sort": "stars", "order": "desc", "per_page": per_page},
        )
        r.raise_for_status()
        data = r.json()
        return list(data.get("items") or [])

    def get_readme_text(self, owner: str, repo: str) -> str | None:
        r = self._client.get(
            f"/repos/{owner}/{repo}/readme",
            headers={"Accept": "application/vnd.github.raw"},
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.text

    def list_root_contents(self, owner: str, repo: str) -> list[dict[str, Any]]:
        r = self._client.get(f"/repos/{owner}/{repo}/contents")
        if r.status_code == 404:
            return []
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return data
        return []

    def get_file_text(self, owner: str, repo: str, path: str, max_chars: int = 120_000) -> str:
        r = self._client.get(f"/repos/{owner}/{repo}/contents/{path}")
        if r.status_code == 404:
            return f"[404: no file at {path}]"
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return f"[Path {path} is a directory; use a file path.]"
        content = data.get("content")
        encoding = data.get("encoding")
        if encoding == "base64" and content:
            raw = base64.b64decode(content).decode("utf-8", errors="replace")
            if len(raw) > max_chars:
                return raw[:max_chars] + "\n\n[Truncated by GitHub Learning Agent]"
            return raw
        if data.get("download_url"):
            rr = httpx.get(data["download_url"], timeout=30.0, verify=ca_bundle_path())
            rr.raise_for_status()
            raw = rr.text
            if len(raw) > max_chars:
                return raw[:max_chars] + "\n\n[Truncated by GitHub Learning Agent]"
            return raw
        return json.dumps(data, indent=2)[:max_chars]
