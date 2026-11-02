# Using the quality-gate tools

Run every tool from the root of the project being changed. All three need `uv`; the launchers
resolve their Python dependencies on first run. Each writes machine-readable results to
`.metrics/` and prints a table.

## Order

1. **crapper**: complexity x coverage per function. Goal: every function under CRAP 10. Split the
   function, test it, or both.
2. **dryer**: structural duplication. Goal: remove every pair ranked 0.8 or above.
3. **mutator**: mutation testing. Goal: cover the uncovered, kill the survivors, delete dead code.
   It reads function names from crapper, so run crapper first.

## Commands

Paths are relative to the skill directory (the absolute paths are in the "Tools in this plugin"
table of `SKILL.md`).

```bash
scripts/crapper [path-or-filter ...]   # writes .metrics/crap.edn
scripts/dryer   [path-or-filter ...]   # writes .metrics/dry.edn
scripts/mutator [path-or-filter ...]   # writes .metrics/mutate/*.edn
```

Pass the file you are working on to `mutator`: the first run of a whole tree executes every
covered mutant and is slow.

Supported languages: Clojure, Java, Go, TypeScript/JavaScript, Rust and Python.

## Python projects

- Give the project its own `.venv` (or `venv`) with `pytest` installed. crapper and mutator both run
  the project's tests with that interpreter.
- crapper treats a project as pytest only when it finds pytest configuration (`pytest.ini`,
  `[tool.pytest.ini_options]`, `conftest.py` ...); otherwise it runs `unittest` and may find no tests.
- Without a project `.venv`, crapper falls back to `python3` on the `PATH`, which needs `coverage`
  and `pytest`. mutator falls back to its own interpreter, has no `pytest` and stops with
  "Baseline failed".
- Exactly 0% coverage on tested code means the tests did not run. Fix the setup before reading it
  as a finding.

## Full upstream documentation

- `references/upstream/crapper.md`
- `references/upstream/dryer.md`
- `references/upstream/mutator.md`
- `references/upstream/uml-viewer.md` (not bundled)
