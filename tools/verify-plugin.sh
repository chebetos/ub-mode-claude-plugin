#!/bin/sh
# Verify the built plugin: versions match, launchers run, manifests validate.
# Requires: jq, uv, pnpm. POSIX sh; also works with the bash 3.2 shipped on macOS.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
SCRIPTS="$ROOT/plugins/ub-mode/skills/ub-mode/scripts"
CLAUDE_CODE_VERSION=2.1.312

plugin=$(jq -r .version "$ROOT/plugins/ub-mode/.claude-plugin/plugin.json")
market=$(jq -r .metadata.version "$ROOT/.claude-plugin/marketplace.json")
if [ "$plugin" != "$market" ]; then
  echo "version mismatch: plugin=$plugin marketplace=$market" >&2
  exit 1
fi

for tool in crapper dryer mutator; do
  "$SCRIPTS/$tool" --help > /dev/null
done

(
  cd "$ROOT/smoke/py_project"
  trap 'rm -rf .metrics' EXIT
  "$SCRIPTS/crapper" > /dev/null
  test -f .metrics/crap.edn
)

cd "$ROOT"
pnpm dlx "@anthropic-ai/claude-code@$CLAUDE_CODE_VERSION" plugin validate --strict .
pnpm dlx "@anthropic-ai/claude-code@$CLAUDE_CODE_VERSION" plugin validate --strict ./plugins/ub-mode
