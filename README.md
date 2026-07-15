# SEO & GEO Consultant Plugin for Claude Code

A Claude Code plugin that acts as a senior SEO and GEO (Generative Engine Optimization) consultant. It audits, strategizes, and implements technical SEO, content optimization, structured data, and AI search visibility for SaaS and web applications.

## What It Does

This plugin gives Claude deep expertise in:

- **Technical SEO** -- Meta tags, sitemaps, robots.txt, canonical URLs, Core Web Vitals, structured data (JSON-LD)
- **Content & Keyword Strategy** -- Search intent mapping, keyword research, topic clusters, content briefs, internal linking architecture
- **Generative Engine Optimization (GEO)** -- Making your content visible in ChatGPT, Perplexity, Google AI Overviews, and Bing Copilot
- **Multi-Stack Implementation** -- Production-ready guidance for Next.js (App Router Metadata API), React SPAs (Vite/CRA with react-helmet-async and prerendering), WordPress, Shopify, and site builders
- **Client Deliverables** -- Standardized audit reports with severity/priority matrices, 30/60/90 roadmaps, confidence-tiered claims, and quarterly AEO measurement
- **Multi-Agent Audit Pipeline** -- 10 specialist subagents that run like corporate departments (discovery, technical, on-page, schema, performance, GEO, content strategy, competitive intel, roadmap, implementation) and merge into one prioritized roadmap

## When It Triggers

The skill activates automatically when you mention:
- SEO, GEO, search visibility, or organic traffic
- Meta tags, structured data, schema markup, JSON-LD
- Sitemaps, robots.txt, Open Graph, Core Web Vitals
- AI search optimization, ChatGPT visibility, Perplexity
- Building landing pages, marketing pages, or blog pages

## Install

### Option A: Plugin install (Claude Code CLI / desktop with plugin support)

In Claude Code, add this repository as a plugin marketplace, then install the plugin:

```
/plugin marketplace add opsach/seo
/plugin install seo-geo-consultant@opsach-seo
```

### Option B: Manual install (works everywhere -- no `/plugin` needed)

If `/plugin` isn't available in your environment (web sessions, older CLI versions,
managed environments), copy the plugin's pieces directly into your target project's
`.claude/` directory. Run from **your project's root**:

```bash
git clone --depth 1 https://github.com/opsach/seo /tmp/seo-plugin
mkdir -p .claude/agents .claude/commands .claude/skills
cp /tmp/seo-plugin/agents/*.md .claude/agents/
cp /tmp/seo-plugin/commands/*.md .claude/commands/
cp -r /tmp/seo-plugin/skills/seo-geo-consultant .claude/skills/
rm -rf /tmp/seo-plugin
```

Claude Code auto-loads `.claude/agents/`, `.claude/commands/`, and `.claude/skills/`
from the project -- the 10 pipeline agents, `/seo-pipeline`, `/seo-audit`, and
`/aeo-plan` all work identically to a plugin install. Commit the `.claude/` folder
to the project repo and every session on that repo (local, desktop, or web) gets the
full pipeline with zero setup. To update later, re-run the same commands.

## What's Included

### Skill: `seo-geo-consultant`

**6 workflow modes:**

1. **Full SEO/GEO Audit** -- Reads your codebase and produces a prioritized report with GEO readiness scoring
2. **Content Page Optimization** -- Optimizes landing pages, blog posts, and marketing content for both Google and AI search
3. **Technical SEO Implementation** -- Implements meta tags, sitemaps, robots.txt, structured data with production-ready code (Next.js, React SPA, WordPress, Shopify)
4. **GEO Optimization** -- Comprehensive strategy for AI search visibility (on-site and off-site)
5. **Live Site Audit** -- URL-only audits for prospects, clients, and competitors when you don't have code access
6. **Keyword & Content Strategy** -- Intent-mapped keyword targets, topic clusters, and content briefs

### Slash Commands

- `/seo-pipeline [URL or path] [goal] [competitor URLs]` -- run the full multi-agent department pipeline end to end
- `/seo-audit [URL or path]` -- run a full single-session audit of the current project, or a URL-only live audit
- `/aeo-plan [product or URL]` -- generate a quarterly AEO measurement plan

### Agent Pipeline (10 department subagents)

`/seo-pipeline` orchestrates specialist subagents like departments in a consultancy --
discovery first, audits in parallel, strategy on top of the audit findings, then one
boardroom merge. Every department reports findings in a shared contract (ID, severity,
evidence, impact/effort, confidence tier) so the final roadmap is deduplicated and
priority-scored, not stapled together. Each agent also works standalone.

| Stage | Agent | Department |
|---|---|---|
| 1 | `seo-discovery` | Intake -- stack detection, page inventory, SEO surface map |
| 2 | `seo-tech-auditor` | Technical SEO -- crawlability, indexation, sitemaps, canonicals, redirects |
| 2 | `seo-onpage-auditor` | On-Page -- titles, metas, headings, internal linking, Open Graph |
| 2 | `seo-schema-auditor` | Structured Data -- JSON-LD coverage, validity, penalty risk |
| 2 | `seo-performance-auditor` | Performance -- Core Web Vitals risk, rendering strategy, JS/image weight |
| 2 | `seo-geo-auditor` | GEO/AEO -- AI crawler access, llms.txt, extractability, off-site presence |
| 3 | `seo-content-strategist` | Content Strategy -- intent map, topic clusters, content briefs |
| 3 | `seo-competitor-analyst` | Competitive Intel -- URL-only competitor benchmarking (optional) |
| 4 | `seo-roadmap-director` | Boardroom -- merges all reports into `seo-audit-report.md` with a 30/60/90 plan |
| 5 | `seo-fix-engineer` | Implementation -- ships approved roadmap items (the only agent with edit rights) |

