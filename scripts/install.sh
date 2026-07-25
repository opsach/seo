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
#   --ref REF      branch or tag to install from (default: main)
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
REF="main"
REF_EXPLICIT=0
QUIET=0

# Printed by --help. Cannot be derived from "$0": under `curl ... | bash` the
# script has no path on disk, so reading usage out of the file is impossible.
usage() {
  cat <<'EOF'
Install the SEO & GEO Consultant plugin into a project (or your user profile).

  curl -fsSL https://raw.githubusercontent.com/opsach/seo/main/scripts/install.sh | bash
  ./scripts/install.sh --target /path/to/project

Flags:
  --target DIR   where to install (default: current directory)
  --user         install into ~/.claude instead of DIR/.claude
  --ref REF      branch or tag to install from (default: main)
  --uninstall    remove a previous install
  --quiet        less output

Safe to re-run: an existing install is replaced cleanly, never nested inside itself.
Pass flags through a pipe with `bash -s --`, e.g. `... | bash -s -- --user`.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="${2:?--target needs a directory}"; shift 2 ;;
    --user) SCOPE="user"; shift ;;
    --ref) REF="${2:?--ref needs a branch or tag}"; REF_EXPLICIT=1; shift 2 ;;
    --uninstall) MODE="uninstall"; shift ;;
    --quiet) QUIET=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "install.sh: unknown option $1" >&2; usage >&2; exit 2 ;;
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
#
# Only a script that exists as a file on disk can have a clone around it. Under
# `curl ... | bash` there is no such file: "$0" is "bash", dirname gives ".", and
# treating that as the script's home makes the *caller's* parent directory look
# like a checkout -- installing from an unrelated tree and silently ignoring
# --ref. Resolve the local path only when there genuinely is one.
SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR=""
case "$SELF" in
  bash|sh|-*|"") ;;                                   # piped or sourced: no file
  *) [ -f "$SELF" ] && SCRIPT_DIR="$(cd "$(dirname "$SELF")" 2>/dev/null && pwd || echo "")" ;;
esac

SRC=""
if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/../skills/$SKILL" ] && [ "$REF_EXPLICIT" = 0 ]; then
  SRC="$(cd "$SCRIPT_DIR/.." && pwd)"
  say "Installing from local checkout: $SRC"
else
  if [ -n "$SCRIPT_DIR" ] && [ "$REF_EXPLICIT" = 1 ]; then
    say "--ref $REF given: fetching that ref rather than using the surrounding checkout."
  fi
  command -v git >/dev/null 2>&1 || die "git is required when not running from a clone"
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  say "Fetching $REPO_URL ($REF) ..."
  git clone --depth 1 --branch "$REF" --quiet "$REPO_URL" "$TMP/seo" \
    || die "clone of ref '$REF' failed -- check the ref name and network access to github.com"
  SRC="$TMP/seo"
fi

# Validate the whole source tree before touching the destination. Checking only
# SKILL.md lets a partial tree through, and the copy then dies halfway with a raw
# `cp: cannot stat`, leaving a half-installed .claude behind.
src_problem=""
[ -f "$SRC/skills/$SKILL/SKILL.md" ] || src_problem="skills/$SKILL/SKILL.md is missing"
if [ -z "$src_problem" ]; then
  set -- "$SRC"/agents/seo-*.md
  [ -f "$1" ] || src_problem="agents/seo-*.md matched no files"
