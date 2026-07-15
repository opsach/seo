# Run Guide: How to Use the SEO/GEO Consultant Tool

This repository is a **skill/plugin knowledge pack** (not a standalone CLI binary). You run it through your coding assistant (Claude Code) after installing the plugin.

## 1) Install

In Claude Code, add this repository as a plugin marketplace and install:

```
/plugin marketplace add opsach/seo
/plugin install seo-geo-consultant@opsach-seo
```

## 2) Open your target project

Start Claude Code in the repo you want to audit (your website/app codebase), then invoke the skill using a clear request.

## 3) Run a full SEO/GEO audit

Use a prompt like:

```text
Audit my site's SEO and GEO readiness.
Use references/audit-checklist.md, references/evidence-policy.md,
and references/audit-report-template.md.
```

Expected output:
- Severity-ranked findings (Critical / Important / Nice-to-have)
- Impact/effort priority ranking
- Confidence tier tags on recommendations
- 30/60/90-day roadmap

## 4) Run AEO measurement planning

Use a prompt like:

```text
Create a quarterly AEO measurement plan for this site using
references/aeo-measurement-template.md.
```

Expected output:
- 20-30 prompt query set
- Platform run format for ChatGPT, Perplexity, Google AI Overviews
- SoM and citation-rate baseline model
- Action mapping table

## 5) Run technical implementation mode

Use a prompt like:

```text
Implement technical SEO for this Next.js app:
metadata, JSON-LD, sitemap, robots.txt, and canonicals.
Use references/nextjs-implementation.md and references/schema-templates.md.
```

For other stacks, swap the implementation reference:
- React SPA (Vite/CRA): `references/react-spa-implementation.md`
- WordPress / Shopify / site builders: `references/cms-implementation.md`

Expected output:
- Concrete code changes in your app (or platform-specific instructions for CMS clients)
- Metadata/structured data implementation
- Crawlability files (`sitemap.xml`, `robots.txt` patterns)

## 5b) Run keyword & content strategy mode

Use a prompt like:

```text
Build a keyword and content plan for this product using
references/content-strategy.md. Start from our Search Console data
and produce topic clusters plus a content brief per page.
```

Expected output:
- Intent-mapped, prioritized keyword targets
- Topic-cluster map (pillar + cluster pages) with internal linking rules
- A content brief per planned page

## Shortcut: slash commands

If installed as a plugin, three commands wrap the most common workflows:

- `/seo-pipeline [URL or path] [goal] [competitors]` -- full multi-agent department pipeline
- `/seo-audit [URL or path]` -- full single-session audit (codebase or URL-only)
- `/aeo-plan [product or URL]` -- quarterly AEO measurement plan

## 5c) Run the multi-agent department pipeline

For the deepest audit, run the department pipeline instead of a single-session audit:

```text
/seo-pipeline https://client-site.com -- goal: get cited by ChatGPT for [category];
competitors: https://competitor-a.com https://competitor-b.com
```

Optional but recommended: create a `seo-data/` folder in the audited project and
drop in any exports you have -- Search Console (Performance/Coverage), a Screaming
Frog crawl, PageSpeed/CrUX, analytics, backlink tools. The pipeline asks once at
kickoff, uses whatever is there to make findings **data-backed** instead of
**inferred**, and runs exactly the same if you have nothing (see
`references/owned-data-guide.md`).

What happens, stage by stage:
1. `seo-discovery` maps the target (stack, page inventory, SEO surfaces, and a data inventory of any `seo-data/` exports)
2. Five audit departments run in parallel: technical, on-page, schema, performance, GEO/AEO
3. `seo-content-strategist` (and `seo-competitor-analyst` if competitors were given) build on the audit findings
4. `seo-roadmap-director` merges everything into `seo-audit-report.md` -- deduplicated, priority-scored, 30/60/90 roadmap, plus a data-coverage line and a consolidated data request for the next cycle
5. You approve items; `seo-fix-engineer` implements them in the codebase

Each department can also be invoked directly for single-domain questions, e.g.
"Use the seo-geo-auditor agent to check our AI search readiness."

## 6) Run a live site audit (URL only)

Use a prompt like:

```text
Run a live SEO/GEO audit of https://client-site.com using
references/live-site-audit.md. I don't have code access.
Format the output with references/audit-report-template.md.
```

Expected output:
- Findings from fetched HTML, robots.txt, sitemap, redirects, and performance signals
- Explicit "not verifiable without code access" list
- Same severity/priority/confidence structure as a codebase audit

## 7) Quality checklist before accepting output

- Recommendations include confidence tier
- Numeric claims include source/date/scope/limitations
- Findings include owner + ETA
- Prioritization uses impact/effort
- Measurement baseline exists for next quarter

## Troubleshooting

### "Tool isn't running"
- Confirm plugin installed successfully in Claude Code
- Confirm you're inside the target project folder
- Use explicit mode language: "Run Full SEO/GEO Audit"

### "Output is too generic"
- Ask the model to use `references/audit-report-template.md` exactly
- Require file-level citations and concrete implementation diffs

### "Need reproducible process"
- Save final audits in your repo using the audit report template
- Re-run quarterly using the AEO measurement template
