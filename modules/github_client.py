"""GitHub client module — repository interaction via GitHub API."""

from __future__ import annotations

import base64
import time
from typing import Optional

import httpx
from config import settings


class GitHubClient:
    """Fetch source code from the Metrics app repo via GitHub API."""

    def __init__(self, repo: str | None = None, token: str | None = None):
        self.repo = repo or settings.GITHUB_REPO
        self.token = token or settings.GITHUB_TOKEN
        self.base_url = "https://api.github.com"
        self._cache: dict[str, tuple[str, float]] = {}  # {path: (content, timestamp)}
        self.cache_ttl = 600  # 10 minutes

    @property
    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SkillfieldSentinel/1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def get_file_content(self, file_path: str, branch: str = "main") -> str | None:
        """Fetch a file's content from GitHub. Returns None if not found. Uses cache."""
        cache_key = f"{file_path}@{branch}"

        # Check cache first (with TTL)
        if cache_key in self._cache:
            content, cached_at = self._cache[cache_key]
            if time.time() - cached_at < self.cache_ttl:
                return content

        if not self.token:
            return None

        url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
        params = {"ref": branch}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=self._headers, params=params)

                if resp.status_code == 404:
                    return None
                resp.raise_for_status()

                data = resp.json()
                if data.get("encoding") == "base64" and data.get("content"):
                    content = base64.b64decode(data["content"]).decode("utf-8")
                    self._cache[cache_key] = (content, time.time())
                    return content

                return None
        except httpx.HTTPError:
            return None

    async def get_directory_listing(self, dir_path: str, branch: str = "main") -> list[str]:
        """List files in a directory."""
        if not self.token:
            return []

        url = f"{self.base_url}/repos/{self.repo}/contents/{dir_path}"
        params = {"ref": branch}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=self._headers, params=params)

                if resp.status_code == 404:
                    return []
                resp.raise_for_status()

                data = resp.json()
                if isinstance(data, list):
                    return [item["path"] for item in data]
                return []
        except httpx.HTTPError:
            return []

    async def create_pull_request(
        self,
        branch_name: str,
        title: str,
        body: str,
        files: list[dict],
    ) -> dict:
        """Create a PR with file changes. Returns {pr_url, pr_number}.

        Each item in ``files`` should be: {"path": "...", "content": "..."}.
        If GITHUB_TOKEN is missing, returns a mock response for demo purposes.
        """
        if not self.token:
            return {
                "pr_url": f"https://github.com/{self.repo}/pull/MOCK",
                "pr_number": 0,
                "mock": True,
                "message": "GITHUB_TOKEN not configured — PR creation skipped.",
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = self._headers

                # 1. Get SHA of main branch
                ref_resp = await client.get(
                    f"{self.base_url}/repos/{self.repo}/git/ref/heads/main",
                    headers=headers,
                )
                ref_resp.raise_for_status()
                main_sha = ref_resp.json()["object"]["sha"]

                # 2. Create new branch from main
                create_ref_resp = await client.post(
                    f"{self.base_url}/repos/{self.repo}/git/refs",
                    headers=headers,
                    json={"ref": f"refs/heads/{branch_name}", "sha": main_sha},
                )
                create_ref_resp.raise_for_status()

                # 3. For each file change, create/update file on the branch
                for file_change in files:
                    file_path = file_change["path"]
                    file_content = file_change["content"]
                    encoded = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")

                    # Try to get existing file SHA for update
                    existing_resp = await client.get(
                        f"{self.base_url}/repos/{self.repo}/contents/{file_path}",
                        headers=headers,
                        params={"ref": branch_name},
                    )
                    put_body: dict = {
                        "message": f"fix: {title} - update {file_path}",
                        "content": encoded,
                        "branch": branch_name,
                    }
                    if existing_resp.status_code == 200:
                        put_body["sha"] = existing_resp.json()["sha"]

                    await client.put(
                        f"{self.base_url}/repos/{self.repo}/contents/{file_path}",
                        headers=headers,
                        json=put_body,
                    )

                # 4. Create PR from branch to main
                pr_resp = await client.post(
                    f"{self.base_url}/repos/{self.repo}/pulls",
                    headers=headers,
                    json={
                        "title": title,
                        "body": body,
                        "head": branch_name,
                        "base": "main",
                    },
                )
                pr_resp.raise_for_status()
                pr_data = pr_resp.json()

                return {
                    "pr_url": pr_data["html_url"],
                    "pr_number": pr_data["number"],
                }
        except httpx.HTTPError as exc:
            return {
                "pr_url": None,
                "pr_number": None,
                "error": str(exc),
            }
