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

# The marketplace and the installer are alternative routes to the same working state.
# The doctor must find out which one is in use before it judges registration -- when
# the marketplace check ran first it had no such evidence, failed complete installs,
# and prescribed a second copy on top of the working one.
files_at = doctor.find('echo "4. Installed files"')
market_at = doctor.find('echo "5. Marketplace and plugin registration"')
check(files_at != -1 and market_at != -1 and files_at < market_at,
      "doctor.sh inspects installed files before judging marketplace registration",
      f"files at {files_at}, marketplace at {market_at}")
check("STANDALONE_FOUND" in doctor,
      "doctor.sh gates its marketplace verdict on whether a file install exists")
check("raw.githubusercontent.com/opsach/seo/main/scripts/install.sh" in doctor,
      "doctor.sh points at the published installer URL")

# install.sh --plugin exists to remove the ordering trap that breaks most CLI
# installs, so the ordering itself must be verifiable, not merely intended: the
# marketplace has to be added before the plugin is installed, and the result has to
# be confirmed against the CLI rather than assumed from a zero exit code.
installer = read("scripts/install.sh")
check("--plugin)" in installer, "install.sh accepts --plugin")
check("--check)" in installer, "install.sh accepts --check")
if marketplace and plugin:
    check(f'MARKET="{marketplace.get("name")}"' in installer,
          "install.sh marketplace name matches marketplace.json",
          marketplace.get("name", "?"))
    check(f'SKILL="{plugin.get("name")}"' in installer,
          "install.sh plugin name matches plugin.json", plugin.get("name", "?"))
add_at = installer.find("claude plugin marketplace add")
inst_at = installer.find('claude plugin install "$SKILL@$MARKET"')
check(add_at != -1 and inst_at != -1 and add_at < inst_at,
      "install.sh adds the marketplace before installing the plugin",
      f"add at {add_at}, install at {inst_at}")
check("claude plugin list" in installer,
      "install.sh confirms the plugin against 'claude plugin list'")

# An install that copies files but cannot execute the probe would otherwise report
# success and fail later, mid-audit, as an empty or invented finding.
check("readiness()" in installer, "install.sh defines a readiness check")
check(installer.count("readiness ") >= 2,
      "install.sh runs readiness on both the plugin and file routes")
check("--help >/dev/null 2>&1" in installer,
      "install.sh proves seo-probe.py executes, not just that it exists")
# A broken runtime and an unreachable target host have opposite remedies, and only
# the first means the install is bad. Collapsing them would either hide a broken
# install behind exit 0 or condemn a good one because a firewall exists.
check("INSTALL INCOMPLETE" in installer and "exit 1" in installer,
      "install.sh exits non-zero when the install cannot run audits")
check("return 2" in installer,
      "install.sh separates a blocked target host from a broken install")

# The routes expose different command names: a plugin install namespaces them
# (`/seo-geo-consultant:seo-audit`) and the bare `/seo-audit` then returns
# "Unknown command". Printing one closing hint for both routes sends half the users
# to a command that does not exist, which reads as a failed install.
check("CMD_PREFIX" in installer,
      "install.sh varies the command hint by install route")
# Asserted against $SKILL rather than a literal name: SKILL is already checked
# against plugin.json above, so the hint stays correct if the plugin is ever renamed.
check('CMD_PREFIX="$SKILL:"' in installer,
      "install.sh namespaces the command hint for the plugin route")
check("PLUGIN_INSTALLED" in doctor,
      "doctor.sh knows which route is installed before naming a command to run")
check("$SKILL:seo-audit" in doctor,
      "doctor.sh names the namespaced command after a plugin install")
readme_txt = read("README.md")
check("Unknown command" in readme_txt,
      "README documents the namespaced-command failure mode")

# CLAUDE_CONFIG_DIR relocates the whole user-level tree that Claude Code reads --
# skills, agents, commands and the plugin cache. Writing a --user install to
# ~/.claude while it is set puts the files where nothing loads them, and searching
# only ~/.claude reports a working install as missing.
check('DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"' in installer,
      "install.sh --user honours CLAUDE_CONFIG_DIR")
check('CFG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"' in doctor,
      "doctor.sh honours CLAUDE_CONFIG_DIR")
check('"$CFG/plugins/cache"' in doctor,
      "doctor.sh searches the plugin cache under the active config dir")

# The documented way to run this script is `curl ... | bash`, where $0 is the string
# "bash". Any instruction built from $0 is then a command the user cannot run.
check('if [ -f "$0" ]' in installer,
      "install.sh only names $0 when it is a real file, not when piped from curl")
check('curl -fsSL $RAW_URL' in installer,
      "install.sh gives a runnable command when invoked through a pipe")

# `--check HOST` alone asks a question. Running it used to copy the whole plugin into
# the current directory as a side effect, which is not what the docs promise and not
# something a reachability check should ever do.
check("WANT_INSTALL" in installer,
      "install.sh distinguishes a reachability question from an install request")
check('MODE="check"' in installer,
      "install.sh has a check-only mode that installs nothing")

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
