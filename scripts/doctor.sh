#!/usr/bin/env bash
#
# Diagnose an install of the SEO & GEO Consultant plugin and name the fix.
#
# Run from anywhere:
#   curl -fsSL https://raw.githubusercontent.com/opsach/seo/main/scripts/doctor.sh | bash
#
# Or from a clone:
#   ./scripts/doctor.sh
#
# Every check that fails prints the exact command that repairs it. Exit code is
# 0 when the plugin is usable, 1 when something needs fixing.

set -uo pipefail   # deliberately NOT -e: a failing probe is a finding, not a crash

SKILL="seo-geo-consultant"
MARKET="opsach-seo"
REPO="opsach/seo"
RAW="https://raw.githubusercontent.com/opsach/seo/main/scripts/install.sh"

# One canonical repair string. Every file-level defect below has the same cure --
# reinstalling replaces the tree wholesale -- so they must dedupe to one plan line.
REINSTALL="curl -fsSL $RAW | bash -s -- --user   (replaces a broken or partial install)"

problems=0
blockers=0
fix_lines=()

pass() { printf '  ok    %s\n' "$1"; }
info() { printf '        %s\n' "$1"; }
warn() { printf '  warn  %s\n' "$1"; problems=$((problems + 1)); }
fail() { printf '  FAIL  %s\n' "$1"; problems=$((problems + 1)); }
blocker() { printf '  FAIL  %s\n' "$1"; problems=$((problems + 1)); blockers=$((blockers + 1)); }
# Several checks can fail for one underlying cause (a half-copied install trips
# agents, commands and references at once). Print the remedy against each finding,
# but list it only once in the final plan -- a plan that repeats "reinstall" five
# times reads as five separate jobs.
remedy() {
  printf '        -> %s\n' "$1"
  case "${fix_seen:-}" in
    *"<$1>"*) return ;;
  esac
  fix_seen="${fix_seen:-}<$1>"
  fix_lines[${#fix_lines[@]}]="$1"
}

echo
echo "SEO & GEO Consultant -- install doctor"
echo "======================================"

# ------------------------------------------------------------- 1. environment
echo
echo "1. Environment"
pass "os: $(uname -s 2>/dev/null || echo unknown) $(uname -m 2>/dev/null || true)"
pass "shell: ${BASH_VERSION:-unknown bash}"
pass "cwd: $PWD"

# ----------------------------------------------------------- 2. prerequisites
echo
echo "2. Prerequisites"

if command -v git >/dev/null 2>&1; then
  pass "git present ($(git --version 2>/dev/null | head -1))"
else
  blocker "git not found"
  remedy "install git -- https://git-scm.com/downloads (marketplace installs clone over git)"
fi

if command -v python3 >/dev/null 2>&1; then
  pass "python3 present ($(python3 --version 2>&1))"
elif command -v python >/dev/null 2>&1 && python -c 'import sys; sys.exit(0 if sys.version_info[0]==3 else 1)' 2>/dev/null; then
  warn "python3 not on PATH, but 'python' is Python 3"
  remedy "live-site audits call 'python3' by name -- alias it or install python3 from python.org"
else
  warn "python3 not found"
  remedy "install Python 3 -- https://www.python.org/downloads (needed only for live-site audits)"
fi

if command -v curl >/dev/null 2>&1; then
  pass "curl present"
else
  warn "curl not found (only needed for the one-line installer)"
fi

# --------------------------------------------------------- 3. claude code cli
echo
echo "3. Claude Code CLI"

CLAUDE_OK=0
if command -v claude >/dev/null 2>&1; then
  CLAUDE_RAW="$(claude --version 2>&1 | head -1)"
  CLAUDE_VER="$(printf '%s' "$CLAUDE_RAW" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
  MAJOR="${CLAUDE_VER%%.*}"
  if [ -z "$CLAUDE_VER" ]; then
    warn "claude found but version unreadable: $CLAUDE_RAW"
  elif [ "${MAJOR:-0}" -lt 2 ] 2>/dev/null; then
    blocker "claude $CLAUDE_VER is too old -- 'claude plugin' needs 2.x"
    remedy "npm install -g @anthropic-ai/claude-code@latest"
  else
    pass "claude $CLAUDE_VER at $(command -v claude)"
    CLAUDE_OK=1
  fi
else
  warn "claude CLI not on PATH"
  info "not fatal: the plugin also installs as plain files (section 5)"
  remedy "npm install -g @anthropic-ai/claude-code   (then reopen your terminal so PATH updates)"
fi

# ---------------------------------------------------- 4. marketplace + plugin
echo
echo "4. Marketplace and plugin registration"

if [ "$CLAUDE_OK" = 1 ]; then
  MKT="$(claude plugin marketplace list 2>&1)"
  if printf '%s' "$MKT" | grep -q "$MARKET"; then
    pass "marketplace '$MARKET' is registered"

    PLG="$(claude plugin list 2>&1)"
    if printf '%s' "$PLG" | grep -q "$SKILL"; then
      pass "plugin '$SKILL' is installed"
      if printf '%s' "$PLG" | grep -qi "disabled"; then
        fail "plugin appears disabled"
        remedy "claude plugin enable $SKILL"
      fi
    else
      fail "plugin '$SKILL' is NOT installed"
      remedy "claude plugin install $SKILL@$MARKET"
    fi
  else
    fail "marketplace '$MARKET' is NOT registered"
    info "installing before adding gives a misleading error that tells you to run"
    info "'marketplace update' -- that is wrong; you need 'marketplace add' first"
    remedy "claude plugin marketplace add $REPO"
    remedy "claude plugin install $SKILL@$MARKET   (in that order)"
  fi
else
  info "skipped -- no usable claude CLI"
fi

# ----------------------------------------------------------- 5. files on disk
echo
echo "5. Installed files"

FOUND=""
for d in "${CLAUDE_PLUGIN_ROOT:-}" "$PWD/.claude" "$HOME/.claude"; do
  [ -n "$d" ] && [ -f "$d/skills/$SKILL/SKILL.md" ] && { FOUND="$d"; break; }
done
if [ -z "$FOUND" ] && [ -d "$HOME/.claude/plugins/cache" ]; then
  CACHED="$(find "$HOME/.claude/plugins/cache" -type f -name SKILL.md -path "*$SKILL*" 2>/dev/null | head -1)"
  [ -n "$CACHED" ] && FOUND="$(cd "$(dirname "$CACHED")/../.." && pwd)"
fi

if [ -n "$FOUND" ]; then
  pass "found at $FOUND"
  agents=$(ls "$FOUND"/agents/seo-*.md 2>/dev/null | wc -l | tr -d ' ')
  cmds=$(ls "$FOUND"/commands/*.md 2>/dev/null | wc -l | tr -d ' ')
  refs=$(ls "$FOUND/skills/$SKILL/references"/*.md 2>/dev/null | wc -l | tr -d ' ')

  [ "${agents:-0}" -ge 10 ] && pass "agents: $agents (expected 10)" || {
    fail "agents: ${agents:-0} (expected 10)"
    remedy "$REINSTALL"; }
  [ "${cmds:-0}" -ge 3 ] && pass "commands: $cmds (expected 3)" || {
    fail "commands: ${cmds:-0} (expected 3)"
    remedy "$REINSTALL"; }
  [ "${refs:-0}" -ge 13 ] && pass "references: $refs (expected 13+)" || {
    fail "references: ${refs:-0} (expected 13+)"
    remedy "$REINSTALL"; }

  if [ -d "$FOUND/skills/$SKILL/$SKILL" ]; then
    fail "nested install detected: $FOUND/skills/$SKILL/$SKILL"
    remedy "$REINSTALL"
  fi

  PROBE=""
  for p in "$FOUND/scripts/seo-probe.py" "$FOUND/../scripts/seo-probe.py"; do
    [ -f "$p" ] && { PROBE="$p"; break; }
  done
  if [ -n "$PROBE" ]; then
    pass "evidence collector: $PROBE"
  else
    warn "seo-probe.py not found -- live-site audits have no evidence collector"
    remedy "$REINSTALL"
  fi
else
  blocker "no installed copy found in CLAUDE_PLUGIN_ROOT, ./.claude, ~/.claude, or the plugin cache"
  remedy "curl -fsSL $RAW | bash -s -- --user   (installs without the plugin system)"
fi

# --------------------------------------------------------------- 6. network
echo
echo "6. Network reachability"
if command -v git >/dev/null 2>&1; then
  if git ls-remote "https://github.com/$REPO.git" HEAD >/dev/null 2>&1; then
    pass "github.com/$REPO reachable over git"
  else
    blocker "cannot reach github.com/$REPO over git"
    remedy "check proxy/VPN/firewall -- marketplace installs and the installer both clone from GitHub"
  fi
else
  info "skipped -- git not installed"
fi

# --------------------------------------------------------------- 7. verdict
echo
echo "======================================"
if [ "$problems" -eq 0 ]; then
  echo "VERDICT: healthy. Start a new Claude Code session and run /seo-audit"
  echo
  exit 0
fi

if [ "$blockers" -gt 0 ]; then
  echo "VERDICT: $problems problem(s), $blockers blocking."
else
  echo "VERDICT: $problems problem(s)."
fi
echo
# A warn can raise a problem without a matching remedy, so an empty plan is a
# legitimate state -- do not index an empty array under `set -u`.
if [ "${#fix_lines[@]}" -gt 0 ]; then
  echo "Run these in order:"
  echo
  n=1
  for line in "${fix_lines[@]}"; do
    printf '  %d. %s\n' "$n" "$line"
    n=$((n + 1))
  done
  echo
fi
echo "Components load at session start -- after fixing, quit Claude Code and reopen it."
echo "Still stuck? Open an issue at https://github.com/$REPO/issues and paste this output."
echo
exit 1
