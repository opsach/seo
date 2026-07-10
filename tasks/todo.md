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
- [x] Test `/plugin marketplace add opsach/seo` end-to-end after merge to main (marketplace pulls from the default branch) (done 2026-07-10: verified on Claude Code 2.1.206 — see below)
- [x] README promises react-helmet-async guidance for Vite/CRA -- no reference file covers it yet; add one or trim the claim (done 2026-07-10: `react-spa-implementation.md`)
- [x] Consider a WordPress/Shopify implementation reference (many agency clients are not Next.js) (done 2026-07-10: `cms-implementation.md`)
- [ ] Decide whether `docs/doctrine/` (Prospect Intel templates) belongs in this repo at all

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

### [2026-07-10] End-to-end install test: `/plugin marketplace add opsach/seo` (Mode: Light)

**What was done:**
- Ran the full install path on Claude Code CLI 2.1.206 against the live GitHub default branch (main)

**What was verified:**
- `claude plugin marketplace add opsach/seo` — clones via HTTPS, marketplace validates, added as `opsach-seo`
- `claude plugin install seo-geo-consultant@opsach-seo` — installs v1.1.0, status enabled
- Installed cache contains `skills/seo-geo-consultant/SKILL.md` + all 12 references, and both slash commands (`commands/seo-audit.md`, `commands/aeo-plan.md`) with valid frontmatter

**Noted for follow-up (backlog):**
- [ ] Because `plugin.json` source is `./`, the *entire repo* ships with the plugin — installers receive `tasks/` (internal todo/lessons logs), `docs/doctrine/` (unrelated Prospect Intel templates), CLAUDE.md, and AGENTS.md. Functionally harmless (only `skills/` and `commands/` are loaded) but bloats the install and exposes internal working notes. Consider restructuring the plugin into a subdirectory or pruning what ships. Ties into the existing "does `docs/doctrine/` belong here" item.

