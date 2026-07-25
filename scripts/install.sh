#!/usr/bin/env bash
#
# Install the SEO & GEO Consultant plugin into a project (or your user profile)
# without needing the /plugin command.
#
# From inside a project you want to audit:
#   curl -fsSL https://raw.githubusercontent.com/opsach/seo/main/scripts/install.sh | bash
#
# Or, from a clone of this repo:
#   ./scripts/install.sh --target /path/to/project
#
# Flags:
#   --target DIR   where to install (default: current directory)
#   --user         install into ~/.claude instead of DIR/.claude (available in every project)
#   --uninstall    remove a previous install
#   --quiet        less output
#
# Safe to re-run: an existing install is replaced cleanly, never nested inside itself.

set -euo pipefail

REPO_URL="https://github.com/opsach/seo"
SKILL="seo-geo-consultant"
TARGET="$PWD"
SCOPE="project"
MODE="install"
QUIET=0

while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="${2:?--target needs a directory}"; shift 2 ;;
    --user) SCOPE="user"; shift ;;
    --uninstall) MODE="uninstall"; shift ;;
    --quiet) QUIET=1; shift ;;
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "install.sh: unknown option $1" >&2; exit 2 ;;
  esac
done

say() { [ "$QUIET" = 1 ] || printf '%s\n' "$*"; }
die() { printf 'install.sh: %s\n' "$*" >&2; exit 1; }

if [ "$SCOPE" = "user" ]; then
  DEST="$HOME/.claude"
else
  [ -d "$TARGET" ] || die "target directory does not exist: $TARGET"
  DEST="$(cd "$TARGET" && pwd)/.claude"
fi

# ---------------------------------------------------------------- uninstall
if [ "$MODE" = "uninstall" ]; then
  removed=0
  for p in "$DEST/skills/$SKILL" "$DEST/scripts/seo-probe.py"; do
    [ -e "$p" ] && { rm -rf "$p"; removed=1; say "removed $p"; }
  done
  for f in "$DEST"/agents/seo-*.md; do
    [ -e "$f" ] && { rm -f "$f"; removed=1; }
  done
  for f in seo-audit.md seo-pipeline.md aeo-plan.md; do
    [ -e "$DEST/commands/$f" ] && { rm -f "$DEST/commands/$f"; removed=1; }
  done
  rmdir "$DEST/scripts" 2>/dev/null || true
  [ "$removed" = 1 ] && say "Uninstalled from $DEST" || say "Nothing to uninstall in $DEST"
  exit 0
fi

# ------------------------------------------------------------------- source
# Prefer the clone this script lives in; otherwise fetch a fresh one.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
SRC=""
if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/../skills/$SKILL" ]; then
  SRC="$(cd "$SCRIPT_DIR/.." && pwd)"
  say "Installing from local checkout: $SRC"
else
  command -v git >/dev/null 2>&1 || die "git is required when not running from a clone"
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  say "Fetching $REPO_URL ..."
  git clone --depth 1 --quiet "$REPO_URL" "$TMP/seo" || die "clone failed -- check network access to github.com"
  SRC="$TMP/seo"
fi

[ -f "$SRC/skills/$SKILL/SKILL.md" ] || die "source checkout looks wrong: no skills/$SKILL/SKILL.md under $SRC"

# ------------------------------------------------------------------ install
mkdir -p "$DEST/agents" "$DEST/commands" "$DEST/skills" "$DEST/scripts"

# Replace, never nest: `cp -r src/dir dest/dir` copies *into* an existing
# directory, which on a second run produces skills/<skill>/<skill>. Remove first.
rm -rf "$DEST/skills/$SKILL"
cp -R "$SRC/skills/$SKILL" "$DEST/skills/$SKILL"

cp "$SRC"/agents/*.md "$DEST/agents/"
cp "$SRC"/commands/*.md "$DEST/commands/"
cp "$SRC"/scripts/seo-probe.py "$DEST/scripts/"
chmod +x "$DEST/scripts/seo-probe.py"

# ------------------------------------------------------------------- verify
agents=$(ls "$DEST"/agents/seo-*.md 2>/dev/null | wc -l | tr -d ' ')
cmds=$(ls "$DEST"/commands/{seo-audit,seo-pipeline,aeo-plan}.md 2>/dev/null | wc -l | tr -d ' ')
refs=$(ls "$DEST/skills/$SKILL/references"/*.md 2>/dev/null | wc -l | tr -d ' ')
[ -f "$DEST/skills/$SKILL/SKILL.md" ] || die "verification failed: SKILL.md missing after copy"
[ "$agents" -ge 10 ] || die "verification failed: expected 10 agents, found $agents"
[ "$cmds" -eq 3 ] || die "verification failed: expected 3 commands, found $cmds"
[ "$refs" -ge 13 ] || die "verification failed: expected 13+ references, found $refs"
python3 -c "import sys; sys.exit(0)" 2>/dev/null || say "note: python3 not found -- scripts/seo-probe.py needs it for live-site audits"

say ""
say "Installed into $DEST"
say "  skill      1  ($SKILL, $refs references)"
say "  agents     $agents"
say "  commands   $cmds  (/seo-pipeline, /seo-audit, /aeo-plan)"
say "  scripts    1  (seo-probe.py)"
say ""
if [ "$SCOPE" = "project" ]; then
  say "Commit .claude/ so every session on this repo -- CLI, desktop, or web -- picks it up."
fi
say "Start a new Claude Code session, then try:  /seo-audit"
