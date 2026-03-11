# SEO/GEO Audit Checklist

Use this checklist systematically when performing a full site audit. Check each item, note the current state, and classify issues as Critical / Important / Nice-to-have.

## 1. Technical Foundation

### Crawlability & Indexation
- [ ] `robots.txt` exists and is correctly configured
- [ ] `robots.txt` allows AI crawlers: GPTBot, OAI-SearchBot, ClaudeBot, Claude-SearchBot, PerplexityBot, Googlebot
- [ ] No critical pages accidentally blocked by robots.txt or meta robots noindex
- [ ] XML sitemap exists at `/sitemap.xml`
- [ ] Sitemap includes all important pages with correct `<lastmod>` dates
- [ ] Sitemap is referenced in robots.txt
- [ ] No orphan pages (pages not linked from anywhere)
- [ ] No broken internal links (404s)
- [ ] Proper HTTP 404 status for non-existent pages (not soft 404s returning 200)
- [ ] No contradictions between robots.txt and sitemap (e.g., Disallowed URLs in sitemap)
- [ ] No contradictions between robots.txt and meta robots (e.g., noindex pages allowed in sitemap)
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] `www` vs non-`www` canonical is consistent
- [ ] Site registered in Bing Webmaster Tools (ChatGPT and Copilot use Bing's index)

### Rendering & Performance
- [ ] SEO-critical content is server-side rendered (not client-only)
- [ ] Pages load within LCP target (<= 2.5s)
- [ ] INP is within threshold (<= 200ms)
- [ ] CLS is minimal (< 0.1)
- [ ] TTFB under 200ms (critical for AI crawler access)
- [ ] Images use `next/image` with proper `width`, `height`, and `alt`
- [ ] Above-the-fold images have `priority` attribute
- [ ] Fonts loaded via `next/font` with `display: 'swap'`
- [ ] No render-blocking resources
- [ ] Heavy components are code-split with `dynamic()` imports
- [ ] Web app manifest (`manifest.json` or `site.webmanifest`) exists for PWA/mobile
- [ ] Apple touch icon is a proper PNG (not SVG data URI -- iOS requires PNG)

### URL Structure
- [ ] URLs are short, descriptive, lowercase, hyphenated
- [ ] No query parameters for content pages
- [ ] Consistent trailing slash policy
- [ ] No duplicate content (same content at multiple URLs)

## 2. On-Page SEO

### Meta Tags (Check Every Public Page)
- [ ] `<title>` tag: 50-60 characters, keyword near start, brand suffix
- [ ] `<meta name="description">`: 150-160 characters with CTA
- [ ] `<link rel="canonical">` pointing to self (or canonical version)
- [ ] `<html lang="xx">` attribute set correctly
- [ ] No duplicate title tags across pages
- [ ] No duplicate meta descriptions across pages
- [ ] Title template configured (`%s | Brand`)

### Content Structure
- [ ] Single `<h1>` per page containing primary keyword
- [ ] Logical heading hierarchy (H1 > H2 > H3, no skipping levels)
- [ ] Adequate content length for the page type (landing pages: 500+ words, blog posts: 1500+ words)
- [ ] Primary keyword in first paragraph
- [ ] Internal links to related pages with descriptive anchor text
- [ ] No thin content pages (pages with < 200 words of unique content)

### Images
- [ ] All images have descriptive `alt` attributes
- [ ] Image file names are descriptive (not `img_001.jpg`)
- [ ] Images are appropriately sized (not serving 4000px images in 400px containers)
- [ ] WebP or AVIF format used where possible (automatic with `next/image`)

## 3. Structured Data

### Required Schema (All Sites)
- [ ] `Organization` schema on homepage / root layout
- [ ] `WebSite` schema with `SearchAction` on homepage
- [ ] `BreadcrumbList` schema on interior pages

### Page-Type Schema
- [ ] `SoftwareApplication` on product/feature pages (SaaS)
- [ ] `Article` / `BlogPosting` on blog posts with author, datePublished, dateModified
- [ ] `FAQPage` on FAQ sections
- [ ] `Product` with `Offer` on pricing pages
- [ ] `Person` schema for author pages
- [ ] `HowTo` on tutorial/guide pages

### Schema Quality
- [ ] JSON-LD format used (not Microdata or RDFa)
- [ ] Schema matches actual page content (no misleading markup)
- [ ] No schema validation errors (test with Google Rich Results Test)
- [ ] XSS prevention: `<` replaced with `\u003c` in JSON-LD output

## 4. Social & Sharing

### Open Graph
- [ ] `og:title` set on all pages
- [ ] `og:description` set on all pages
- [ ] `og:image` set (1200x630px recommended)
- [ ] `og:type` set (`website` for homepage, `article` for posts)
- [ ] `og:url` set to canonical URL
- [ ] `og:site_name` set

### Twitter Cards
- [ ] `twitter:card` set (`summary_large_image` for pages with images)
- [ ] `twitter:title` and `twitter:description` set
- [ ] `twitter:image` set (absolute URL required)
- [ ] `twitter:creator` set if applicable

## 5. GEO (Generative Engine Optimization)

### Content Structure for AI
- [ ] Content organized in self-contained passages (120-180 words between headers)
- [ ] Sections lead with a direct answer in first 40-60 words
- [ ] Content includes specific statistics with sources
- [ ] Expert quotations included with attribution
- [ ] Comparison tables use clean HTML (not images)
- [ ] Definitions and explanations are extractable without surrounding context

### Author Authority
- [ ] All content has named, credentialed author bylines
- [ ] Author pages exist with `Person` schema
- [ ] Authors have verifiable external presence (LinkedIn, publications)
- [ ] No "content team" or anonymous bylines

### AI Crawler Access
- [ ] robots.txt allows: GPTBot, OAI-SearchBot, ClaudeBot, Claude-SearchBot, PerplexityBot
- [ ] CDN (Cloudflare etc.) is not blocking AI bot requests
- [ ] Server-side rendering for all important content
- [ ] TTFB under 200ms

### Content Freshness
- [ ] Key content updated within last 3 months (the "citation cliff")
- [ ] Visible "Last updated" timestamps on content pages
- [ ] `dateModified` in Article/BlogPosting schema is accurate
- [ ] Quarterly content refresh schedule in place

### Entity Authority
- [ ] Consistent brand information across platforms (Crunchbase, G2, LinkedIn, etc.)
- [ ] Product comparison pages with feature matrices exist
- [ ] Category-defining content exists ("What is [your category]?")
- [ ] Knowledge base / documentation is comprehensive

### llms.txt (Forward-Looking)
- [ ] `/llms.txt` file exists with site summary in Markdown
- [ ] Includes project name, summary, and key page URLs
- [ ] Includes query-answer pairs matching how users ask AI assistants
- [ ] Includes competitive positioning section
- [ ] Referenced in robots.txt
- [ ] Updated when site structure changes

### Recommendation Confidence & Evidence
- [ ] Each recommendation is tagged with confidence: **Standards-based** / **Widely observed** / **Experimental**
- [ ] Benchmark-style claims include source links or references
- [ ] Any platform-specific claim (ChatGPT, Perplexity, Google AI Overviews, Bing Copilot) includes date/context
- [ ] Forward-looking recommendations are clearly labeled as hypotheses, not guarantees

### Off-Site Presence
- [ ] Product listed on relevant directories (G2, Capterra, ProductHunt, AlternativeTo)
- [ ] Consistent brand information across all external platforms
- [ ] Community presence established (Reddit, HN, GitHub)
- [ ] `sameAs` in Organization schema links to all active profiles
- [ ] Site registered in Bing Webmaster Tools

## 6. User-Generated & Dynamic Content (If Applicable)

- [ ] User-generated pages have sufficient unique text content (not just a title and embed)
- [ ] Auto-generated descriptions enrich thin UGC pages (e.g., list components/features used)
- [ ] Dynamic pages return proper HTTP 404 for non-existent items (not 200 with error state)
- [ ] UGC pages have appropriate schema markup reflecting actual content
- [ ] Shared/public UGC pages are in the sitemap with real `lastmod` dates

## 7. International SEO (If Applicable)

- [ ] `hreflang` tags present on all localized pages
- [ ] `x-default` hreflang set for fallback language
- [ ] Locale-prefixed URLs (`/en/about`, `/de/about`)
- [ ] Sitemap includes `alternates.languages` for each locale
- [ ] Canonical URLs are locale-specific
- [ ] Middleware handles locale detection and redirection

## 8. GEO/AEO Measurement Discipline

- [ ] 20-30 target prompts tracked quarterly across ChatGPT, Perplexity, and Google AI Overviews
- [ ] Share of Model (SoM) tracked against top 3-5 competitors
- [ ] Citation log records source URL, query, model, and date
- [ ] AI referral traffic segmented in analytics (`chat.openai.com`, `perplexity.ai`, etc.)
- [ ] Optimization backlog linked to measurement deltas (what changed, what improved)

## Scoring Guide

After completing the audit, assign a GEO Readiness Score:

| Score | Meaning |
|-------|---------|
| 9-10 | Excellent -- competitive advantage in AI search |
| 7-8 | Good -- solid foundation, minor improvements needed |
| 5-6 | Average -- significant gaps in GEO readiness |
| 3-4 | Below average -- major technical or content issues |
| 1-2 | Critical -- fundamental SEO problems must be fixed first |
