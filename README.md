# SEO & GEO Consultant Plugin for Claude Code

A Claude Code plugin that acts as a senior SEO and GEO (Generative Engine Optimization) consultant. It audits, strategizes, and implements technical SEO, content optimization, structured data, and AI search visibility for SaaS and web applications.

## What It Does

This plugin gives Claude deep expertise in:

- **Technical SEO** -- Meta tags, sitemaps, robots.txt, canonical URLs, Core Web Vitals, structured data (JSON-LD)
- **Content Optimization** -- Heading hierarchy, keyword strategy, content structure for both Google and AI search
- **Generative Engine Optimization (GEO)** -- Making your content visible in ChatGPT, Perplexity, Google AI Overviews, and Bing Copilot
- **Next.js / React Implementation** -- Production-ready code using the App Router Metadata API, or react-helmet-async for Vite/CRA projects

## When It Triggers

The skill activates automatically when you mention:
- SEO, GEO, search visibility, or organic traffic
- Meta tags, structured data, schema markup, JSON-LD
- Sitemaps, robots.txt, Open Graph, Core Web Vitals
- AI search optimization, ChatGPT visibility, Perplexity
- Building landing pages, marketing pages, or blog pages

## Install

In Claude Code, add this repository as a plugin marketplace, then install the plugin:

```
/plugin marketplace add opsach/seo
/plugin install seo-geo-consultant@opsach-seo
```

## What's Included

### Skill: `seo-geo-consultant`

**5 workflow modes:**

1. **Full SEO/GEO Audit** -- Reads your codebase and produces a prioritized report with GEO readiness scoring
2. **Content Page Optimization** -- Optimizes landing pages, blog posts, and marketing content for both Google and AI search
3. **Technical SEO Implementation** -- Implements meta tags, sitemaps, robots.txt, structured data with production-ready code
4. **GEO Optimization** -- Comprehensive strategy for AI search visibility (on-site and off-site)
5. **Live Site Audit** -- URL-only audits for prospects, clients, and competitors when you don't have code access

### Reference Files

- `audit-checklist.md` -- Complete 130+ item audit checklist covering technical SEO, on-page, structured data, GEO, local SEO, and off-site presence
- `geo-optimization.md` -- Deep dive on GEO: content structure for AI citations, E-E-A-T, AI crawler management, llms.txt optimization, off-site strategy, and measurement
- `nextjs-implementation.md` -- Production-ready Next.js App Router code for metadata API, JSON-LD, sitemaps, robots.ts, OG images, Core Web Vitals, and i18n
- `schema-templates.md` -- Copy-paste JSON-LD templates for Organization, WebSite, SoftwareApplication, Article, FAQPage, BreadcrumbList, Person, HowTo, LocalBusiness, and more
- `live-site-audit.md` -- URL-only audit procedure (fetch/inspect meta tags, robots.txt, sitemap, redirects, TTFB, PageSpeed field data) for sites without code access
- `aeo-measurement-template.md` -- Quarterly AEO measurement framework for prompt tracking, Share of Model, citation rate, and action mapping
- `audit-report-template.md` -- Standardized SEO/GEO audit output format with severity, impact/effort prioritization, and 30/60/90 roadmap
- `evidence-policy.md` -- Confidence-tier and evidence-quality policy to prevent overconfident GEO/AEO claims
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
```

## Credits

Originally based on [seo-geo-consultant by AndreasH96](https://github.com/AndreasH96/seo-geo-consultant) (MIT). This fork adds the AEO measurement framework, evidence/confidence policy, audit report template, run guide, live-site audit workflow, LocalBusiness schema support, and plugin packaging.

## License

MIT -- see [LICENSE](LICENSE) (original copyright retained).
