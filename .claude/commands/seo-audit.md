---
description: Run a full SEO/GEO audit of the current codebase, or a URL-only live audit
argument-hint: "[URL or path -- omit to audit the current project]"
---

Run a full SEO/GEO audit using the seo-geo-consultant skill.

Target: $ARGUMENTS

- If the target is a URL (or the user has no code access), follow the Live Site
  Audit workflow in `references/live-site-audit.md`. **Preflight before anything
  else** — `seo-probe.py preflight <origin>`. Exit 3 means the environment's network
  policy blocked the request: report that and stop rather than auditing from memory.
  Then collect the evidence pack with `seo-probe.py site <origin> -n 5`.
- Otherwise audit the current codebase: read the project structure, then work
  through `references/audit-checklist.md` systematically, reading the relevant
  files for each area.

Rules for the deliverable:
1. Format the final report with `references/audit-report-template.md` exactly --
   executive summary with scores, severity + priority matrix (Impact/Effort),
   findings by domain, 30/60/90-day plan, measurement plan.
2. Tag every recommendation with a confidence tier and follow
   `references/evidence-policy.md` for any numeric claim.
3. Cite the file path (or URL) and the specific observed value for every finding.
   Never cite WebFetch output for a meta-tag, schema, or status-code finding — it
   summarises pages into markdown and drops exactly those signals.
4. Anything you could not read or fetch goes in "Could Not Verify" with the reason.
   A missing finding is recoverable; an invented one is not.
5. Finish by offering to implement the fixes starting with the highest
   priority-score items.
