#!/usr/bin/env bash
#
# Install the SEO & GEO Consultant plugin, and prove it can actually run.
#
# From inside a project you want to audit:
#   curl -fsSL https://raw.githubusercontent.com/opsach/seo/main/scripts/install.sh | bash
#
# Claude Code CLI users who want it registered as a real plugin instead:
#   curl -fsSL https://raw.githubusercontent.com/opsach/seo/main/scripts/install.sh | bash -s -- --plugin
#
# Or, from a clone of this repo:
#   ./scripts/install.sh --target /path/to/project
#
# Flags:
#   --plugin       install via the Claude Code plugin system (marketplace + install,
#                  in the required order) instead of copying files
#   --target DIR   where to install (default: current directory)
#   --user         install into ~/.claude instead of DIR/.claude (available in every project)
#   --ref REF      branch or tag to install from (default: main)
#   --check HOST   after installing, preflight HOST to prove live audits work here
#   --uninstall    remove a previous install
#   --quiet        less output
#
# Safe to re-run: an existing install is replaced cleanly, never nested inside itself.

set -euo pipefail

REPO_URL="https://github.com/opsach/seo"
REPO_SLUG="opsach/seo"
SKILL="seo-geo-consultant"
MARKET="opsach-seo"
TARGET="$PWD"
SCOPE="project"
MODE="install"
REF="main"
CHECK_HOST=""
QUIET=0

while [ $# -gt 0 ]; do
  case "$1" in
    --plugin) MODE="plugin"; shift ;;
    --target) TARGET="${2:?--target needs a directory}"; shift 2 ;;
    --user) SCOPE="user"; shift ;;
    --ref) REF="${2:?--ref needs a branch or tag}"; shift 2 ;;
    --check) CHECK_HOST="${2:?--check needs a host or URL}"; shift 2 ;;
    --uninstall) MODE="uninstall"; shift ;;
    --quiet) QUIET=1; shift ;;
    -h|--help) sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "install.sh: unknown option $1" >&2; exit 2 ;;
  esac
done

say() { [ "$QUIET" = 1 ] || printf '%s\n' "$*"; }
die() { printf 'install.sh: %s\n' "$*" >&2; exit 1; }

# An install that lands the files but cannot execute the probe is a broken install
# that reports success -- the failure would surface later, mid-audit, as a fabricated
# or empty finding. Prove the runtime here, at the one moment the user is watching.
#
# Return codes separate the two very different failures, because they have opposite
# remedies and only one of them means the install is bad:
#   0 = ready
#   1 = the install cannot run audits at all (no python3, or the probe won't execute)
#   2 = the install is fine; this environment cannot reach the host you named
# Conflating them would condemn a perfectly good install because a firewall exists.
#
# $1 = absolute path to the installed seo-probe.py ("" if this route has none)
readiness() {
  probe="${1:-}"
  say "Readiness"

  if ! command -v python3 >/dev/null 2>&1; then
    say "  FAIL  python3 not found -- live-site audits cannot run"
    say "        codebase audits still work; install python3 to enable URL audits"
    return 1
  fi
  # Being on PATH is not the same as working -- report the version we actually got.
  pyver="$(python3 -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null || true)"
  if [ -z "$pyver" ]; then
    say "  FAIL  python3 is on PATH but does not run"
    say "        repair the python3 install; live-site audits depend on it"
    return 1
  fi
  say "  ok    python3 $pyver"

  if [ -z "$probe" ] || [ ! -f "$probe" ]; then
    say "  FAIL  seo-probe.py not found -- live-site audits have no evidence collector"
    return 1
  fi
  if ! python3 "$probe" --help >/dev/null 2>&1; then
    say "  FAIL  seo-probe.py did not execute: python3 $probe --help"
    say "        re-run this installer; if it persists, open an issue with the error"
    return 1
  fi
  say "  ok    seo-probe.py runs"

  # Network is the dependency that most often turns a good install into a failed
  # audit, and it fails per-host. Only a real preflight can tell the user which.
  if [ -n "$CHECK_HOST" ]; then
    # `cmd || rc=$?` keeps this safe under `set -e` without toggling errexit --
    # toggling it inside a function silently overrides the caller's setting, which
    # turned an informational `return 2` into an immediate exit.
    rc=0
    out="$(python3 "$probe" preflight "$CHECK_HOST" 2>&1)" || rc=$?
    case "$rc" in
      0) say "  ok    $CHECK_HOST reachable -- live audits will work" ;;
      3) say "  FAIL  $CHECK_HOST blocked by this environment's network policy"
         say "        Not an install fault and not the site's fault: the request never left"
         say "        this machine. Allow the host in your egress settings and start a new"
         say "        session, or run the audit from a machine with normal internet access."
         return 2 ;;
      4) say "  warn  $CHECK_HOST reachable but it blocks automated clients"
         say "        an audit can still run; expect gaps where the site refuses the probe" ;;
      5) say "  FAIL  $CHECK_HOST unreachable (DNS or connection failure)"
         say "        check the hostname spelling and that the site is up"
         return 2 ;;
      *) say "  warn  preflight of $CHECK_HOST returned $rc"
         printf '%s\n' "$out" | sed 's/^/        /' ;;
    esac
  else
    say "  note  network to a specific client site is not tested"
    say "        before auditing, run: $0 --check <client-domain>"
  fi
  return 0
}

