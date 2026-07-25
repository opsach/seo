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

### [2026-07-25] Seamless install + run in Claude Code CLI (Mode: Light)

**Requested:** "seamless run and installation in claude cli, can you fix this" — after a
live audit of fitzers.ie could not run.

**Two real defects found by executing the user's journey, not reading it:**

1. **`/seo-audit` did not exist after a plugin install.** Plugin commands are namespaced
   (`/seo-geo-consultant:seo-audit`); the bare form returns `Unknown command`. README,
   run-guide, `install.sh` and `doctor.sh` all told users to type the bare form. A
   correct install's first action failed like a broken one.
2. **`CLAUDE_CONFIG_DIR` was ignored.** `--user` wrote to `$HOME/.claude` even when the
   config dir was relocated (files land where nothing loads them, install says success),
   and `doctor.sh` searched only `$HOME/.claude`, so it declared a healthy plugin
   install "no installed copy found" and prescribed a redundant second copy.

**Built:**
- `install.sh --plugin` — one command for the CLI plugin route. Checks the CLI exists
  and is 2.x, runs `marketplace add` **then** `install` (removing the ordering trap
  whose CLI error recommends the wrong fix), confirms the result against
  `claude plugin list`, and resolves the versioned cache path rather than assuming one.
- `install.sh --check HOST` — preflights a client domain at install time, so a blocked
  host surfaces before an audit instead of halfway through one.
- `readiness()` on both routes — proves `python3` runs and `seo-probe.py` executes,
  rather than only reporting that files were copied. Return codes separate "cannot run
  audits" (exit 1) from "this host is unreachable" (exit 0, install is valid).
- Route-aware closing hints in `install.sh` and `doctor.sh`; namespacing documented in
  README (incl. a troubleshooting row) and run-guide.
- `verify.py` +18 checks: 78 → 96.
- plugin.json 1.4.0 → 1.5.0; `.claude/` mirror regenerated via `install.sh`.

**What was verified (executed on Claude Code CLI 2.1.220, not read):**
- Both install routes in isolated `CLAUDE_CONFIG_DIR`s, then a real session in each:
  skill + 3 commands + 10 agents discovered on both.
- The command each route's docs prescribe, actually typed: bare `/seo-audit` resolves
  after a file install; `/seo-geo-consultant:seo-audit` after a plugin install; the
  bare form under the plugin route reproduces `Unknown command`.
- `CLAUDE_CONFIG_DIR` both ways — files in `$HOME/.claude` with the var set are NOT
  loaded (session answered NO); the same files in the config dir ARE (answered YES).
- Doctor on a plugin-only install: was exit 1 with a wrong remedy, now exit 0 with the
  namespaced command. File-only install still exit 0 with the bare command.
- Exit-code matrix: healthy 0, blocked target 0 (install valid), broken python3 1
  ("INSTALL INCOMPLETE"). A `set -e` bug that made `return 2` kill the script was
  found and fixed by tracing, not assumed.
- Idempotency (no `skills/<skill>/<skill>` nesting), uninstall (0 leftovers),
  `--plugin` re-run, and `--plugin` with no `claude` on PATH (exit 1, named remedy).
- Full loop end to end: install → new session → `/seo-audit https://pypi.org` →
  preflight → probe → real measured values (200, TTFB 56ms, title 31 chars), matching
  a direct probe run. Closes the "dry-run against a real site" backlog item for
  `/seo-audit`.
- `python3 scripts/verify.py` 96 checks, 0 failed, 0 warnings; `claude plugin validate .`
  passes.

**Noted for follow-up:**
- [ ] `--plugin` installs from GitHub `main`, so it serves these fixes only after this
  branch merges. Until then use the file route from a clone.
- [ ] `/seo-pipeline` (multi-agent) still has no live dry-run; only `/seo-audit` does.
- [ ] The audit run prompted for Bash approval before the probe could execute. Harmless
  interactively, but worth a note in the run-guide for headless/CI use.

### [2026-07-25] Make the plugin install without problems (Mode: Light)

**Requested:** "make me this able to install into claude as a plugin without any
problems" — after a user hit repeated, unidentifiable install errors.

