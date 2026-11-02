"""Detect upstream changes and apply them as one atomic commit per upstream."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from tools import build as build_module
from tools.upstream import GitHub, make_fetcher

EXIT_CHANGES = 10
MAX_LISTED_FILES = 20
COMMIT_PATHS = ["upstream.lock.json", "plugins"]


def _is_tool_code(path: str) -> bool:
    return path.startswith("src/") or path == "pyproject.toml"


# Apply order, and for each upstream which changed file counts as code (feat, not fix).
CODE_CHANGE: dict[str, Callable[[str], bool]] = {
    "ub-mode": lambda path: path == "SKILL.md",
    "crapper": _is_tool_code,
    "dryer": _is_tool_code,
    "mutator": _is_tool_code,
    "uml-viewer": lambda path: False,
}
ORDER = tuple(CODE_CHANGE)


class Upstream(Protocol):
    """GitHub operations the sync needs."""

    def resolve_sha(self, repo: str, ref: str) -> str:
        """Resolve a ref to a commit SHA."""
        ...

    def changed_paths(self, repo: str, base: str, head: str) -> list[str]:
        """List files changed between two commits."""
        ...


@dataclass(frozen=True)
class Change:
    """A pending update of one upstream."""

    name: str
    type: str
    old_sha: str
    new_sha: str
    paths: list[str]


def classify(name: str, paths: Sequence[str]) -> str:
    """Pick the conventional commit type for an upstream change.

    Args:
        name: Upstream name.
        paths: Files changed upstream.

    Returns:
        ``feat`` when the skill or tool code changed, otherwise ``fix``.
    """
    return "feat" if any(map(CODE_CHANGE[name], paths)) else "fix"


def check(lock: dict[str, dict[str, str]], github: Upstream) -> list[Change]:
    """Compare pinned SHAs with upstream heads.

    Args:
        lock: Mapping of upstream name to ``repo``, ``ref`` and ``sha``.
        github: Client used to resolve heads and list changed files.

    Returns:
        Pending changes in apply order.
    """
    changes = []
    for name in ORDER:
        pin = lock[name]
        head = github.resolve_sha(pin["repo"], pin["ref"])
        if head == pin["sha"]:
            continue
        paths = github.changed_paths(pin["repo"], pin["sha"], head)
        changes.append(Change(name, classify(name, paths), pin["sha"], head, paths))
    return changes


def commit_message(change: Change) -> str:
    """Build the conventional commit message for a change.

    Args:
        change: The pending change.

    Returns:
        The full commit message.
    """
    listed = [f"- {path}" for path in change.paths[:MAX_LISTED_FILES]]
    extra = len(change.paths) - MAX_LISTED_FILES
    if extra > 0:
        listed.append(f"- ... and {extra} more")
    subject = f"{change.type}(upstream/{change.name}): sync to {change.new_sha[:7]}"
    return subject + "\n\nChanged upstream files:\n" + "\n".join(listed)


def apply(
    changes: Sequence[Change],
    lock: dict[str, dict[str, str]],
    lock_path: Path,
    run_build: Callable[[], None],
    git: Callable[..., None],
    paths: Sequence[str],
) -> None:
    """Commit each change separately: lock bump, rebuild, commit.

    Args:
        changes: Pending changes in apply order.
        lock: Lock mapping, updated in place.
        lock_path: File the lock is written to.
        run_build: Callable regenerating the plugin from the lock.
        git: Callable running a git command with the given arguments.
        paths: Paths staged for every commit.
    """
    for change in changes:
        lock[change.name]["sha"] = change.new_sha
        lock_path.write_text(json.dumps(lock, indent=2) + "\n")
        run_build()
        git("add", "-A", *paths)
        git("commit", "-m", commit_message(change))


def _git(*args: str) -> None:
    subprocess.run(["git", *args], check=True)


def main(
    argv: Sequence[str] | None = None,
    lock_path: Path = build_module.LOCK,
    github: Upstream | None = None,
) -> int:
    """Run the sync CLI.

    Args:
        argv: Command-line arguments.
        lock_path: Lock file to read and update.
        github: Upstream client; defaults to the real GitHub API.

    Returns:
        ``10`` when ``--check`` finds changes, otherwise ``0``.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="report pending changes")
    mode.add_argument("--apply", action="store_true", help="commit pending changes")
    args = parser.parse_args(argv)

    github = github or GitHub(make_fetcher(os.environ.get("GITHUB_TOKEN")))
    lock = json.loads(lock_path.read_text())
    changes = check(lock, github)
    report = [
        {"name": c.name, "type": c.type, "old_sha": c.old_sha, "new_sha": c.new_sha}
        for c in changes
    ]
    print(json.dumps(report, indent=2))
    if args.apply:
        apply(changes, lock, lock_path, build_module.main, _git, COMMIT_PATHS)
        return 0
    return EXIT_CHANGES if changes else 0


if __name__ == "__main__":
    sys.exit(main())
