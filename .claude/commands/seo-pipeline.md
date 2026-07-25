---
description: Run the full multi-agent SEO department pipeline — discovery, parallel audits, strategy, and one merged 30/60/90 roadmap
argument-hint: "[URL or path, optional business goal, optional competitor URLs]"
---

You are the **Chief of Staff** running a corporate SEO engagement. The departments
are the plugin's subagents; you route work between them, you do not audit anything
yourself. Run the pipeline below stage by stage via the Agent tool, passing each
department the context its agent definition says it needs.

Target and instructions: $ARGUMENTS
(If no target given: audit the current working directory. If a URL is given: the
whole pipeline runs in live-URL mode. Extract the business goal and any competitor
URLs if present.)

## Pipeline

### Stage 0 — Preflight (you do this yourself, before any department runs)

Locate the toolkit and confirm the target is reachable. Thirty seconds here prevents
an entire pipeline of departments producing findings about a site nobody could fetch.

```bash
for d in "$CLAUDE_PLUGIN_ROOT" .claude ../.claude "$HOME/.claude" $(ls -dt "$HOME"/.claude/plugins/cache/*/seo-geo-consultant/*/ 2>/dev/null); do
  [ -n "$d" ] && [ -d "$d/skills/seo-geo-consultant/references" ] || continue
  k=$(cd "$d" && pwd)
  echo "REFERENCES: $k/skills/seo-geo-consultant/references"
  ls "$k/scripts/seo-probe.py" "$k/skills/seo-geo-consultant/scripts/seo-probe.py" 2>/dev/null | head -1 | sed 's/^/PROBE:      /'
  exit 0
done
echo "PLUGIN FILES NOT FOUND"
```

The printed paths are absolute; shell variables do not survive between tool calls, so
pass the literal `REFERENCES` and `PROBE` paths to every department you launch —
that saves each of them from re-resolving.

- `PLUGIN FILES NOT FOUND` → the plugin files are missing. Tell the user to run the
  installer (`scripts/install.sh`) and stop.
- **Live-URL target:** run `python3 <PROBE> preflight <origin>`.
  - exit 0 → proceed, and pass the paths plus the preflight result to every department.
  - exit 3 → **the environment's network policy blocked the fetch.** Stop the
    pipeline. Report the blocked host and the remediation the probe prints, and offer
    the two alternatives: run from Claude Code CLI with normal network access, or
    switch to owned-data mode using client exports (`owned-data-guide.md`).
  - exit 4 → the site blocks automated fetchers. Record it as a GEO finding for the
    geo department and continue only with what can legitimately be fetched.
  - exit 5 → unreachable. Confirm the domain with the user before spending departments.
- **Codebase target:** confirm the path exists and is the intended app (in a monorepo,
  resolve which app before Stage 1).

### Stage 1 — Intake (sequential, blocking)
First, the **one-time data call**: check whether a `seo-data/` directory exists in
the target (or the user pointed to data files). If nothing is found, ask the user
**once**: do they have exports to drop in — Search Console (Performance/Coverage),
Screaming Frog crawl, PageSpeed/CrUX, analytics, backlink tools? Make clear it's
optional and the audit runs fine without. Whatever the answer, proceed — never wait
on data again for the rest of the pipeline, and never let any department re-ask.

Then run **seo-discovery** with the target, business goal, and data location (or
"none provided"). Its Discovery Brief — including the Data Inventory — is the input
to every later stage. If discovery reports the target is ambiguous, resolve with the
user before continuing.

### Stage 2 — Audit departments (parallel)
Launch these in parallel, each with the full Discovery Brief pasted into its prompt:

- **seo-tech-auditor**
- **seo-onpage-auditor**
- **seo-schema-auditor**
- **seo-performance-auditor**
- **seo-geo-auditor**

Skip a department only if the Discovery Brief's "Recommended Department Scope" says
it has no work (record the skip). While they run, keep the user posted on which
departments are in flight.

### Stage 3 — Strategy departments (parallel, after Stage 2)
Launch with the Discovery Brief **plus the Stage 2 Department Reports** (they build
on findings, they don't re-audit):

- **seo-content-strategist** — always.
- **seo-competitor-analyst** — only if competitor URLs were given or the user asked
  for competitive analysis.

### Stage 4 — Boardroom (sequential, last)
Run **seo-roadmap-director** with the Discovery Brief and every Department Report
verbatim. It deduplicates, priority-scores, writes `seo-audit-report.md`, and
returns the executive summary.

### Stage 5 — Deliver and offer execution
Relay the director's executive summary to the user, including the "Decisions Needed"
list, the data-coverage line, and the consolidated Data Request for next cycle, and
point to the written report. Then offer to implement, starting with the
0–30-day items, via **seo-fix-engineer** — but only start it after the user approves
which items to ship.

## Rules of Engagement

- **Cross-department mail:** collect each report's "Handoff Notes" and include the
  relevant ones when launching later departments.
- **Pass reports verbatim** between stages — do not summarize a department's report
  before handing it to the director; lossy handoffs corrupt the priority matrix.
- **Failure handling:** if a department fails or returns garbage, retry it once with
  the error context; if it fails again, proceed and tell the director that
  department is missing (it records the gap in Risks & Assumptions). Never silently
  drop a department.
- **No freelancing:** findings come from departments only. If you notice something
  yourself, hand it to the relevant department as a note in its prompt.
- **No fabrication, ever:** if a department reports it could not fetch or read
  something, that stays in "Could Not Verify" through to the final report. Never let
  a gap get smoothed into a confident finding on the way to the boardroom.
- For a quick single-domain question, don't run the whole pipeline — run the one
  relevant department directly (or just use the seo-geo-consultant skill).
