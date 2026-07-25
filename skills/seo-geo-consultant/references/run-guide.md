# Run Guide: How to Use the SEO/GEO Consultant Tool

This repository is a **skill/plugin knowledge pack** (not a standalone CLI binary). You run it through your coding assistant (Claude Code) after installing the plugin.

## 1) Install

**Installer route** (works everywhere, including Claude Code on the web) -- run from
the root of the project you want to audit:

```bash
curl -fsSL https://raw.githubusercontent.com/opsach/seo/main/scripts/install.sh | bash
```

Add `-s -- --user` to install once for every project instead of one repo, or
`-s -- --ref BRANCH` to install from a branch or tag. Re-running is safe. Agents,
slash commands, the skill, and the evidence probe load automatically from `.claude/`;
commit that folder to make the pipeline available in every session with zero setup.

**On Claude Code web this is the only route** -- `/plugin` does not exist there, and
the container is ephemeral, so a `--user` install disappears with the session.
Installing into the project and committing `.claude/` is what persists.

**Plugin route** (Claude Code CLI/desktop only -- `/plugin` does not exist on web):

```
/plugin marketplace add opsach/seo
/plugin install seo-geo-consultant@opsach-seo
```

**Verify either route** by starting a new session and typing `/seo-audit`. Commands
and agents are loaded at session start, so an install mid-session needs a fresh one.

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

**Preflight first.** From the project where you installed:

```bash
python3 .claude/scripts/seo-probe.py preflight https://client-site.com
```

Exit 0 means fetching works. Exit 3 means the environment's network policy blocked
the request before it left the machine -- fix that first (see Troubleshooting below);
an audit run past a blocked preflight is fabricated, not fetched.

Then:

```text
Run a live SEO/GEO audit of https://client-site.com using
references/live-site-audit.md. I don't have code access.
Format the output with references/audit-report-template.md.
```

Expected output:
- Findings citing measured values from the probe -- status codes, tag lengths,
  robots verdicts with line numbers, JSON-LD parse errors, rendering verdict
- Explicit "not verifiable without code access" list, and the sample size stated
  ("5 of 412 sitemap URLs probed on <date>")
- Same severity/priority/confidence structure as a codebase audit

## 7) Quality checklist before accepting output

- Recommendations include confidence tier
- Numeric claims include source/date/scope/limitations
- Findings include owner + ETA
- Prioritization uses impact/effort
- Measurement baseline exists for next quarter

## Troubleshooting

### "Tool isn't running" / slash commands missing
- Commands and agents load at **session start** -- start a new session after installing
- Confirm the files landed: `ls .claude/agents .claude/commands .claude/skills`
- From a clone of the plugin repo, run `python3 scripts/verify.py` to validate the
  manifests, frontmatter, references, and `.claude/` mirror in one pass
- Confirm you're inside the target project folder
- Use explicit mode language: "Run Full SEO/GEO Audit"

### "`/plugin` isn't available in this environment"
Expected on Claude Code web -- `/plugin` exists only in the CLI and desktop app.
Nothing is broken; use the installer route in section 1 instead.

### "Can't reach the client's website"
Run `seo-probe.py preflight <origin>` and read the exit code:

- **3 -- blocked by network policy.** The sandbox refused the connection. Change the
  environment's network access setting (or allowlist the domain) and start a new
  session (<https://code.claude.com/docs/en/claude-code-on-the-web>), run the audit
  from Claude Code CLI instead, or switch to owned-data mode with client exports
  (`owned-data-guide.md`).
- **4 -- the site blocks automated fetchers.** Report it as a finding; AI crawlers are
  refused the same way. Never try to defeat bot protection.
- **5 -- unreachable.** DNS, TLS, or timeout. Confirm the domain with the client.

Whatever the cause, do not accept an audit that continues past a failed preflight:
its findings were not measured.

### "Output is too generic"
- Ask the model to use `references/audit-report-template.md` exactly
- Require file-level citations and concrete implementation diffs

### "Need reproducible process"
- Save final audits in your repo using the audit report template
- Re-run quarterly using the AEO measurement template
