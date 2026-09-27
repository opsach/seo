**Toolkit root:** `${CLAUDE_PLUGIN_ROOT}`

If the line above is an absolute path, the plugin is installed as a Claude Code
plugin and that path is the toolkit root. If it still reads literally
`${CLAUDE_PLUGIN_ROOT}`, the plugin was installed as files -- run this once to find
the root:

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
Write these absolute paths out literally in every command -- shell variables do not
survive between tool calls. `PLUGIN FILES NOT FOUND` means stop and report it; never
work from memory instead.
