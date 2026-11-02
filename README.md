# ub-mode Claude Code plugin

A Claude Code marketplace that packages [unclebob/ub-mode](https://github.com/unclebob/ub-mode)
and the quality-gate tools it relies on, and keeps them in sync with upstream automatically.

## What you get

`ub-mode` is a skill that makes the agent follow a fixed discipline on every code change:

1. **First make it work**: laziness protocol, TDD, redesign from first principles, subtract before
   you add, domain modeling and boundary discipline.
2. **Then make it right**: fix root causes, test behavior rather than implementation, and pass three
   deterministic quality gates (below).
3. **Practice**: keep a log, guard the context window, commit often in small ordered commits.

The plugin bundles the skill and the tools it names:

| Tool                                                 | What it does                                                                                  | In this plugin                                                 |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| [crapper](https://github.com/unclebob/crapper)       | Cyclomatic complexity and test coverage per function, combined into a CRAP score (goal: < 10) | Vendored, runs through `uv`                                    |
| [dryer](https://github.com/unclebob/dryer)           | Structural duplicate finder (goal: remove pairs ranked 0.8 or above)                          | Vendored, runs through `uv`                                    |
| [mutator](https://github.com/unclebob/mutator)       | Mutation testing: uncovered code and surviving mutants (goal: cover, kill, delete)            | Vendored, runs through `uv`                                    |
| [uml-viewer](https://github.com/unclebob/uml-viewer) | Live UML viewer coloured by CRAP and mutation scores (Clojure, needs Java 21+)                | Not bundled. Documented, pinned commit tracked for the install |

crapper, dryer and mutator support Clojure, Java, Go, TypeScript/JavaScript, Rust and Python.

## Requirements

- [Claude Code](https://code.claude.com)
- [`uv`](https://docs.astral.sh/uv/) on the `PATH` (`brew install uv`). The tool launchers resolve
  their Python dependencies on first run, so the first run needs network access.
- Python 3.11 or newer is fetched by `uv` when missing.
- Optional, only for uml-viewer: Clojure CLI and Java 21+.

## Install

```bash
claude plugin marketplace add chebetos/ub-mode-claude-plugin
claude plugin install ub-mode@ub-mode-marketplace
```

Or, inside a session:

```text
/plugin marketplace add chebetos/ub-mode-claude-plugin
/plugin install ub-mode@ub-mode-marketplace
```

Auto-update is off by default for third-party marketplaces. Enable it in `/plugin` under
Marketplaces, or update manually with `claude plugin update ub-mode@ub-mode-marketplace`.

## Use

The skill never activates on its own (`disable-model-invocation: true`). Invoke it explicitly when you
want the discipline applied:

```text
/ub-mode:ub-mode add pagination to the orders endpoint
```

Claude then works test-first and, in the "make it right" phase, runs the bundled tools from the root
of your project, in this order:

1. `crapper`: split or test every function above CRAP 10.
2. `dryer`: eliminate duplication ranked 0.8 or above.
3. `mutator`: cover the uncovered, kill the survivors, delete dead code. It reads function names from
   crapper, so crapper must have run first.

Results are written to `.metrics/` in your project and printed as tables. The skill pre-approves
only these three launchers (plus `Read`) while it runs. Details and flags are in the skill's
`references/` directory: a short `usage.md` and the upstream README of every tool, pinned to the
bundled commit.

### Known limitations

- Python projects need their own `.venv` (or `venv`) with `pytest` for crapper and mutator to run
  the tests. Without one, crapper falls back to `python3` on the `PATH` (needs `coverage` and
  `pytest`) and mutator stops with "Baseline failed". Exactly 0% coverage on tested code means the
  tests did not run. See the skill's `references/usage.md`.
- The first `mutator` run over a whole tree executes every covered mutant. Pass the file you are
  working on.

## How it stays up to date

- `upstream.lock.json` pins one commit for each of ub-mode, crapper, dryer, mutator and uml-viewer.
- `tools/sync.py --check` compares the pins with upstream heads and exits `10` when something moved.
- A GitHub Actions workflow runs it every Monday. When something changed it recreates the
  `upstream-sync` branch, adds **one commit per upstream** (`feat(upstream/crapper): sync to 6fd92c4`
  when skill or tool code changed, `fix(...)` when only documentation did), verifies the plugin,
  and opens or updates a single pull request. Events caused by `GITHUB_TOKEN` do not start
  workflows, so the sync workflow dispatches `ci.yml` on the branch; its checks attach to the
  branch head commit.
- Pull requests are merged with **rebase** so each commit reaches `main` and
  [semantic-release](https://github.com/semantic-release/semantic-release) can version it. It writes
  one version into `plugin.json` and the marketplace manifest, updates `CHANGELOG.md` and
  creates the GitHub release. Breaking changes are never automatic: add a `BREAKING CHANGE:` footer
  by hand while reviewing the pull request.

## Repository layout

```text
.claude-plugin/marketplace.json     marketplace manifest
plugins/ub-mode/                    the plugin (everything under skills/ is generated except usage.md)
upstream.lock.json                  pinned upstream commits
templates/                          frontmatter overlay, skill appendix, launcher template, dependency pins
tools/                              build.py, sync.py, upstream.py, verify-plugin.sh, set-version.sh
tests/                              pytest suite for the tools
smoke/                              tiny project used to smoke-test the launchers
```

## Development

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run ty check

export GITHUB_TOKEN=$(gh auth token)          # avoids API rate limits
uv run python -m tools.sync --check           # report pending upstream changes
uv run python -m tools.build                  # regenerate plugins/ub-mode from the lock
tools/verify-plugin.sh                        # smoke test and validate manifests (needs jq, pnpm)
```

Do not edit generated files by hand. Change `templates/` or `tools/` and rebuild. Contribution rules,
commit conventions and the release flow are in [CLAUDE.md](CLAUDE.md).

### Maintainer setup

Pushing is manual. After creating the repository:

- Allow **rebase merging only** in the repository settings.
- Under Actions, set workflow permissions to read and write, and allow Actions to create pull
  requests.
- Decide how semantic-release pushes its `chore(release)` commit to `main`. On a personal account
  GitHub Actions usually cannot be a ruleset bypass actor, so a `GITHUB_TOKEN` push is rejected as
  soon as `main` requires pull requests. Either leave `main` unprotected, or use a GitHub App or
  fine-grained personal access token that is on the ruleset bypass list. The release workflow
  currently uses `GITHUB_TOKEN` and needs adapting for the latter.
- `brew install lefthook && lefthook install` to validate commit messages locally.

## Licenses and attribution

All upstream work belongs to Robert C. Martin (`unclebob`). crapper, dryer and mutator are 0BSD
licensed. **ub-mode itself and uml-viewer publish no license.** The ub-mode `SKILL.md` is included
verbatim with attribution; uml-viewer is not redistributed. See
[plugins/ub-mode/NOTICE.md](plugins/ub-mode/NOTICE.md). This repository declares no license of its
own yet.
