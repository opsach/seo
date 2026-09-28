# Claude Operating Instructions

> This repository is the **SEO & GEO Consultant plugin for Claude Code** — a
> skill knowledge pack plus stdlib-only Python tooling. The product is the content
> under `skills/seo-geo-consultant/`, the agents and commands, and `scripts/`.
> There is no build; the test suite is `python3 scripts/verify.py`.

---

## Startup Sequence (Every Session)

1. Read `tasks/lessons.md` — absorb all active rules
2. Read `tasks/todo.md` — find where the last session ended
3. Identify active mode — default for this repo: **Light** (docs-only, no production users)
4. Then begin work

---

## What Lives Where

| Path | Purpose |
|---|---|
| `skills/seo-geo-consultant/SKILL.md` | The skill entry point — triggers, workflows, core principles |
| `skills/seo-geo-consultant/references/` | Deep-dive references loaded on demand (audit checklist, GEO playbook, Next.js code, schema templates, AEO measurement, evidence policy, report template, run guide, live-site audit) |
| `.claude-plugin/` | Plugin + marketplace manifests — keep in sync with README install instructions |
| `agents/`, `commands/` | The 10 department subagents and the 4 slash commands (`/seo-fix`, `/seo-audit`, `/seo-pipeline`, `/aeo-plan`) |
| `scripts/` | `seo-probe.py` (live URL evidence), `seo-scan.py` (codebase/rendered scoring + fix plan), `install.sh`, `doctor.sh`, `verify.py` (the test suite), `test-scan.py` (scanner regression tests), `sync-shared.py` (regenerates shared blocks from `scripts/shared/`) |
| `tests/fixtures/` | Small projects with known defects (and two correct ones that must score 10.0) that pin the scanner's verdicts |
| `.claude/` | Generated mirror for file installs — regenerate with `./scripts/install.sh --target .`, never edit by hand |
| `docs/doctrine/` | General agent execution doctrine (build/test/ship/secure). Written to be copied into application projects; most of it does not apply to this docs-only repo. `AGENT_OPS_PROSPECT_INTEL.md` and `CHATGPT_PROJECT_INSTRUCTIONS.md` are overlays for a *different* project (Prospect Intel) kept only as templates — never treat them as rules for this repo. |
| `tasks/` | Active task plan and lessons log |

---

## Editing Rules for This Repo

- **Every factual/numeric claim added to the skill must follow
  `skills/seo-geo-consultant/references/evidence-policy.md`** — tag confidence
  (Standards-based / Widely observed / Experimental) and give source + date for
  benchmark-style numbers.
- **Keep SKILL.md lean** — detailed material goes in `references/`, SKILL.md
  only orchestrates. Update SKILL.md's Reference Files list when adding a reference.
- **Shared blocks are generated** — the locate-the-toolkit block lives in
  `scripts/shared/toolkit.md`; edit it there and run `python3 scripts/sync-shared.py`.
- **A new scanner check needs three things** — a registry entry in `seo-scan.py`, a
  `<a name="id">` recipe in `fix-playbook.md`, and a fixture assertion in
  `scripts/test-scan.py`. `verify.py` enforces the first two pairings.
- **Keep README, run-guide, and `.claude-plugin/` manifests consistent** —
  install commands, file lists, and counts must match reality.
- **No project-specific leftovers** — examples must use placeholder brands
  (`YourBrand`, `[Product]`), not real client or third-party product names.

---

## Non-Negotiables

- Temporary fixes are future bugs with extra steps
- Never fail silently
- Read `tasks/lessons.md` first. Every session.
