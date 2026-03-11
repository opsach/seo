# Run Guide: How to Use the SEO/GEO Consultant Tool

This repository is a **skill/plugin knowledge pack** (not a standalone CLI binary). You run it through your coding assistant (Claude Code) after installing the plugin.

## 1) Install

```bash
claude /install-plugin https://github.com/AndreasH96/seo-geo-consultant
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

Expected output:
- Concrete code changes in your app
- Metadata/structured data implementation
- Crawlability files (`sitemap.xml`, `robots.txt` patterns)

## 6) Quality checklist before accepting output

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
