**Toolkit root:** `${CLAUDE_PLUGIN_ROOT}`

The line above already holds the root -- Claude Code writes it for a plugin install,
the installer writes it for a file install. Read it; do not compute it. Never
`echo`/`printenv` CLAUDE_PLUGIN_ROOT: it is not a shell variable, and the command is
refused.

- **An absolute path, or `.claude`** (relative to the project root, where every Bash
  call starts): run the tools as `python3 <root>/scripts/seo-scan.py …` and
  `python3 <root>/scripts/seo-probe.py …`. Both are pre-approved, so do not `ls` the
  directory first. For the Read tool, make a relative root absolute with the
  project's path.
- **Still the unexpanded placeholder** (a dollar sign and braces -- the files were
  copied by hand, not by the installer): run this once; Claude Code asks to approve
  it, because it reads environment variables:

```bash
for d in "$CLAUDE_PLUGIN_ROOT" .claude ../.claude "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" "$HOME/.claude" $(ls -dt "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/plugins/cache/*/seo-geo-consultant/*/ "$HOME"/.claude/plugins/cache/*/seo-geo-consultant/*/ 2>/dev/null); do
  [ -n "$d" ] && [ -d "$d/skills/seo-geo-consultant/references" ] || continue
  k=$(cd "$d" && pwd)
  echo "REFERENCES: $k/skills/seo-geo-consultant/references"
  echo "PROBE:      $k/scripts/seo-probe.py"
  echo "SCAN:       $k/scripts/seo-scan.py"
  exit 0
done
echo "PLUGIN FILES NOT FOUND -- reinstall: curl -fsSL https://raw.githubusercontent.com/opsach/seo/main/scripts/install.sh | bash" >&2; exit 1
```

From the root: `<REFERENCES>` is `<root>/skills/seo-geo-consultant/references`,
`<PROBE>` is `<root>/scripts/seo-probe.py`, `<SCAN>` is `<root>/scripts/seo-scan.py`.
Write the path out literally in every command -- shell variables do not survive
between tool calls, and a literal path is what the pre-approved
`python3 *seo-scan.py *` rule matches. `PLUGIN FILES NOT FOUND` means stop and report
it; never work from memory instead.
