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
- [ ] README promises react-helmet-async guidance for Vite/CRA -- no reference file covers it yet; add one or trim the claim
- [ ] Consider a WordPress/Shopify implementation reference (many agency clients are not Next.js)
- [ ] Decide whether `docs/doctrine/` (Prospect Intel templates) belongs in this repo at all

