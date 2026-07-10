# Live Site Audit (URL Only)

Procedure for auditing a site when you only have a URL -- no codebase access.
Use for prospect audits, client pitches, and competitor benchmarking. Output the
findings through `audit-report-template.md` exactly like a codebase audit, and
explicitly flag anything that could not be verified without code access.

## 1) Fetch the Core Assets

Fetch raw HTML (not a rendered/markdown view) so meta tags and JSON-LD are visible:

```bash
# Homepage HTML + response headers + timing
curl -sS -D - -o homepage.html -w 'TTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n' \
  -A "Mozilla/5.0 (compatible; SEO-Audit)" https://example.com/

# Crawl-control files
curl -sS https://example.com/robots.txt
curl -sS https://example.com/sitemap.xml | head -100
curl -sS -o /dev/null -w '%{http_code}' https://example.com/llms.txt
```

If `curl` is unavailable, use WebFetch -- but note that WebFetch returns
processed content, so for meta-tag inspection prefer raw HTML whenever possible.

## 2) Canonicalization & Redirect Checks

```bash
# Each of these should end at ONE canonical origin in a single redirect hop
curl -sIL -o /dev/null -w '%{url_effective} %{http_code}\n' http://example.com/
curl -sIL -o /dev/null -w '%{url_effective} %{http_code}\n' http://www.example.com/
curl -sIL -o /dev/null -w '%{url_effective} %{http_code}\n' https://www.example.com/

# Soft-404 check: a garbage URL must return 404, not 200
curl -s -o /dev/null -w '%{http_code}' https://example.com/this-page-should-not-exist-xyz
```

Record: HTTPS enforcement, www/non-www consistency, redirect chain length,
trailing-slash consistency, soft-404 behavior.

## 3) Inspect the Homepage HTML

Check in the raw HTML (grep or read `homepage.html`):

- `<title>` -- length, keyword placement, brand suffix
- `<meta name="description">` -- length, CTA
- `<link rel="canonical">` -- present, self-referencing, absolute
- `<html lang="...">` -- set correctly
- `og:*` and `twitter:*` tags -- complete set, absolute image URLs
- `<script type="application/ld+json">` -- which schema types exist; validate structure
- Heading structure -- exactly one `<h1>`, logical H2/H3 nesting
- `<img>` tags -- alt attributes present, dimensions set
- **SSR check**: is the main content present in the raw HTML, or only an empty
  root div (`<div id="root"></div>` / skeleton markup)? Client-only rendering is a
  Critical finding for both SEO and GEO -- AI crawlers largely do not execute JS.

## 4) robots.txt & Sitemap Analysis

- Does robots.txt block any AI crawlers (GPTBot, OAI-SearchBot, ClaudeBot,
  Claude-SearchBot, PerplexityBot, Google-Extended)? Explicit allows are ideal;
  absence of blocks is acceptable.
- Is the sitemap referenced in robots.txt?
- Does the sitemap parse? Do `<lastmod>` dates look real (varied) or fake (all identical/today)?
- Cross-check: any sitemap URLs that robots.txt disallows? (contradiction)
- Sample the sitemap: pick 5-10 representative URLs (homepage, a product/service
  page, a blog post, a category page) and repeat step 3 on each.

## 5) Performance Signals

- TTFB from the curl timing above (target < 200ms; > 800ms is a Critical finding)
- Response headers: compression (`content-encoding: br|gzip`), caching
  (`cache-control`, `age`, CDN headers like `cf-cache-status`/`x-vercel-cache`)
- Run PageSpeed Insights for lab + field data (no API key needed at low volume):

```bash
curl -sS "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://example.com&strategy=mobile" \
  | head -c 4000
```

Extract: LCP, INP, CLS from `loadingExperience` (real-user CrUX data, when
available) -- prefer field data over lab scores in the report.

## 6) GEO Spot-Checks

- Is content structured in self-contained sections with question-like headings?
- Named authors on blog content? Visible "last updated" dates?
- `llms.txt` present? Quality per `geo-optimization.md`?
- Quick off-site scan: search the brand on G2/Capterra/ProductHunt (SaaS) or
  Google Business Profile/Yelp (local); check Reddit/HN mentions.

## 7) Report

Use `audit-report-template.md`. Additional rules for URL-only audits:

- Add a **"Not verifiable without code access"** list (e.g., exact rendering
  strategy, internal redirects config, image pipeline, middleware) -- never guess these.
- Every finding must cite the URL where it was observed and the date of the check.
- Pitch framing: lead with the 3 highest-impact fixes and estimate effort
  assuming no codebase familiarity.

## Limits

- Do not crawl aggressively: keep it to ~10-15 requests per site, spaced out.
- Do not attempt to bypass bot protection (Cloudflare challenges etc.). If the
  site blocks you, note "site blocks automated fetchers" -- that itself is a
  GEO finding worth reporting.
- Field data (CrUX) is only available for sites with sufficient traffic; say so
  when it's missing rather than substituting lab data silently.
