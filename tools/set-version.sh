#!/bin/sh
# Write a release version into plugin.json and marketplace.json, preserving formatting.
# Usage: tools/set-version.sh MAJOR.MINOR.PATCH
set -eu

version=${1:?usage: set-version.sh MAJOR.MINOR.PATCH}
case "$version" in
  [0-9]*.[0-9]*.[0-9]*) ;;
  *) echo "invalid version: $version" >&2; exit 1 ;;
esac

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
for file in "$ROOT/plugins/ub-mode/.claude-plugin/plugin.json" "$ROOT/.claude-plugin/marketplace.json"; do
  sed -E -i.bak "s/(\"version\": \")[^\"]+(\")/\1$version\2/" "$file"
  rm -f "$file.bak"
done