fi
if [ -z "$src_problem" ]; then
  set -- "$SRC"/commands/*.md
  [ -f "$1" ] || src_problem="commands/*.md matched no files"
fi
if [ -n "$src_problem" ]; then
  printf 'install.sh: source tree at %s is not a usable copy of this plugin: %s\n' "$SRC" "$src_problem" >&2
  if [ -n "$SCRIPT_DIR" ] && [ "$SRC" != "${TMP:-}/seo" ]; then
    printf '  This came from the directory around the script, not from GitHub.\n' >&2
    printf '  Remedy: run the installer from a full clone of %s,\n' "$REPO_URL" >&2
    printf '          or pipe it from GitHub:\n' >&2
    printf '          curl -fsSL %s/raw/%s/scripts/install.sh | bash -s -- --ref %s\n' "$REPO_URL" "$REF" "$REF" >&2
  else
    printf '  Remedy: ref %s does not carry the full plugin -- install from a ref that does (try --ref main).\n' "$REF" >&2
  fi
  exit 1
fi

# ------------------------------------------------------------------ install
# Build the install in a staging directory and verify it there. A copy that dies
# partway (or a tree that fails verification) must not leave the destination in a
# half-installed state: Claude Code would load a skill whose agents are missing
# and /seo-pipeline would fail at runtime. Nothing moves into place until the
# staged copy is complete and checked.
mkdir -p "$DEST"
rm -rf "$DEST"/.install-staging.*   # stale staging from a run that was killed
STAGE="$DEST/.install-staging.$$"
mkdir -p "$STAGE/agents" "$STAGE/commands" "$STAGE/scripts"
cleanup() {
  [ -n "${STAGE:-}" ] && rm -rf "$STAGE"
  [ -n "${TMP:-}" ] && rm -rf "$TMP"
  return 0
}
trap cleanup EXIT

cp -R "$SRC/skills/$SKILL" "$STAGE/skill"
cp "$SRC"/agents/*.md "$STAGE/agents/"
cp "$SRC"/commands/*.md "$STAGE/commands/"
if [ -f "$SRC/scripts/seo-probe.py" ]; then
  cp "$SRC/scripts/seo-probe.py" "$STAGE/scripts/"
  chmod +x "$STAGE/scripts/seo-probe.py"
else
  say "warning: this ref ($REF) predates scripts/seo-probe.py -- live-site audits will"
  say "         have no evidence collector. Install from a ref that includes it."
fi

# ------------------------------------------------------------------- verify
agents=$(ls "$STAGE"/agents/seo-*.md 2>/dev/null | wc -l | tr -d ' ')
cmds=$(ls "$STAGE"/commands/{seo-audit,seo-pipeline,aeo-plan}.md 2>/dev/null | wc -l | tr -d ' ')
refs=$(ls "$STAGE/skill/references"/*.md 2>/dev/null | wc -l | tr -d ' ')
[ -f "$STAGE/skill/SKILL.md" ] || die "verification failed: SKILL.md missing after copy"
[ "$agents" -ge 10 ] || die "verification failed: expected 10 agents, found $agents"
[ "$cmds" -eq 3 ] || die "verification failed: expected 3 commands, found $cmds"
[ "$refs" -ge 13 ] || die "verification failed: expected 13+ references, found $refs"

# ---------------------------------------------------------------- swap in
# Only our own files are replaced; anything else the project keeps in .claude/
# agents/ and commands/ is left alone.
mkdir -p "$DEST/agents" "$DEST/commands" "$DEST/skills" "$DEST/scripts"
# Replace, never nest: `cp -r src/dir dest/dir` copies *into* an existing
# directory, which on a second run produces skills/<skill>/<skill>. Remove first.
rm -rf "$DEST/skills/$SKILL"
mv "$STAGE/skill" "$DEST/skills/$SKILL"
cp "$STAGE"/agents/*.md "$DEST/agents/"
cp "$STAGE"/commands/*.md "$DEST/commands/"
if [ -f "$STAGE/scripts/seo-probe.py" ]; then
  cp "$STAGE/scripts/seo-probe.py" "$DEST/scripts/"
fi
rm -rf "$STAGE"

[ -f "$DEST/skills/$SKILL/SKILL.md" ] || die "install failed: SKILL.md missing at $DEST after swap"
python3 -c "import sys; sys.exit(0)" 2>/dev/null || say "note: python3 not found -- scripts/seo-probe.py needs it for live-site audits"

say ""
say "Installed into $DEST"
say "  skill      1  ($SKILL, $refs references)"
say "  agents     $agents"
say "  commands   $cmds  (/seo-pipeline, /seo-audit, /aeo-plan)"
if [ -f "$DEST/scripts/seo-probe.py" ]; then
  say "  scripts    1  (seo-probe.py)"
else
  say "  scripts    0  (no seo-probe.py on ref $REF -- live-site audits have no evidence collector)"
fi
say ""
if [ "$SCOPE" = "project" ]; then
  say "Commit .claude/ so every session on this repo -- CLI, desktop, or web -- picks it up."
fi
say "Start a new Claude Code session, then try:  /seo-audit"
