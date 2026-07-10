# CMS SEO Implementation (WordPress / Shopify / Site Builders)

Most agency clients are not on Next.js. Read this when the target site runs
WordPress, Shopify, or a hosted site builder (Webflow, Squarespace, Wix). The
audit checklist and GEO playbook apply unchanged -- this file covers *how to
implement* fixes on each platform and the platform-specific traps to check.

## 1. WordPress

### Baseline Setup
- **One SEO plugin** -- Yoast SEO or Rank Math. Never both (duplicate meta tags,
  conflicting sitemaps). The plugin handles titles, meta descriptions,
  canonicals, OG/Twitter tags, and XML sitemaps.
- WordPress 5.5+ ships a native sitemap (`/wp-sitemap.xml`); SEO plugins replace
  it with their own (`/sitemap_index.xml` for Yoast). Confirm only ONE sitemap
  is live and that it's the one referenced in robots.txt.
- **robots.txt is virtual** by default. Edit it via the SEO plugin's file editor
  or place a physical `robots.txt` in the web root (physical overrides virtual).
  Add the AI crawler allowances from `geo-optimization.md` there.
- **llms.txt**: upload as a static file to the web root via hosting file manager
  or FTP; plugins also exist. Verify it serves at `/llms.txt` with `text/plain`
  or `text/markdown`.

### WordPress-Specific Audit Traps
- **Thin archive pages** -- tag, date, and author archives generate hundreds of
  near-empty indexable pages. Noindex them in the SEO plugin unless they have
  real content.
- **Attachment pages** -- old WP versions created an indexable page per uploaded
  image. WP 6.4+ disables this by default; on older sites, enable the SEO
  plugin's "redirect attachment URLs to the file" option.
- **`?replytocom=` and other parameter URLs** -- check GSC for parameter-based
  duplicates; canonicals usually handle it, verify they do.
- **Page builder bloat** (Elementor/Divi) -- deep div nesting and heavy CSS/JS
  wreck LCP/INP. Audit with PageSpeed; caching plugin (WP Rocket or equivalent)
  + image optimization (WebP conversion) are the standard first moves.
- **Schema**: SEO plugins output basic Organization/Article/BreadcrumbList
  JSON-LD automatically. For anything beyond that (FAQPage, LocalBusiness,
  Product), add custom JSON-LD via the theme (`wp_head` hook) or a snippets
  plugin -- and confirm the plugin's auto-schema doesn't duplicate the same
  `@type`.
- **Category-in-URL settings** -- changing permalink structure on an established
  site without a redirect map is a self-inflicted migration. Flag any permalink
  change as Critical-risk (see Site Migrations section of the audit checklist).

### High-Value WordPress Wins
1. Fix titles/descriptions sitewide via the SEO plugin's templates (`%%title%% %%sep%% %%sitename%%`)
2. Noindex thin archives; consolidate near-duplicate tag pages
3. Caching + WebP -- usually the biggest single CWV improvement
4. LocalBusiness JSON-LD for local clients (see `schema-templates.md`)
5. Named author pages with real bios for E-E-A-T (map to `Person` schema)

## 2. Shopify

### What Shopify Handles Automatically
- Sitemap at `/sitemap.xml` (auto-generated, not editable) -- submit to GSC/Bing
- Canonical tags in standard themes (collection-scoped product URLs
  canonicalize to `/products/handle`)
- SSL, and `robots.txt` with sensible defaults

### What You Can and Should Edit
- **robots.txt** -- editable since 2021 via `robots.txt.liquid`
  (Online Store > Themes > Edit code > Add template > robots). Add AI crawler
  allowances there; do not remove Shopify's default checkout/cart disallows.
- **Titles/meta** -- per-product/collection/page in the admin ("Search engine
  listing"); theme-level defaults in `theme.liquid`.
- **Structured data** -- standard themes emit basic Product JSON-LD. Verify it
  includes `offers` with real price/availability; extend via a theme snippet
  rendered in `theme.liquid` rather than stacking multiple SEO apps that each
  inject their own (duplicate Product schema is a common Shopify failure).
- **llms.txt** -- Shopify began auto-generating `/llms.txt` for storefronts in
  2025; verify at `yourstore.com/llms.txt`. Root files are otherwise not
  user-editable on Shopify. [Verify current platform behavior at audit time]

### Shopify-Specific Audit Traps
- **Duplicate product URLs** -- internal links must use the canonical
  `/products/handle` form, not `/collections/x/products/handle`. Standard themes
  link the collection-scoped form by default (`within: collection`); check the
  theme's product-card snippet.
- **Variant parameter URLs** (`?variant=123`) -- canonicals handle indexing, but
  ad/social links spread them; fine to leave, just don't sitemap them.
- **Thin collection pages** -- collections with no description text are
  boilerplate-only pages at scale. Add 100-200 words of real category content
  (this doubles as prime GEO extraction material).
- **App bloat** -- every app injects JS; measure PageSpeed before/after app
  installs. Remove leftovers from uninstalled apps in `theme.liquid`.
- **Blog limitations** -- Shopify's blog lacks native author profiles.
  For content-led GEO strategies, consider hosting the blog on a subdomain
  or headless setup only if the client has real publishing volume; otherwise
  work within Shopify and add `Person` author JSON-LD manually.

## 3. Site Builders (Webflow / Squarespace / Wix)

All three now expose the essentials -- per-page titles/descriptions, automatic
sitemaps, editable robots.txt (Webflow/Squarespace; Wix via SEO settings), and
custom code injection for JSON-LD.

- **Webflow**: best of the three for SEO control. Per-page OG fields, per-page
  custom code (head) for JSON-LD, editable robots.txt, auto sitemap. CMS
  collection templates let you bind JSON-LD fields dynamically.
- **Squarespace**: solid defaults; JSON-LD via per-page code injection
  (Settings > Advanced > Code Injection on Business plan+).
- **Wix**: has SEO settings panels and structured data support per page; verify
  output with Rich Results Test rather than trusting the UI.

For all builders: the ceiling is lower than WordPress/frameworks -- if the
audit calls for programmatic pages, hreflang at scale, or edge redirects, note
the platform limit explicitly in the report rather than promising workarounds.

## 4. Cross-Platform Verification (Any CMS)

After implementing on any platform, verify from outside the CMS -- the admin UI
lies by omission:

```bash
curl -s https://client-site.com/ | grep -iE '<title>|meta name="description"|rel="canonical"|application/ld\+json'
curl -s https://client-site.com/robots.txt
curl -s -o /dev/null -w '%{http_code}' https://client-site.com/sitemap.xml
```

Then run the standard checks from `live-site-audit.md` (redirect consistency,
soft-404s, TTFB, PageSpeed field data) -- platform makes no difference to the
acceptance criteria.