# Close out with a verdict that matches what readiness actually found. A broken
# runtime must not exit 0 -- that is the silent failure this repo forbids -- but a
# blocked target host is an environment fact, not a bad install, so it must not
# fail the install either.
#
# The two routes expose the slash commands under DIFFERENT names, so a single closing
# hint would be wrong for one of them. A plugin install namespaces its commands
# (`/seo-geo-consultant:seo-audit`); a file install in .claude/commands/ does not
# (`/seo-audit`). Typing the file-route form after a plugin install returns
# "Unknown command: /seo-audit", which reads as a failed install.
CMD_PREFIX=""
#
# $1 = readiness return code; remaining args = route-specific closing lines
finish() {
  rc="$1"; shift
  say ""
  for l in "$@"; do say "$l"; done
  case "$rc" in
    0) say "Components load at session start -- quit Claude Code and reopen it, then try:"
       say "  /${CMD_PREFIX}seo-audit https://example.com"
       exit 0 ;;
    2) say ""
       say "The plugin itself is installed and working -- only the host you checked is"
       say "out of reach from here. Restore access before running a live audit, or point"
       say "/${CMD_PREFIX}seo-audit at a codebase instead."
       exit 0 ;;
    *) say ""
       say "INSTALL INCOMPLETE: the files are in place but audits cannot run (see Readiness)."
       say "Fix the failure above and re-run this installer."
       exit 1 ;;
  esac
}

# -------------------------------------------------------------- plugin route
# `claude plugin install` before `marketplace add` fails with "not found in
# marketplace ... try `marketplace update`" -- advice that cannot work, because
# nothing was ever added. That single ordering trap is the most common install
# failure, so this route removes the ordering decision from the user entirely.
if [ "$MODE" = "plugin" ]; then
  command -v claude >/dev/null 2>&1 || die \
"the 'claude' CLI is not on PATH, so --plugin cannot run.
  Install it with:  npm install -g @anthropic-ai/claude-code
  Then reopen your terminal so PATH updates.
  Or drop --plugin: the default file install needs no CLI at all."

  ver="$(claude --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
  case "${ver%%.*}" in
    ''|0|1) die "claude ${ver:-<unreadable>} is too old -- 'claude plugin' needs 2.x.
  Upgrade with:  npm install -g @anthropic-ai/claude-code@latest" ;;
  esac
  say "Claude Code CLI $ver"

  # Both steps are idempotent, so re-running this is safe.
  if claude plugin marketplace list 2>/dev/null | grep -q "^[[:space:]]*>[[:space:]]*$MARKET$"; then
    say "  ok    marketplace $MARKET already registered"
  else
    say "  ..    adding marketplace $MARKET (from $REPO_SLUG)"
    claude plugin marketplace add "$REPO_SLUG" >/dev/null 2>&1 || die \
