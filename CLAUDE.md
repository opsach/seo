# Claude Operating Instructions

> This repository is the **SEO & GEO Consultant plugin for Claude Code** — a
> documentation/skill knowledge pack. There is no application code, build, or
> test suite here. The product is the content under `skills/seo-geo-consultant/`.

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
- **Keep README, run-guide, and `.claude-plugin/` manifests consistent** —
  install commands, file lists, and counts must match reality.
- **No project-specific leftovers** — examples must use placeholder brands
  (`YourBrand`, `[Product]`), not real client or third-party product names.

---

## Non-Negotiables

- Temporary fixes are future bugs with extra steps
- Never fail silently
- Read `tasks/lessons.md` first. Every session.
