# React SPA SEO Implementation (Vite / CRA)

SEO guidance for client-side React apps that do NOT use a server-rendering
framework. Read this when the project is Vite or Create React App and the user
cannot (or will not) migrate to Next.js/Astro right now.

## 1. The Honest Reality Check (Tell the Client This First)

A client-rendered SPA serves an empty HTML shell; content appears only after
JavaScript executes.

- **Googlebot** renders JavaScript, but rendering is queued and delayed, and
  mistakes (blocked resources, render errors) silently produce blank pages in
  the index. [Standards-based -- Google documentation]
- **AI crawlers largely do NOT execute JavaScript.** GPTBot, ClaudeBot, and
  PerplexityBot read the raw HTML response. A pure SPA is effectively
  invisible to AI search. [Widely observed]

So the recommendation ladder, best to worst:

| Option | When |
|---|---|
| 1. Move public/marketing pages to SSG (Next.js, Astro) -- keep the app itself an SPA behind login | SEO matters and there is any budget. Split `www.domain.com` (static marketing) from `app.domain.com` (SPA) |
| 2. Prerender public routes at build time | Small, finite set of public routes; can't change stacks |
| 3. Server-side render the SPA with Vike (vite-plugin-ssr successor) | Vite project, dynamic public content, engineering capacity exists |
| 4. Dynamic rendering (prerender proxy for bots) | Last resort only -- Google now calls this a workaround, it adds infrastructure, and bot-detection lists go stale |

Never present option 4 as a long-term fix. If the audit finds a pure SPA with
SEO-critical content, that is a **Critical** finding regardless of how good the
meta tags are.

## 2. Meta Tag Management with react-helmet-async

`react-helmet` is unmaintained; use `react-helmet-async`.

```bash
npm install react-helmet-async
```

```tsx
// main.tsx
import { HelmetProvider } from 'react-helmet-async'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <HelmetProvider>
    <App />
  </HelmetProvider>
)
```

```tsx
// components/Seo.tsx
import { Helmet } from 'react-helmet-async'

interface SeoProps {
  title: string
  description: string
  path: string            // e.g. "/pricing"
  image?: string
  type?: 'website' | 'article'
  jsonLd?: Record<string, unknown>
}

const SITE = 'https://yourdomain.com'
const BRAND = 'YourBrand'

export function Seo({ title, description, path, image = '/og-default.png', type = 'website', jsonLd }: SeoProps) {
  const url = `${SITE}${path}`
  return (
    <Helmet>
      <title>{`${title} | ${BRAND}`}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={url} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={url} />
      <meta property="og:image" content={`${SITE}${image}`} />
      <meta property="og:type" content={type} />
      <meta property="og:site_name" content={BRAND} />
      <meta name="twitter:card" content="summary_large_image" />
      {jsonLd && (
        <script type="application/ld+json">
          {JSON.stringify(jsonLd).replace(/</g, '\\u003c')}
        </script>
      )}
    </Helmet>
  )
}
```

**Critical caveat:** without prerendering or SSR, Helmet updates tags in the
browser only. Crawlers that fetch raw HTML (all AI crawlers, social link
previews) see whatever is in `index.html`. Helmet alone fixes nothing for them
-- pair it with option 1-3 above, and say so in the audit.

## 3. Prerendering Public Routes (Vite)

For a finite set of public routes, prerender at build time so the served HTML
is complete. Approaches, in order of preference:

1. **Vike** (`vike`) -- full SSR/SSG for Vite with per-page `prerender` config
2. **A post-build prerender step** -- run the built app in headless Chromium
   (Playwright is preinstalled in many CI images) and snapshot each route's
   HTML into `dist/`

Minimal post-build snapshot script (concept):

```ts
// scripts/prerender.ts -- run after `vite build`, serves dist/ and snapshots routes
import { chromium } from 'playwright'
const routes = ['/', '/pricing', '/about', '/blog']
// for each route: page.goto(previewUrl + route) -> wait for content ->
// fs.writeFile(`dist${route}/index.html`, await page.content())
```

Verify prerendered output with `curl` -- the acceptance test is: **all
SEO-critical content and meta tags visible in the raw HTML response.**

## 4. SPA-Specific Audit Traps

- **Soft 404s everywhere.** SPA hosting rewrites all paths to `index.html`
  with HTTP 200, so `/any-garbage-url` returns 200. Fix: prerender a real 404
  page and configure the host (Netlify `_redirects`, Vercel config,
  `try_files` in nginx) to serve it with status 404 for unknown paths.
- **One title for every page** in `index.html` -- duplicate titles/descriptions
  across the whole site until Helmet runs.
- **robots.txt and sitemap.xml** -- put them in `public/`. Generate the sitemap
  in a build script from the route list; do not hand-maintain it.
- **Route-based code splitting** (`React.lazy`) helps LCP/INP but does not fix
  crawlability -- don't let performance wins mask the rendering problem.
- **Hash routing (`/#/pricing`)** is not indexable as separate pages. Migrate
  to history routing before doing anything else.

## 5. What to Put in the Audit Report

For a pure SPA, the findings block should look like:

1. **[Critical] Client-only rendering** -- invisible to AI crawlers, delayed/fragile
   for Google. Recommendation: split marketing pages to SSG (impact 5, effort 3-4).
2. **[Critical] Soft 404s** -- all unknown URLs return 200.
3. **[Important] Meta tags static in index.html** -- interim fix: react-helmet-async
   + prerendering of the top N public routes.

Frame the SSG migration as the roadmap's structural item (31-60 days) and
prerendering as the quick win (0-30 days).
