# tasks/todo.md

> Active task plan. Updated every session. Never deleted — append only.

---

## Active Task

**Task:**
**Mode:** Standard / Light / Incident
**Classified as:** Trivial / Non-trivial / Complex
**Session started:**

### Plan
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

### Risk Flags
| Domain | Flag | Resolution |
|---|---|---|
| Performance | | |
| Security | | |
| Backward Compatibility | | |
| Migration | | |
| Test Coverage | | |

### Ambiguities Resolved
- [assumption made and why]

---

## Verification
- [ ] Tests pass
- [ ] Logs clean
- [ ] Behaviour confirmed beyond tests
- [ ] Risk flags closed
- [ ] No adjacent regressions
- [ ] Staff engineer bar met

### Review
**What was done:**
**What was verified:**
**Noted for follow-up:**

---

## Backlog
> Items noticed but out of scope. Do not action without explicit instruction.

- [ ]
- [ ]

---

## Completed Tasks
> Append completed tasks below with date. Do not delete.

### [2026-07-10] Product audit + packaging/content fixes (Mode: Light)

**What was done:**
- Added `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` so the plugin is actually installable from `opsach/seo`
- Fixed install instructions in README and run-guide (previously pointed to the upstream `AndreasH96/seo-geo-consultant` repo with a nonexistent `claude /install-plugin` command)
- Removed upstream project leftovers from SKILL.md (Skyblobs example, data-architecture "Edge Types" section)
- Fixed invalid robots token `GoogleExtended` -> `Google-Extended`; added user-initiated AI fetchers (ChatGPT-User, Claude-User, Perplexity-User)
- Applied the repo's own evidence policy to unsourced stats in geo-optimization.md (confidence tags, softened vendor numbers)
- Added Google 2023 deprecation notes for FAQ/HowTo rich results + fake-aggregateRating warning in schema-templates.md
- NEW: LocalBusiness/Restaurant schema template + Local SEO checklist section
- NEW: `references/live-site-audit.md` + workflow mode 5 (URL-only audits for clients/prospects)
- Moved unrelated Prospect Intel / generic ops doctrine to `docs/doctrine/`; rewrote CLAUDE.md and AGENTS.md for this repo (paths `tasks/lessons.md`, `tasks/todo.md` now real)
- Completed SKILL.md Reference Files list (was missing 4 of the reference files)

**Noted for follow-up (backlog):**
- [ ] Test `/plugin marketplace add opsach/seo` end-to-end after merge to main (marketplace pulls from the default branch)
- [x] README promises react-helmet-async guidance for Vite/CRA -- no reference file covers it yet; add one or trim the claim (done 2026-07-10: `react-spa-implementation.md`)
- [x] Consider a WordPress/Shopify implementation reference (many agency clients are not Next.js) (done 2026-07-10: `cms-implementation.md`)
- [ ] Decide whether `docs/doctrine/` (Prospect Intel templates) belongs in this repo at all

### [2026-07-14] Multi-agent SEO department pipeline (Mode: Light)

**What was done:**
- NEW `agents/` directory with 10 department subagents sharing one findings contract
  (ID prefix, severity, evidence citation, impact/effort 1-5, confidence tier):
  `seo-discovery` (intake brief), `seo-tech-auditor`, `seo-onpage-auditor`,
  `seo-schema-auditor`, `seo-performance-auditor`, `seo-geo-auditor`,
  `seo-content-strategist`, `seo-competitor-analyst`, `seo-roadmap-director`
  (writes `seo-audit-report.md` per audit-report-template), `seo-fix-engineer`
  (only agent with edit rights)
- NEW `commands/seo-pipeline.md` -- 5-stage orchestration: discovery -> parallel
  audits -> strategy -> boardroom merge -> approved implementation
- All auditor agents are read-only, scoped to their audit-checklist sections, and
  bound to evidence-policy.md confidence tiers; department scopes are mutually
  exclusive with handoff notes for cross-department observations
- README: pipeline bullet, agent table, `/seo-pipeline` in commands list
- run-guide: new section 5c (pipeline walkthrough), slash-command list updated
- plugin.json version 1.1.0 -> 1.2.0 (agents/ auto-discovered; no manifest key needed)

**What was verified:**
- Agent scopes map 1:1 onto audit-checklist.md sections with no orphan sections
  (1/7/11 tech, 2/4 on-page, 3/10-schema schema, 1-perf performance, 5/8 GEO,
  9 owned by roadmap-director's quality gates)
- README counts, command lists, and run-guide stay consistent with actual files
- Output contracts match audit-report-template.md fields (severity, impact/effort,
  priority score = impact/effort, confidence tiers)

**Noted for follow-up (backlog):**
- [ ] Dry-run `/seo-pipeline` against a real site after merge to confirm
  `${CLAUDE_PLUGIN_ROOT}` expansion inside agent files across Claude Code versions

### [2026-07-10] Round 2: close the strategic gaps (Mode: Light)

**What was done:**
- NEW `references/react-spa-implementation.md` -- Vite/CRA SEO: rendering reality check (AI crawlers don't execute JS), react-helmet-async component, prerendering ladder, SPA audit traps (soft 404s, hash routing)
- NEW `references/cms-implementation.md` -- WordPress (plugin setup, thin archives, attachment pages, schema duplication), Shopify (robots.txt.liquid, duplicate product URLs, app bloat), site builders, cross-platform verification
- NEW `references/content-strategy.md` -- search intent mapping, keyword research from owned data outward, topic clusters, content brief template, internal linking architecture, cannibalization consolidation
- NEW audit-checklist section 11: Site Migrations (redirect maps, staging noindex, GSC change of address, post-launch monitoring)
- NEW slash commands: `commands/seo-audit.md`, `commands/aeo-plan.md`
- SKILL.md: broadened trigger description to all stacks, stack-routing in mode 3, new mode 6 (Keyword & Content Strategy), reference list updated
- README/run-guide updated for all of the above; plugin version 1.0.0 -> 1.1.0

**What was verified:**
- All new numeric/behavioral claims hedged or confidence-tagged per evidence-policy.md
- README counts, mode numbers, file lists, and install commands consistent with actual files

