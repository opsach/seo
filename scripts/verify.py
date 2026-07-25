#!/usr/bin/env python3
"""
verify.py -- self-check for the seo-geo-consultant plugin repo.

This repo ships no application code, so its bugs are packaging bugs: a manifest
that does not parse, an agent whose frontmatter name does not match its filename,
a reference file listed in SKILL.md that does not exist, a README count that drifted
from reality, or a `.claude/` mirror that fell out of sync with source. Every one of
those is invisible until a user tries to install. This script catches all of them.

Run from the repo root:  python3 scripts/verify.py
Exit code 0 = clean, 1 = failures.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = "seo-geo-consultant"
EXPECTED_COMMANDS = {"seo-audit.md", "seo-pipeline.md", "aeo-plan.md"}

failures: list[str] = []
warnings: list[str] = []
checks = 0


def check(ok, label, detail=""):
    global checks
    checks += 1
    if ok:
        print(f"  ok    {label}")
    else:
        print(f"  FAIL  {label}" + (f" -- {detail}" if detail else ""))
        failures.append(label)
    return ok


def warn(label, detail=""):
    print(f"  warn  {label}" + (f" -- {detail}" if detail else ""))
    warnings.append(label)


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return fh.read()


def frontmatter(text, path):
    """Minimal YAML frontmatter reader: top-level `key: value` pairs only."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block, out, key = text[3:end], {}, None
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if m:
            key = m.group(1)
            out[key] = m.group(2).strip()
        elif key and (line.startswith(" ") or line.startswith("\t")):
            out[key] = (out[key] + " " + line.strip()).strip()
        else:
            warnings.append(f"{path}: unparsed frontmatter line {line[:40]!r}")
    return out


# ---------------------------------------------------------------- manifests
print("\nManifests")
plugin = marketplace = None
try:
    plugin = json.loads(read(".claude-plugin/plugin.json"))
    check(True, "plugin.json parses")
except Exception as exc:  # noqa: BLE001
    check(False, "plugin.json parses", str(exc))
try:
    marketplace = json.loads(read(".claude-plugin/marketplace.json"))
    check(True, "marketplace.json parses")
except Exception as exc:  # noqa: BLE001
    check(False, "marketplace.json parses", str(exc))

if plugin and marketplace:
    names = [p.get("name") for p in marketplace.get("plugins", [])]
    check(plugin.get("name") in names,
          "marketplace lists the plugin by name",
          f"plugin.json name={plugin.get('name')!r}, marketplace names={names}")
    check(bool(re.match(r"^\d+\.\d+\.\d+$", plugin.get("version", ""))),
          "plugin version is semver", plugin.get("version", "(missing)"))
    check(bool(marketplace.get("metadata", {}).get("description")),
          "marketplace has a description")

# ------------------------------------------------------------------- skill
print("\nSkill")
skill_path = f"skills/{SKILL}/SKILL.md"
check(os.path.isfile(os.path.join(ROOT, skill_path)), f"{skill_path} exists")
skill_text = read(skill_path)
fm = frontmatter(skill_text, skill_path)
check(fm is not None, "SKILL.md has frontmatter")
if fm:
    check(fm.get("name") == SKILL, "SKILL.md name matches directory", fm.get("name", "?"))
    check(len(fm.get("description", "")) > 80, "SKILL.md has a substantial description")

ref_dir = os.path.join(ROOT, "skills", SKILL, "references")
actual_refs = sorted(f for f in os.listdir(ref_dir) if f.endswith(".md"))
linked_refs = sorted(set(re.findall(r"references/([a-z0-9-]+\.md)", skill_text)))
missing = [r for r in linked_refs if r not in actual_refs]
unlisted = [r for r in actual_refs if r not in linked_refs]
check(not missing, "every reference SKILL.md links to exists", ", ".join(missing))
check(not unlisted, "every reference file is listed in SKILL.md", ", ".join(unlisted))

# ------------------------------------------------------------------ agents
print("\nAgents")
agent_dir = os.path.join(ROOT, "agents")
agent_files = sorted(f for f in os.listdir(agent_dir) if f.endswith(".md"))
check(len(agent_files) == 10, "10 agent files present", str(len(agent_files)))
agent_names = set()
for f in agent_files:
    text = read(f"agents/{f}")
    afm = frontmatter(text, f"agents/{f}")
    if not check(afm is not None, f"agents/{f} has frontmatter"):
        continue
    agent_names.add(afm.get("name", ""))
    check(afm.get("name") == f[:-3], f"agents/{f} name matches filename", afm.get("name", "?"))
    check(bool(afm.get("description")), f"agents/{f} has a description")
    check(bool(afm.get("tools")), f"agents/{f} declares tools")

# ---------------------------------------------------------------- commands
print("\nCommands")
cmd_dir = os.path.join(ROOT, "commands")
cmd_files = sorted(f for f in os.listdir(cmd_dir) if f.endswith(".md"))
check(set(cmd_files) == EXPECTED_COMMANDS, "expected command set",
      f"found {sorted(cmd_files)}")
for f in cmd_files:
    cfm = frontmatter(read(f"commands/{f}"), f"commands/{f}")
    check(cfm is not None and bool(cfm.get("description")),
          f"commands/{f} has a description")

# ------------------------------------------------- shared resolver / evidence
print("\nShared blocks")
RESOLVER_MARK = 'for d in "$CLAUDE_PLUGIN_ROOT" .claude ../.claude "$HOME/.claude"'
FETCHERS = {"seo-discovery", "seo-tech-auditor", "seo-onpage-auditor",
            "seo-schema-auditor", "seo-performance-auditor", "seo-geo-auditor",
            "seo-competitor-analyst"}
