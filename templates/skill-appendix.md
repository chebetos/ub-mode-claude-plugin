# Tools in this plugin

The quality-gate tools named above ship with this plugin. Run them from the project root
you are changing. They need `uv` on the PATH.

| Tool    | Command                                  | Reference                                   |
| ------- | ---------------------------------------- | ------------------------------------------- |
| crapper | `${CLAUDE_SKILL_DIR}/scripts/crapper`    | `${CLAUDE_SKILL_DIR}/references/upstream/crapper.md` |
| dryer   | `${CLAUDE_SKILL_DIR}/scripts/dryer`      | `${CLAUDE_SKILL_DIR}/references/upstream/dryer.md`   |
| mutator | `${CLAUDE_SKILL_DIR}/scripts/mutator`    | `${CLAUDE_SKILL_DIR}/references/upstream/mutator.md` |

- Order of use: crapper, then dryer, then mutator. See `${CLAUDE_SKILL_DIR}/references/usage.md`.
- Results land in `.metrics/` of the examined project.
- `uml-viewer` is not bundled (needs Clojure CLI and Java 21+). See
  `${CLAUDE_SKILL_DIR}/references/upstream/uml-viewer.md`; pin it with
  `UML_VIEWER_REF={{uml_viewer_sha}}`.