"could not add the marketplace from $REPO_SLUG.
  Most likely github.com is unreachable (proxy, VPN, or firewall).
  Check with:  git ls-remote https://github.com/$REPO_SLUG.git HEAD"
    say "  ok    marketplace $MARKET registered"
  fi

  # The marketplace is named $MARKET, which does NOT match the repo path passed to
  # `marketplace add`. Passing @seo here is the second-most-common failure; the
  # user never types either name.
  say "  ..    installing $SKILL@$MARKET"
  if ! claude plugin install "$SKILL@$MARKET" >/dev/null 2>&1; then
    die "the marketplace registered but 'claude plugin install $SKILL@$MARKET' failed.
  Re-run it directly to see the CLI's own error:
      claude plugin install $SKILL@$MARKET
  Then diagnose with:
      curl -fsSL https://raw.githubusercontent.com/$REPO_SLUG/main/scripts/doctor.sh | bash"
  fi

  claude plugin list 2>/dev/null | grep -q "$SKILL@$MARKET" \
    || die "install reported success but '$SKILL@$MARKET' is not in 'claude plugin list'.
  Diagnose with:  curl -fsSL https://raw.githubusercontent.com/$REPO_SLUG/main/scripts/doctor.sh | bash"
  say "  ok    $SKILL@$MARKET installed"

  # The plugin cache is versioned, so the probe path changes on every upgrade.
  # Resolve it rather than assuming a version.
  CFG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
  probe_path="$(ls -t "$CFG"/plugins/cache/*/"$SKILL"/*/scripts/seo-probe.py 2>/dev/null | head -1 || true)"

  say ""
  ready_rc=0; readiness "$probe_path" || ready_rc=$?
  CMD_PREFIX="$SKILL:"
  finish "$ready_rc" \
    "Installed as a Claude Code plugin (skill + 10 agents + 3 commands)." \
    "Plugin commands are namespaced -- the bare /seo-audit will not resolve."
fi

if [ "$SCOPE" = "user" ]; then
  # Claude Code reads user-level skills, agents and commands from its config dir,
  # which CLAUDE_CONFIG_DIR relocates. Installing into ~/.claude while that variable
  # is set puts the files somewhere nothing ever loads -- the install reports success
  # and the commands never appear.
  DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
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
  say "Fetching $REPO_URL ($REF) ..."
  git clone --depth 1 --branch "$REF" --quiet "$REPO_URL" "$TMP/seo" \
    || die "clone of ref '$REF' failed -- check the ref name and network access to github.com"
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
if [ -f "$SRC/scripts/seo-probe.py" ]; then
  cp "$SRC/scripts/seo-probe.py" "$DEST/scripts/"
  chmod +x "$DEST/scripts/seo-probe.py"
else
  say "warning: this ref ($REF) predates scripts/seo-probe.py -- live-site audits will"
  say "         have no evidence collector. Install from a ref that includes it."
fi

# ------------------------------------------------------------------- verify
agents=$(ls "$DEST"/agents/seo-*.md 2>/dev/null | wc -l | tr -d ' ')
cmds=$(ls "$DEST"/commands/{seo-audit,seo-pipeline,aeo-plan}.md 2>/dev/null | wc -l | tr -d ' ')
refs=$(ls "$DEST/skills/$SKILL/references"/*.md 2>/dev/null | wc -l | tr -d ' ')
[ -f "$DEST/skills/$SKILL/SKILL.md" ] || die "verification failed: SKILL.md missing after copy"
[ "$agents" -ge 10 ] || die "verification failed: expected 10 agents, found $agents"
[ "$cmds" -eq 3 ] || die "verification failed: expected 3 commands, found $cmds"
[ "$refs" -ge 13 ] || die "verification failed: expected 13+ references, found $refs"
say ""
say "Installed into $DEST"
say "  skill      1  ($SKILL, $refs references)"
say "  agents     $agents"
say "  commands   $cmds  (/seo-pipeline, /seo-audit, /aeo-plan)"
say "  scripts    1  (seo-probe.py)"
say ""
ready_rc=0; readiness "$DEST/scripts/seo-probe.py" || ready_rc=$?
if [ "$SCOPE" = "project" ]; then
  finish "$ready_rc" "Commit .claude/ so every session on this repo -- CLI, desktop, or web -- picks it up."
else
  finish "$ready_rc" "Installed for your user account -- available in every project."
fi
