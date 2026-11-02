# CLAUDE.md

Claude Code marketplace wrapping [unclebob/ub-mode](https://github.com/unclebob/ub-mode) and its
tools (crapper, dryer, mutator, uml-viewer). See [README.md](README.md) for what it does.

## Layout

- `plugins/ub-mode/skills/ub-mode/` is **generated** by `tools/build.py` from `upstream.lock.json`
  and `templates/`. Never edit it by hand. The only hand-written file in it is
  `references/usage.md`.
- Hand-written sources: `tools/`, `tests/`, `templates/`, `smoke/`, workflows, manifests, docs.
- `plugins/ub-mode/NOTICE.md` is hand-written and must stay accurate when upstream licenses change.

## Commands

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run ty check
GITHUB_TOKEN=$(gh auth token) uv run python -m tools.sync --check
GITHUB_TOKEN=$(gh auth token) uv run python -m tools.build
tools/verify-plugin.sh
```

## Atomic commits

- One logical change per commit. If the message needs "and", split it.
- Every commit builds and passes tests on its own. No "fix previous commit" commits: amend or
  fixup locally before sharing.
- Tests ship in the same commit as the behavior they cover (test first, then implementation).
- Never mix generated output with unrelated hand-written changes. A change to `templates/` or
  `tools/build.py` and the regenerated `plugins/` output belong together; nothing else does.
- Upstream bumps are one commit per upstream, lock file and regenerated output together. The
  order is ub-mode, crapper, dryer, mutator, uml-viewer, because mutator imports crapper.
- Do not reformat or reorder code outside the change.

## Conventional commits

Format: `type(scope): subject`, lowercase subject, no trailing period. semantic-release derives
the version from these, so the type matters.

- Types: `feat` (minor), `fix` (patch), `refactor`, `test`, `docs`, `chore`, `ci`.
  `BREAKING CHANGE:` in the footer means major, and is added by a human only. A `!` in the header
  is rejected by commitlint.
- Scopes (enforced by commitlint): `upstream/ub-mode`, `upstream/crapper`, `upstream/dryer`,
  `upstream/mutator`, `upstream/uml-viewer`, `scripts`, `plugin`, `ci`, `sync`, `docs`.
- `feat(upstream/...)` when skill or tool code changed upstream, `fix(upstream/...)` when only
  documentation did.
- Commit messages explain why, what changed and how it was verified.

## Development rules

- Test first for everything in `tools/` (pytest, HTTP injected, no network in tests).
- Python 3.12, type hints and Google-style docstrings, `ruff` and `ty`. Standard library only in
  `tools/`.
- Pin exact versions of tools, actions and dependencies. Do not use `latest`, and skip releases
  younger than 5 days.
- Never run vendored upstream code in a step that holds a write token. See
  `.github/workflows/upstream-sync.yml`.
- Update `README.md` and this file whenever behavior or process changes.

## Release flow

- Pull requests are **rebase-merged** so every atomic commit reaches `main`.
- On push to `main`, CI runs and then semantic-release bumps `plugin.json` and
  `marketplace.json` together (`tools/set-version.sh`), updates `CHANGELOG.md`, tags and creates
  the GitHub release with a `chore(release): x.y.z [skip ci]` commit.
- Never push from an agent session. Pushing and repository settings are manual.