no_resolver = [f for f in agent_files if RESOLVER_MARK not in read(f"agents/{f}")]
check(not no_resolver, "every agent carries the file resolver", ", ".join(no_resolver))
no_rules = [f for f in sorted(FETCHERS)
            if "Evidence Rules (non-negotiable)" not in read(f"agents/{f}.md")]
check(not no_rules, "every fetching agent carries the evidence rules", ", ".join(no_rules))

# The resolver prints absolute paths precisely because shell variables do not
# survive between tool calls; a $SEO_KIT reference means that lesson regressed.
stale = []
for rel in ([f"agents/{f}" for f in agent_files] + [f"commands/{f}" for f in cmd_files]
            + [skill_path] + [f"skills/{SKILL}/references/{r}" for r in actual_refs]):
    if "$SEO_KIT" in read(rel):
        stale.append(rel)
check(not stale, "no file relies on a shell variable surviving between tool calls",
      ", ".join(stale))

pipeline = read("commands/seo-pipeline.md")
referenced = set(re.findall(r"\*\*(seo-[a-z-]+)\*\*", pipeline))
unknown = sorted(referenced - agent_names)
check(not unknown, "every agent named in /seo-pipeline exists", ", ".join(unknown))

# ------------------------------------------------------------------ README
print("\nREADME consistency")
readme = read("README.md")
readme_refs = sorted(set(re.findall(r"`([a-z0-9-]+\.md)`", readme)))
# Files the plugin *writes* rather than ships, plus its own docs.
ARTIFACTS = {"SKILL.md", "seo-audit-report.md", "CLAUDE.md", "AGENTS.md", "README.md"}
readme_missing = [r for r in readme_refs
                  if r not in actual_refs and r not in cmd_files and r not in ARTIFACTS]
check(not readme_missing, "README names no reference file that is missing",
      ", ".join(readme_missing))
undocumented = [r for r in actual_refs if r not in readme_refs]
if undocumented:
    warn("references not mentioned in README", ", ".join(undocumented))
for agent in sorted(agent_names):
    if agent and agent not in readme:
        warn(f"agent {agent} not documented in README")

# ----------------------------------------------------------------- scripts
print("\nScripts")
for rel in ("scripts/seo-probe.py", "scripts/verify.py"):
    path = os.path.join(ROOT, rel)
    ok = subprocess.run([sys.executable, "-m", "py_compile", path],
                        capture_output=True).returncode == 0
    check(ok, f"{rel} compiles")
    check(os.access(path, os.X_OK), f"{rel} is executable")
for rel in ("scripts/install.sh", "scripts/doctor.sh"):
    sh = os.path.join(ROOT, rel)
    check(subprocess.run(["bash", "-n", sh], capture_output=True).returncode == 0,
          f"{rel} parses")
    check(os.access(sh, os.X_OK), f"{rel} is executable")

# doctor.sh is the failure path for installation itself, so its own advice must be
# runnable: the marketplace and plugin names it prints have to match the manifests,
# and it must exit non-zero when it finds problems (a doctor that always exits 0
# reports "healthy" to CI and to the user alike).
doctor = read("scripts/doctor.sh")
if marketplace and plugin:
    check(f'MARKET="{marketplace.get("name")}"' in doctor,
          "doctor.sh marketplace name matches marketplace.json",
          marketplace.get("name", "?"))
    check(f'SKILL="{plugin.get("name")}"' in doctor,
          "doctor.sh plugin name matches plugin.json", plugin.get("name", "?"))
check("exit 1" in doctor, "doctor.sh exits non-zero on problems")
check("raw.githubusercontent.com/opsach/seo/main/scripts/install.sh" in doctor,
      "doctor.sh points at the published installer URL")

# ------------------------------------------------------- .claude mirror sync
print("\n.claude/ mirror")
mirror = os.path.join(ROOT, ".claude")
if not os.path.isdir(mirror):
    warn(".claude/ mirror absent (fine if intentionally not committed)")
else:
    pairs = []
    for f in agent_files:
        pairs.append((f"agents/{f}", f".claude/agents/{f}"))
    for f in cmd_files:
        pairs.append((f"commands/{f}", f".claude/commands/{f}"))
    for dirpath, _, files in os.walk(os.path.join(ROOT, "skills", SKILL)):
        for f in files:
            src = os.path.relpath(os.path.join(dirpath, f), ROOT)
            pairs.append((src, os.path.join(".claude", src)))
    pairs.append(("scripts/seo-probe.py", ".claude/scripts/seo-probe.py"))

    drift = []
    for src, dst in pairs:
        dst_abs = os.path.join(ROOT, dst)
        if not os.path.isfile(dst_abs):
            drift.append(f"{dst} missing")
        elif read(src) != read(dst):
            drift.append(f"{dst} differs from {src}")
    check(not drift, ".claude/ mirror matches source",
          "; ".join(drift[:6]) + (" …" if len(drift) > 6 else ""))
    stray = []
    for sub in ("agents", "commands"):
        d = os.path.join(mirror, sub)
        if os.path.isdir(d):
            known = agent_files if sub == "agents" else cmd_files
            stray += [f"{sub}/{f}" for f in os.listdir(d)
                      if f.endswith(".md") and f not in known]
    check(not stray, ".claude/ mirror has no orphaned files", ", ".join(stray))

# ------------------------------------------------------------------ summary
print(f"\n{checks} checks, {len(failures)} failed, {len(warnings)} warnings")
if failures:
    print("\nFailures:")
    for f in failures:
        print(f"  - {f}")
sys.exit(1 if failures else 0)
