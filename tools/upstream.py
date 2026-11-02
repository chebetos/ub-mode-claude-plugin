"""Minimal GitHub API client for resolving, comparing and downloading upstream repos."""

from __future__ import annotations

import io
import json
import tarfile
import urllib.request
from collections.abc import Callable
from pathlib import Path

API = "https://api.github.com"
COMPARE_FILE_LIMIT = 300

Fetcher = Callable[[str], bytes]


class UpstreamError(RuntimeError):
    """Raised when an upstream response is malformed or unsafe."""


def build_request(url: str, token: str | None) -> urllib.request.Request:
    """Build a GitHub API request.

    Args:
        url: Absolute API URL.
        token: Optional GitHub token sent as a bearer token.

    Returns:
        The prepared request.
    """
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    return request


def make_fetcher(token: str | None = None) -> Fetcher:
    """Create a fetcher that performs authenticated GET requests.

    Args:
        token: Optional GitHub token.

    Returns:
        A callable returning the response body for a URL.
    """

    def fetch(url: str) -> bytes:
        with urllib.request.urlopen(build_request(url, token), timeout=60) as response:
            return response.read()

    return fetch


class GitHub:
    """Read-only GitHub client built on an injectable fetcher."""

    def __init__(self, fetch: Fetcher) -> None:
        """Store the fetcher used for every request.

        Args:
            fetch: Callable returning the response body for a URL.
        """
        self._fetch = fetch

    def resolve_sha(self, repo: str, ref: str) -> str:
        """Resolve a branch, tag or SHA to a full commit SHA.

        Args:
            repo: Repository as ``owner/name``.
            ref: Branch, tag or SHA.

        Returns:
            The commit SHA.

        Raises:
            UpstreamError: If the response has no SHA.
        """
        data = json.loads(self._fetch(f"{API}/repos/{repo}/commits/{ref}"))
        sha = data.get("sha")
        if not sha:
            raise UpstreamError(f"no sha returned for {repo}@{ref}")
        return str(sha)

    def changed_paths(self, repo: str, base: str, head: str) -> list[str]:
        """List files changed between two commits.

        Args:
            repo: Repository as ``owner/name``.
            base: Older commit SHA.
            head: Newer commit SHA.

        Returns:
            Changed file paths in API order.

        Raises:
            UpstreamError: If the file list reached the API limit and may be truncated.
        """
        data = json.loads(self._fetch(f"{API}/repos/{repo}/compare/{base}...{head}"))
        paths = [item["filename"] for item in data.get("files", [])]
        if len(paths) >= COMPARE_FILE_LIMIT:
            raise UpstreamError(f"comparison {repo} {base}...{head} may be truncated")
        return paths

    def extract_tarball(self, repo: str, sha: str, dest: Path) -> Path:
        """Download a commit tarball and extract it without the top-level prefix.

        Args:
            repo: Repository as ``owner/name``.
            sha: Commit SHA to download.
            dest: Empty directory to extract into.

        Returns:
            The directory holding the repository contents.

        Raises:
            UpstreamError: If an archive member would escape ``dest``.
        """
        payload = self._fetch(f"{API}/repos/{repo}/tarball/{sha}")
        root = dest.resolve()
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tar:
            for member in tar.getmembers():
                _, _, relative = member.name.partition("/")
                target = (root / relative).resolve()
                if not target.is_relative_to(root):
                    raise UpstreamError(f"unsafe path in archive: {member.name}")
                if not relative or not member.isfile():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                source = tar.extractfile(member)
                if source is not None:
                    target.write_bytes(source.read())
        return root