**Diagnosis:** the repo was not broken. `claude plugin validate .` passed, `verify.py`
passed 69/69, and a clean-room install from GitHub worked. The defect was that the
install path had no diagnosis of its own, and three real traps were undocumented:

1. `install` before `marketplace add` returns *"not found in marketplace ... try
   `marketplace update`"* — advice that cannot work, since nothing was ever added.
2. The marketplace is named `opsach-seo`, not `seo`. Using the repo path
   (`@seo`) produces the same misleading "not found / try update" error.
3. `/plugin ...` (in-session) and `claude plugin ...` (terminal) are not
   interchangeable, and a shell command typed at the `>` prompt fails silently — it
   is simply read as a message.

**Built:**
- NEW `scripts/doctor.sh` — diagnoses an install in 6 sections (environment,
  prerequisites, CLI presence/version, marketplace + plugin registration, files on
  disk across all four install locations including the plugin cache, GitHub
  reachability). Every finding carries its repair command; the closing plan is
  deduplicated and ordered. Exit 0 healthy / 1 needs work.
- `verify.py` +6 checks: doctor.sh parses, is executable, its `MARKET`/`SKILL`
  constants match the manifests, it exits non-zero, and its installer URL is the
  published one. Now 75 checks.
- README install section: order-matters callout, the in-session vs terminal
  distinction, the marketplace-name trap, doctor.sh as the first troubleshooting
  step, and 5 new table rows keyed to the **literal error strings** users see.
- run-guide.md: same corrections, plus the doctor.
- plugin.json 1.3.0 → 1.4.0; `.claude/` mirror regenerated via `install.sh`.

**What was verified (executed, not read):**
- Failure modes reproduced in an isolated `CLAUDE_CONFIG_DIR`: install-before-add,
  wrong marketplace suffix, re-add (idempotent), install without suffix (works),
  double install (idempotent).
- doctor.sh across four machine states — healthy (exit 0), bare machine with no CLI
  and no install (exit 1, 2 problems), CLI present but marketplace unregistered,
  and a deliberately nested + half-copied install (5 findings → 1 deduplicated fix).
- Prescribed repair proven end to end: broken install → `install.sh` → doctor
  reports healthy.
- Published one-liner run twice from `raw.githubusercontent.com` into a fresh
  directory: HTTP 200, correct counts, no nesting on re-run.
- `claude plugin validate .` passes; `python3 scripts/verify.py` 75 checks, 0 failed,
  0 warnings.

**Noted for follow-up:**
- [ ] `doctor.sh`'s own curl URL points at `main`; it is only fetchable that way once
  this branch merges. Until then it runs from a clone.
- [ ] doctor.sh is bash — unverified under Windows PowerShell (Git Bash works).

### [2026-07-25] Full install + run verification on Claude Code 2.1.220 (Mode: Light)

**Requested:** check the installation, paths, README, and everything needed to install
and run properly in Claude Code.

**Verified working (all executed, not read):**
- `claude plugin validate .` — passes, zero warnings.
- GitHub marketplace install in an isolated `CLAUDE_CONFIG_DIR`:
  `marketplace add opsach/seo` → `install seo-geo-consultant@opsach-seo` → `details`
  reports Skills (4), Agents (10), ~2,044 always-on tokens.
- `scripts/` ships in the plugin package: the probe resolves at
  `<cache>/seo-geo-consultant/1.3.0/scripts/seo-probe.py`.
- File resolver returns correct absolute paths in all four install layouts —
  `CLAUDE_PLUGIN_ROOT`, `~/.claude/plugins/cache/*/seo-geo-consultant/*/`, project
  `.claude/`, and `--user` `~/.claude/`.
- `install.sh`: fresh install, re-run (no `skills/<skill>/<skill>` nesting), and
  `--uninstall` (no leftovers) — all clean.
- Inventory matches the manifests: 10 agents, 3 commands, 13 references, name/filename
  agreement on every agent.
