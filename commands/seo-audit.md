---
description: Run a full SEO/GEO audit of the current codebase, or a URL-only live audit
argument-hint: "[URL or path -- omit to audit the current project]"
---

Run a full SEO/GEO audit using the seo-geo-consultant skill.

Target: $ARGUMENTS

- If the target is a URL (or the user has no code access), follow the Live Site
  Audit workflow in `references/live-site-audit.md`.
- Otherwise audit the current codebase: read the project structure, then work
  through `references/audit-checklist.md` systematically, reading the relevant
  files for each area.

Rules for the deliverable:
1. Format the final report with `references/audit-report-template.md` exactly --
   executive summary with scores, severity + priority matrix (Impact/Effort),
   findings by domain, 30/60/90-day plan, measurement plan.
2. Tag every recommendation with a confidence tier and follow
   `references/evidence-policy.md` for any numeric claim.
3. Cite the file path (or URL) and the specific evidence for every finding.
4. Finish by offering to implement the fixes starting with the highest
   priority-score items.
