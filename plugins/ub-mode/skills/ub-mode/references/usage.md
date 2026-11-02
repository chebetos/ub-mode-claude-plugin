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

```bash
${CLAUDE_SKILL_DIR}/scripts/crapper [path-or-filter ...]   # writes .metrics/crap.edn
${CLAUDE_SKILL_DIR}/scripts/dryer   [path-or-filter ...]   # writes .metrics/dry.edn
${CLAUDE_SKILL_DIR}/scripts/mutator [path-or-filter ...]   # writes .metrics/mutate/*.edn
```

Pass the file you are working on to `mutator`: the first run of a whole tree executes every
covered mutant and is slow.

Supported languages: Clojure, Java, Go, TypeScript/JavaScript, Rust and Python.

## Known limitation

For Python projects, crapper may report 0% coverage when launched through `uv run --script`,
because it installs `coverage` into the interpreter that runs it. Treat a Python coverage of
exactly 0% on tested code as a tooling gap, not a finding.

## Full upstream documentation

- `${CLAUDE_SKILL_DIR}/references/upstream/crapper.md`
- `${CLAUDE_SKILL_DIR}/references/upstream/dryer.md`
- `${CLAUDE_SKILL_DIR}/references/upstream/mutator.md`
- `${CLAUDE_SKILL_DIR}/references/upstream/uml-viewer.md` (not bundled)