- The published `main` now carries the proxy-denial fix (PR #12): installing from
  GitHub and probing a blocked host returns exit 3, not a fabricated page audit.

**Fixed this session:**
- The resolver printed `PLUGIN FILES NOT FOUND` on stdout and **exited 0** — a silent
  failure in the one place that must be loud, since everything downstream depends on
  those paths. Now `>&2` and `exit 1`, in all 13 copies (10 agents, `seo-pipeline`,
  SKILL.md, `live-site-audit.md`). Found case still exits 0.
- README claimed `plugin details` "confirms 1 skill, 3 commands, 10 agents". CLI
  2.1.220 prints Skills (4) / Agents (10) with commands folded into Skills, so a
  correct install looked broken. README now states the real output.

**Reported, not changed (design trade-off for the owner to decide):**
- The shipped plugin is 868K, of which 344K is `.claude/` — byte-identical to
  `skills/` + `agents/` + `commands/`. Every marketplace install downloads the tree
  twice. It does not double-load (details shows 4/10, not 8/20), so this is payload
  waste only. The mirror is what makes the committed-`.claude/` and web install paths
  work, so removing it is a product decision, not a cleanup.

### [2026-07-25] Audit attempt on fitzers.ie → fixed a fabricated-findings bug (Mode: Light)

**Requested:** full audit of `http://fitzers.ie`.

**Outcome:** the audit could not run — this environment's network policy does not
allow `fitzers.ie`, so no byte of the site was ever fetched. No findings issued.

**Bug found and fixed (the real deliverable):** `seo-probe.py` mis-handled the
egress proxy's plaintext-`http://` denial. `page` parsed the 97-byte denial notice
as the client's homepage and reported MISSING title, 0 H1s, 0 words, no JSON-LD,
"NEARLY EMPTY (critical)" — at exit 0. `preflight` called the same response
"BLOCKED BY THE SITE" (exit 4), which invites the false claim that the client blocks
Googlebot and AI crawlers. Both now return exit 3 with the host and deny reason.

- `fetch()` gained `_is_proxy_denial()`, checked *before* the bot-protection
  heuristic: an `x-deny-reason` header or an allowlist-denial phrase sets
  `error_kind="policy"`, populates `error`, and clears the body so no caller can
  parse it. `https://` was already correct (refused CONNECT → URLError → policy);
  only the plaintext path was missing.
- Untracked `scripts/__pycache__/*.pyc` and added `.gitignore` — committed bytecode
  churned on every `verify.py` run.

**What was verified:**
- `preflight | page | robots | sitemap | redirects` against `http://fitzers.ie`:
  all five now exit 3 with "egress proxy refused fitzers.ie (HTTP 403,
  host_not_allowed)" and the remediation block. Pre-fix, `page` exited 0 with a
  full fabricated table.
- Regression on a reachable host (`https://pypi.org`): preflight exit 0, `page`
  returns real values (HTTP 200, TTFB 71ms, title 31 chars). No false positives.
- `redirects` shows both transports side by side — plaintext rows now match the
  already-correct CONNECT rows.
- `python3 scripts/verify.py` — 69 checks, 0 failed, 0 warnings.
- `.claude/` mirror regenerated with `./scripts/install.sh --target .`, not by hand.

**Blocked on the user:** allow `fitzers.ie` in the environment's network egress
settings and start a new session, or run the audit from Claude Code CLI, or supply
Search Console / crawl exports for owned-data mode.

### [2026-07-25] Fix install + live-site audit; add evidence toolkit (Mode: Light)

**Reported problem:** "can not install plugin, can not run on client website."

**Root causes found (all reproduced in-session):**
1. `/plugin` does not exist in Claude Code on the web — the README led with it, and
   the manual fallback was buried as "Option B" with copy-paste commands.
2. The manual install's `cp -r ... .claude/skills/` nests into
   `skills/seo-geo-consultant/seo-geo-consultant/` on a re-run under BSD/macOS `cp`
   (GNU `cp` merges instead), and the README explicitly told users to re-run it.
3. The committed `.claude/` mirror was stale — it predated the 2026-07-15 agent
   edits, so manual installs shipped older agents than the plugin route.
