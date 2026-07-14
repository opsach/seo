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

### Stage 1 — Intake (sequential, blocking)
Run **seo-discovery** with the target and business goal. Its Discovery Brief is the
input to every later stage. If discovery reports the target is ambiguous, resolve
with the user before continuing.

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
list, and point to the written report. Then offer to implement, starting with the
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
- For a quick single-domain question, don't run the whole pipeline — run the one
  relevant department directly (or just use the seo-geo-consultant skill).