**Optional owned data:** drop Search Console, Screaming Frog, PageSpeed/CrUX,
analytics, or backlink exports into a `seo-data/` folder in the audited project and
the departments use them to verify findings at scale (labeled **data-backed** vs
**inferred**). No data? The pipeline runs exactly the same and tells you which
exports would be most valuable next cycle. See `owned-data-guide.md`.

### Reference Files

- `audit-checklist.md` -- Complete 140+ item audit checklist covering technical SEO, on-page, structured data, GEO, local SEO, site migrations, and off-site presence
- `geo-optimization.md` -- Deep dive on GEO: content structure for AI citations, E-E-A-T, AI crawler management, llms.txt optimization, off-site strategy, and measurement
- `content-strategy.md` -- Keyword research, search intent mapping, topic clusters, content brief template, internal linking architecture, and cannibalization fixes
- `nextjs-implementation.md` -- Production-ready Next.js App Router code for metadata API, JSON-LD, sitemaps, robots.ts, OG images, Core Web Vitals, and i18n
- `react-spa-implementation.md` -- SEO for client-rendered React (Vite/CRA): rendering reality check, react-helmet-async, prerendering, and SPA-specific traps
- `cms-implementation.md` -- WordPress, Shopify, and site-builder implementation guidance with platform-specific traps and high-value wins
- `schema-templates.md` -- Copy-paste JSON-LD templates for Organization, WebSite, SoftwareApplication, Article, FAQPage, BreadcrumbList, Person, HowTo, LocalBusiness, and more
- `live-site-audit.md` -- URL-only audit procedure (fetch/inspect meta tags, robots.txt, sitemap, redirects, TTFB, PageSpeed field data) for sites without code access
- `aeo-measurement-template.md` -- Quarterly AEO measurement framework for prompt tracking, Share of Model, citation rate, and action mapping
- `audit-report-template.md` -- Standardized SEO/GEO audit output format with severity, impact/effort prioritization, and 30/60/90 roadmap
- `evidence-policy.md` -- Confidence-tier and evidence-quality policy to prevent overconfident GEO/AEO claims
- `owned-data-guide.md` -- Optional client-data ingestion (GSC, Screaming Frog, CrUX/PSI, analytics, backlinks) via a `seo-data/` folder, with data-backed vs inferred evidence labeling and graceful degradation when no data is provided
- `run-guide.md` -- Step-by-step guide to run audits, AEO planning, and implementation workflows in Claude Code


## How to Run This Tool

This project is a **Claude Code plugin/skill**, not a standalone CLI executable.

1. Install the plugin (see [Install](#install) above).
2. Open Claude Code in the website/app repo you want to improve -- or anywhere, if you're running a URL-only live site audit.
3. Trigger one of the workflows with explicit prompts, for example:

```text
Audit my site's SEO and GEO readiness and format output using references/audit-report-template.md
```

```text
Create a quarterly AEO measurement plan using references/aeo-measurement-template.md
```

```text
Implement Next.js technical SEO using references/nextjs-implementation.md and references/schema-templates.md
```

See the full operational guide in `skills/seo-geo-consultant/references/run-guide.md`.

## Key GEO Concepts

This plugin teaches Claude about:

- **The 120-180 word section rule** -- AI systems extract passages of this length for citations
- **The 3-month citation cliff** -- Content older than 3 months sees sharp drops in AI citations
- **AI-extractable writing patterns** -- Definitional statements, feature bullets, comparative positioning
- **AI crawler management** -- Proper robots.txt for GPTBot, ClaudeBot, PerplexityBot, OAI-SearchBot
- **Off-site GEO** -- Product directories, Reddit/HN presence, content syndication
- **llms.txt optimization** -- Query-answer pairs and competitive positioning for AI retrieval

## Example Usage

```
> Audit my site's SEO and GEO readiness

> Add proper meta tags and structured data to my Next.js app

> How do I make my SaaS product show up in ChatGPT and Perplexity?

> Optimize this landing page for AI search visibility

> Create a robots.txt that allows AI crawlers

> Run a live SEO/GEO audit of https://client-site.com -- I only have the URL, no code access

> Build a keyword and content plan with topic clusters for my product

> Fix the SEO on my client's WordPress site
```

## Credits

Originally based on [seo-geo-consultant by AndreasH96](https://github.com/AndreasH96/seo-geo-consultant) (MIT). This fork adds the AEO measurement framework, evidence/confidence policy, audit report template, run guide, live-site audit workflow, keyword/content strategy, React SPA and WordPress/Shopify implementation guides, site-migration and local SEO checklists, LocalBusiness schema support, slash commands, and plugin packaging.

## License

MIT -- see [LICENSE](LICENSE) (original copyright retained).