4. **Live audits had no failure path.** `curl` and `WebFetch` both return an opaque
   403 from the egress proxy when the environment's network policy disallows the
   target host. Nothing in the plugin recognised this, so a blocked audit would
   either die confusingly or continue on recalled facts.
5. `WebFetch` was treated as a co-equal fetch tool, but it converts pages to markdown
   through a summarising model — destroying `<title>`, meta, canonical, hreflang,
   `og:*`, JSON-LD, and status codes, i.e. everything a live audit is about.

**What was done:**
- NEW `scripts/seo-probe.py` (stdlib only): `preflight | page | robots | redirects |
  sitemap | site`. Measures status/redirect chains, TTFB, tag lengths, canonical,
  robots directives, heading outline, 120-180w GEO section band, JSON-LD types **and
  parse errors with positions**, og/twitter, hreflang, alt gaps, compression/cache,
  and a server-vs-client rendering verdict. Exit codes 3/4/5 separate "network policy
  blocked you" from "the site blocks bots" from "unreachable", each with a remedy.
- NEW `scripts/install.sh` — idempotent, verifies its own result, `--user`,
  `--target`, `--uninstall`; also regenerates the `.claude/` mirror.
- NEW `scripts/verify.py` — 69 checks: manifests, frontmatter, agent-name/filename
  match, reference-link integrity both ways, README consistency, pipeline agent
  references, script compilation, shared-block presence, and `.claude/` mirror
  equality. Caught root cause 3 on its first run.
- All 10 agents: deterministic file resolver that prints **absolute** reference and
  probe paths across plugin / project / user installs. The 7 fetching agents also
  carry non-negotiable evidence rules (preflight first, probe is the evidence source,
  WebFetch is prose-only, never report what you did not fetch) plus their own
  department-specific probe commands.
- `/seo-pipeline` gained Stage 0 (resolve toolkit + preflight target, stop on block)
  and a no-fabrication rule of engagement; `/seo-audit` gained preflight + evidence
  citation rules.
- `live-site-audit.md` rewritten around preflight → evidence pack → interpretation,
  with an exit-code table and a tool-discipline matrix.
- SKILL.md: new Toolkit section, mode 5 rewritten preflight-first.
- README: installer script is now Option A, `/plugin` marked CLI/desktop-only, plus
  an install-troubleshooting table and a "Running against a client website" section
  covering the sandbox network policy.
- plugin.json 1.2.0 → 1.3.0.

**What was verified:**
- GitHub-sourced plugin install end to end on Claude Code CLI 2.1.220
  (`marketplace add opsach/seo` → `install` → `details` shows 1 skill, 3 commands,
  10 agents). Closes the long-standing backlog item.
- `claude plugin validate` passes with zero warnings.
- Installer: fresh install, re-run (no nesting), uninstall (no leftovers).
- Resolver returns correct absolute paths in four situations: project `.claude/`,
  user `~/.claude/`, marketplace plugin cache, and `CLAUDE_PLUGIN_ROOT` set — and
  reports `PLUGIN FILES NOT FOUND` when nothing is installed.
- Probe exercised against a local fixture site covering redirect chains, soft-404,
  robots syntax errors, AI-crawler blocks, fake `lastmod`, broken JSON-LD, missing
  alt text, duplicate H1s, and an empty SPA shell — every one detected.
- Blocked-domain path confirmed against a real external host: exit 3 with the
  remediation text, no fabricated findings.
- `python3 scripts/verify.py` — 69 checks, 0 failures, 0 warnings.

**Noted for follow-up (backlog):**
- [ ] Dry-run the full `/seo-pipeline` against a real client site from an environment
  with network access — the probe and preflight are verified, the multi-agent
  orchestration on a live target is not.
- [ ] Optional headless-render diff (Chromium is available in web sessions): compare
  raw HTML against the rendered DOM to quantify what client-rendering hides.
- [ ] Dry-run once with a real GSC + Screaming Frog export in `seo-data/` to validate
  the header-detection table in `owned-data-guide.md`.

### [2026-07-15] Manual `.claude/` install fallback (Mode: Light)

**What was done:**
- `/plugin` was unavailable in the session environment, so the plugin was
  installed manually: `agents/*.md` → `.claude/agents/`, `commands/*.md` →
  `.claude/commands/`, `skills/seo-geo-consultant/` → `.claude/skills/`
- The `.claude/` copies were committed per the repo owner's stop-hook policy
  (no untracked files left behind)

**What was verified:**
- All 10 agents, 3 commands, and SKILL.md + 13 reference files copied intact
- Agent files' built-in fallback ("if `${CLAUDE_PLUGIN_ROOT}` does not
  expand, locate the installed skill") covers this non-plugin install path

**Noted for follow-up (backlog):**
- [ ] `.claude/` now duplicates the plugin source in-repo; decide whether to
  keep it in sync on future edits, replace it with a documented install
  script, or gitignore it

### [2026-07-15] Plugin packaging validation + marketplace description (Mode: Light)

**What was done:**
- Ran `claude plugin validate` (Claude Code CLI 2.1.210) on the repo: passed, with
  one warning — the marketplace manifest had no description
- Added `metadata.description` to `.claude-plugin/marketplace.json`; validation
  now passes with zero warnings
- End-to-end install test inside the session container:
  `claude plugin marketplace add <local clone>` then
  `claude plugin install seo-geo-consultant@opsach-seo` — both succeeded
- `claude plugin details seo-geo-consultant` confirms the full component
  inventory is discovered: the skill, all 3 slash commands, and all 10 agents
  (~2.0k always-on tokens)
- Test install and marketplace removed from the container after verification

**What was verified:**
- JSON manifests parse; YAML frontmatter of SKILL.md, all 10 agents, and all
  3 commands parses with expected keys (name/description/tools, argument-hint)
- README/run-guide install commands match the marketplace name (`opsach-seo`)
  and plugin name (`seo-geo-consultant`); README's 13 reference-file bullets
  match the 13 actual files in `references/`

**Noted for follow-up (backlog):**
- The container test used a local-path marketplace source; one confirmation of
  the GitHub-sourced flow (`/plugin marketplace add opsach/seo`) on a real
  machine would fully close the loop
- `${CLAUDE_PLUGIN_ROOT}` expansion and agent-name resolution inside
  `/seo-pipeline` still pending a live pipeline dry-run (existing backlog item)

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
- [x] Test `/plugin marketplace add opsach/seo` end-to-end after merge to main (marketplace pulls from the default branch) (done 2026-07-15 via CLI against a local clone of main; a GitHub-sourced install on a real machine is still worth one confirmation)
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

**Round 2 (same session): owned-data ingestion**
- NEW `references/owned-data-guide.md` -- `seo-data/` folder convention, file
  detection by headers (GSC, Screaming Frog, PSI/CrUX, analytics, backlinks),
  per-department data slices, evidence classes (data-backed / inferred /
  needs-data), graceful-degradation rules (never block on missing data, ask once
  at intake only)
- Discovery inventories data files (Data Inventory table in the brief); all seven
  analysis departments consume their slice and label every finding's evidence
  class; each report now ends with a "Data Requests (top 1-3)" section
- Roadmap director reports a Data Coverage line, consolidates data requests into
  one client-facing list, and breaks priority ties toward data-backed findings
- Pipeline Stage 1 asks the user once for exports (optional, non-blocking)
- SKILL.md reference list, README, and run-guide updated for the new reference

**Round 3 (same session): manual install path**
- User's environment has no `/plugin` command -> added Option B manual install to
  README + run-guide: copy `agents/`, `commands/`, `skills/seo-geo-consultant/`
  into the target project's `.claude/` directory (auto-loaded, works on web too)
- All 10 agents' reference-path fallback now names
  `.claude/skills/seo-geo-consultant/references/` explicitly for manual installs

**Noted for follow-up (backlog):**
- [ ] Dry-run `/seo-pipeline` against a real site after merge to confirm
  `${CLAUDE_PLUGIN_ROOT}` expansion inside agent files across Claude Code versions
- [ ] Dry-run once with a real GSC + Screaming Frog export in `seo-data/` to
  validate the header-detection table in owned-data-guide.md against real files

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

