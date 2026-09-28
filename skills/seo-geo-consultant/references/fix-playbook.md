# Fix Playbook

How to fix every check `seo-scan.py` reports, per stack, and how to prove the fix
worked. `/seo-fix` and the `seo-fix-engineer` agent work from this file; each
section's anchor is the scanner's check ID (`fix-playbook.md#canonical`).

The scanner decides **what** is broken and **where**. This file decides **how**.
The rendered output decides **whether it worked**.

---

## Rules that apply to every fix

1. **Confirm before editing.** Read the file the scanner points at and confirm the
   finding still holds. The source scan is heuristic; rendered evidence is not.
2. **Fix at the source, never in build output.** Edit `app/layout.tsx`, the Astro
   layout, the Hugo partial -- never `dist/`, `out/`, `.next/`, `_site/`, `public/`
   of a Hugo/Gatsby build. Static-HTML sites are the exception: there the HTML *is*
   the source.
3. **One source of truth per value.** Put the site URL, brand name and default
   image in one place (framework config, or a small `site` config module) and
   reference it. Scattering the domain across 30 files is how canonicals rot.
4. **Never invent facts.** Titles, descriptions and alt text are *derived from the
   page's own content* -- that is writing, and it is in scope. Phone numbers,
   addresses, prices, ratings, review counts, author credentials, founding dates,
   social profiles and logos are *facts*: use them only when they are in the
   codebase or the user supplied them. Missing fact -> omit the property, list it
   in the report.
5. **Match the codebase.** Same component patterns, quoting, formatting and file
   layout as the neighbouring code. Run the project's formatter if it has one.
6. **Preserve appearance.** SEO fixes should not change how the page looks. When
   demoting an `<h1>` to `<h2>`, keep its classes (and add one if CSS targets the
   tag). When adding image dimensions, keep `height: auto` responsive behaviour.
7. **Verify with the scanner, not by eye.** Rebuild, re-score with `--compare`,
   and read the diff. A check that did not move was not fixed.

## Fix classes

| Class | Meaning | `/seo-fix` behaviour |
|---|---|---|
| `auto` | Derived from the site itself; no business decision | Fixed without asking |
| `input` | Needs a fact (site URL, brand, image) | Fixed once the fact is known; asked **once**, all together |
| `review` | Changes behaviour, or is a business decision | Listed with its consequence; fixed only when approved |

The scanner can override a check's class for one project -- e.g. on a client-rendered
SPA, unique titles need prerendering, so `title-unique` becomes `review`.

## Facts

| Fact | Used by | Where to look first | If missing |
|---|---|---|---|
| `site_url` | base-url, canonical, sitemap, robots-sitemap, og-image, schema-org, llms-txt | `seo-scan.py detect` (config, CNAME, `.env*`, existing canonicals) | Ask. Never use a Vercel/Netlify preview URL unless the user confirms it is production |
| `brand` | title template, og:site_name, schema-org, llms-txt | detect (siteName, title template, manifest, config title) | Ask |
| `lang` | html-lang | detect; otherwise the language the copy is written in | Infer from the copy (that is observation, not invention) |
| `og_image` | og-image | detect (`og*.png`, `opengraph-image.*`) | Next.js: generate one (see [og-image](#og-image)); elsewhere ask |
| `icon` | favicon | detect (`favicon.*`, `icon.*`) | Ask; do not draw a logo |
| `logo` | schema-org `logo` | detect (`logo.*`) | Omit the property |
| `same_as` | schema-org `sameAs` | detect (social links already on the site) | Omit the property |

## Order of operations

Dependencies decide the order; the fix plan is sorted to respect them.

1. `server-rendered` first when it fails -- on a client-rendered SPA every other
   page-level fix is invisible to crawlers until content is in the HTML.
2. `base-url` before `canonical`, `og-image`, `sitemap-present`, `robots-sitemap`,
   `schema-org` -- they all resolve against it.
3. `schema-valid` before `schema-org` -- a broken block may already contain the entity.
4. Site files (`robots-*`, `sitemap-*`, `llms-txt`) are independent -- do them together.
5. Page metadata (`title*`, `description*`, `og-tags`, `twitter-card`) -- root
   defaults first, then per-page values.
6. Content hygiene (`h1`, `img-alt`, `img-dimensions`, `font-display`) last.

## Getting rendered evidence

`seo-scan.py detect` prints the exact commands for the project. The patterns:

| Stack | Build | Score |
|---|---|---|
| Next.js (server) | `npm run build` | `score . --serve "npx next start -p 4319" --url http://localhost:4319` |
| Next.js (`output: 'export'`) | `npm run build` | `score . --html out` |
| Vite / CRA | `npm run build` | `score . --html dist` (CRA: `build`) |
| Astro (static) | `npm run build` | `score . --html dist` |
| Gatsby / Hugo | build | `score . --html public` |
| Jekyll / Eleventy | build | `score . --html _site` |
| SvelteKit / Remix / SSR | `npm run build` | `score . --serve "<start cmd>" --url http://localhost:4319` |
| Static HTML | none | `score .` |
| No code (live site) | none | `score https://client.com` |

`--serve` starts the server, waits for it, scans and **always stops it** -- never leave
a background server running between tool calls. Pick a free port; if the scanner
says the port already answers, another server is on it (exit 7).

If dependencies are not installed and cannot be (no network, no lockfile), score
from source alone and say so: source-only results are heuristic.

---

## Crawl & index

### robots-present <a name="robots-present"></a>

`/robots.txt` must exist. Absent is not fatal (crawling is unrestricted by default)
but it leaves no sitemap pointer and no explicit AI-crawler policy.
[Confidence: Standards-based]

Content (merge with any existing rules -- never drop an existing `Disallow` without approval):

```
User-agent: *
Allow: /
Disallow: /api/        # only paths that exist and should stay private

# AI search and user-initiated fetchers -- these produce citations
User-agent: OAI-SearchBot
User-agent: ChatGPT-User
User-agent: Claude-SearchBot
User-agent: Claude-User
User-agent: PerplexityBot
User-agent: Perplexity-User
Allow: /

Sitemap: <site_url>/sitemap.xml
```

Consecutive `User-agent` lines form one group, so the block above allows all six
fetchers. Training crawlers (GPTBot, ClaudeBot, Google-Extended, CCBot) are a
licensing decision: leave whatever the site already does, and never add blocks
for them unasked.

| Stack | Where |
|---|---|
| Next.js App Router | `app/robots.ts` returning `MetadataRoute.Robots` (see `nextjs-implementation.md` §4) -- or `public/robots.txt` if the project already uses static files |
| Next.js Pages, Vite, CRA, Astro, Nuxt, Remix | `public/robots.txt` |
| SvelteKit, Gatsby, Docusaurus, Hugo | `static/robots.txt` (Hugo alternative: `enableRobotsTXT = true` + `layouts/robots.txt`) |
| Jekyll, Eleventy, static HTML | `robots.txt` at the site root (Eleventy: add a passthrough copy) |
| WordPress | SEO plugin's robots editor, or a physical `robots.txt` in the web root |
| Shopify | `templates/robots.txt.liquid` -- extend `{{ robots.default_groups }}`, do not replace it |

**Verify:** rendered `robots-present`, `robots-syntax`, `ai-crawlers` pass.

### robots-search-open <a name="robots-search-open"></a> -- review

Googlebot or Bingbot is blocked at `/`. Usually a staging `Disallow: /` that shipped
to production; occasionally deliberate (an app behind login). **Ask before changing.**
State the consequence plainly: while it stands, the site cannot rank at all.
Fix by removing the blanket `Disallow: /` for `*` (or the named bot) and keeping
only the private paths. If the file is generated per environment, fix the
environment switch, not the output.

### robots-syntax <a name="robots-syntax"></a>

Unknown directives and rules before any `User-agent` are ignored by crawlers --
the author's intent silently does nothing. Fix each reported line: typo'd field
names (`Dissallow`), rules above the first `User-agent`, missing colons.

### robots-sitemap <a name="robots-sitemap"></a> -- input: site_url

Add `Sitemap: <site_url>/sitemap.xml` -- an **absolute** URL; relative values are
invalid. In `app/robots.ts`: `sitemap: \`${SITE_URL}/sitemap.xml\``.

### sitemap-present <a name="sitemap-present"></a> -- input: site_url

| Stack | Fix |
|---|---|
| Next.js App Router | `app/sitemap.ts` listing every public route; dynamic routes from the same data source the pages use (`nextjs-implementation.md` §3) |
| Next.js Pages | `next-sitemap` (postbuild) or `pages/sitemap.xml.ts` with `getServerSideProps` writing XML |
| Astro | `@astrojs/sitemap` integration (needs `site` in `astro.config`) |
| Nuxt | `@nuxtjs/sitemap` module (needs site url) |
| SvelteKit | `src/routes/sitemap.xml/+server.ts` returning XML with `content-type: application/xml` |
| Gatsby | `gatsby-plugin-sitemap` (needs `siteMetadata.siteUrl`) |
| Hugo | built in -- confirm `sitemap` is not in `disableKinds` |
| Jekyll | `jekyll-sitemap` plugin |
| Eleventy | a `sitemap.njk` template with `permalink: /sitemap.xml` over `collections.all` |
| Vite / CRA | generate `public/sitemap.xml` in a build script from the route list -- do not hand-maintain it |
| Static HTML | write `sitemap.xml` listing every page file's URL |
| WordPress / Shopify | built in (`/wp-sitemap.xml` or the SEO plugin's; Shopify `/sitemap.xml`) -- just reference it |

Exclude noindex pages, redirects, 404s and parameter URLs. **Verify:** the
rendered sitemap lists production URLs (`sitemap-present` fails on localhost or
placeholder hosts).

### sitemap-lastmod <a name="sitemap-lastmod"></a>

`lastModified: new Date()` stamps every URL with the build time; crawlers learn to
ignore lastmod that is not trustworthy. [Confidence: Standards-based -- Google
documents that it uses lastmod only when it is consistently accurate.]
Use a real change date (content front matter `updated`/`date`, CMS `updatedAt`,
or `git log -1 --format=%cI -- <file>` at build time). If no honest date exists,
**omit** lastmod rather than fake it -- the scanner passes an absent lastmod and
warns only on dates that are all identical.

### not-found <a name="not-found"></a>

Unknown URLs must answer HTTP 404 (or 410), not 200 with a "not found" page.

| Stack | Fix |
|---|---|
| Next.js | returns 404 by default; add `app/not-found.tsx` only for branding |
| Astro / Gatsby / Nuxt / SvelteKit | `src/pages/404.astro` · `src/pages/404.js` · `error.vue` · `src/routes/+error.svelte` |
| Hugo / Jekyll / static | `404.html` at the output root (most static hosts serve it with status 404) |
| Vite / CRA SPA | host config -- review: Netlify `/* /index.html 200` rewrites everything to 200; prerender known routes and configure the host to 404 unknown ones |

### noindex-sitewide <a name="noindex-sitewide"></a> -- review

A root-level `noindex` (Next.js root `robots: { index: false }`, a layout `<meta
name="robots" content="noindex">`, an `X-Robots-Tag` header, WordPress "Discourage
search engines") removes every page from search. Confirm with the user whether the
site is meant to be public; if yes, remove it at the root and keep `noindex` only
on the pages that need it (admin, search results, thank-you pages).

---

## Metadata

### base-url <a name="base-url"></a> -- input: site_url

| Stack | Setting |
|---|---|
| Next.js App Router | `metadataBase: new URL(SITE_URL)` in the root layout's `metadata` |
| Astro | `site: 'https://…'` in `astro.config.*` |
| Nuxt | `site: { url }` (Nuxt SEO) or `runtimeConfig.public.siteUrl` |
| Gatsby | `siteMetadata.siteUrl` |
| Docusaurus | `url` |
| Hugo | `baseURL = 'https://…/'` |
| Jekyll | `url: "https://…"` in `_config.yml` |
| Everything else | one exported `SITE_URL` constant (e.g. `src/lib/site.ts`), read from an env var when the project already uses env config |

Never hardcode `localhost`, a preview URL or a placeholder.

### title <a name="title"></a>

Every indexable page needs a unique, descriptive `<title>`: primary topic first,
brand last, 50-60 characters as a target (the scanner flags outside 15-65).
**Write it from the page's own H1 and copy** -- no claims the page does not make.
Check the length before writing it: `python3 <SCAN> len "Candidate title" "Candidate description"`.
Homepage: `Brand -- what it is / for whom`. Starter titles (`Create Next App`,
`Vite + React`, `Home`) always fail.

| Stack | Pattern |
|---|---|
| Next.js App Router | root: `title: { default: 'Brand -- value prop', template: '%s \| Brand' }`; each page: `export const metadata = { title: 'Page topic' }`; dynamic routes: `generateMetadata` |
| Next.js, `'use client'` page | a client component cannot export metadata: add a `layout.tsx` beside it that exports `metadata`, or move the client part into a child component |
| Next.js Pages | `<Head><title>…</title></Head>` per page, or next-seo `<NextSeo title>` |
| Vite / CRA | default in `index.html`; per route with `react-helmet-async` -- visible to crawlers only with prerendering ([server-rendered](#server-rendered)) |
| Astro | pass `title` to the layout; layout renders `<title>{title} \| {BRAND}</title>` |
| Nuxt | `useSeoMeta({ title })` per page; `titleTemplate` in `app.head` or `useHead` |
| SvelteKit | `<svelte:head><title>…</title></svelte:head>` per route |
| Gatsby | `export const Head = () => <title>…</title>` per page |
| Hugo | head partial: `{{ if .IsHome }}{{ site.Title }}{{ else }}{{ .Title }} \| {{ site.Title }}{{ end }}` |
| Jekyll | `jekyll-seo-tag` (`{% seo %}`) + front-matter `title` |
| Eleventy | layout `<title>{{ title }} \| {{ site.name }}</title>` + front matter |
| Static HTML | edit `<title>` in each file |
| WordPress | theme `add_theme_support( 'title-tag' )`; titles via the SEO plugin's templates |
| Shopify | `layout/theme.liquid`: `<title>{{ page_title }}{% unless page_title contains shop.name %} -- {{ shop.name }}{% endunless %}</title>` |

### title-unique <a name="title-unique"></a>

The scanner lists pages that share a title (rendered) or routes that inherit the
root default (Next.js source). Give each its own title per [title](#title). On a
client-rendered SPA this is `review`: it needs prerendering, not just a head manager.

### description <a name="description"></a>

A 140-160 character summary of **what the page actually says**, with a reason to
click. Not a ranking factor, but it is the snippet people read. Same placement as
titles (`description` in Next.js metadata, `<meta name="description">` elsewhere,
`useSeoMeta({ description })`, front matter `description` for Hugo/Jekyll/Eleventy/
Astro content). Replace starter text (`Generated by create next app`).

### description-unique <a name="description-unique"></a>

As [title-unique](#title-unique), for descriptions.

### canonical <a name="canonical"></a> -- input: site_url

Every indexable page declares its own absolute URL. The scanner fails pages that
are missing one, point at a placeholder/local host, or -- the dangerous case --
several pages that all point at one URL.

| Stack | Pattern |
|---|---|
| Next.js App Router | root layout: `metadataBase` + `alternates: { canonical: './' }`. `'./'` resolves to each route's own URL (verified on Next.js 15.5, Sep 2026). **Never `canonical: '/'` in the root layout** -- every page that does not override it inherits it and declares itself a duplicate of the homepage (verified, same build). Pages with query-driven variants override with an explicit path |
| Next.js Pages | in `_app` or a `Seo` component: `<link rel="canonical" href={SITE_URL + (router.asPath.split(/[?#]/)[0])} />` |
| Astro | layout: `<link rel="canonical" href={new URL(Astro.url.pathname, Astro.site)} />` |
| Nuxt | Nuxt SEO adds it; otherwise `useHead({ link: [{ rel: 'canonical', href: SITE_URL + route.path }] })` |
| SvelteKit | `+layout.svelte`: `<link rel="canonical" href={SITE_URL + page.url.pathname} />` (`page` from `$app/state`; `$page` from `$app/stores` before Svelte 5) |
| Gatsby | in `Head`: `siteUrl + location.pathname` |
| Hugo | `<link rel="canonical" href="{{ .Permalink }}">` |
| Jekyll | `{% seo %}`, or `<link rel="canonical" href="{{ page.url \| absolute_url }}">` |
| Eleventy | `<link rel="canonical" href="{{ site.url }}{{ page.url }}">` |
| Static HTML | one absolute `<link rel="canonical">` per file |
| Vite / CRA | per route via the head manager **plus** prerendering. Never a canonical in `index.html` for a multi-route SPA -- every route would canonicalize to the homepage |
| WordPress / Shopify | core/plugin and `{{ canonical_url }}` handle it; fix the settings, not the template |

Use the same host form everywhere (https, www or apex as production redirects to).

### html-lang <a name="html-lang"></a>

`<html lang="…">` with the language of the copy (`en`, `en-GB`, `de`). Next.js:
root layout `<html lang="en">`; Pages Router: `pages/_document` `<Html lang="en">`;
Nuxt: `app.head.htmlAttrs.lang`; SvelteKit: `src/app.html`; Gatsby:
`gatsby-ssr` `setHtmlAttributes`; Hugo: `<html lang="{{ site.Language.LanguageCode }}">`;
Jekyll: `lang: en` in `_config.yml` + layout; static: every file.

### viewport <a name="viewport"></a>

`<meta name="viewport" content="width=device-width, initial-scale=1">` in the head
template (Next.js adds it automatically). Mobile-first indexing evaluates the
mobile rendering. [Confidence: Standards-based]

### favicon <a name="favicon"></a> -- input: icon

Next.js App Router: put the icon file at `app/icon.png` (or `.svg`, or
`app/favicon.ico`) -- the file convention emits the tags. Elsewhere:
`<link rel="icon" href="/favicon.ico">` (plus `apple-touch-icon` when the asset
exists). Use the client's existing icon or logo asset; never draw one.

---

## On-page structure

### h1 <a name="h1"></a>

Exactly one `<h1>` naming the page's topic.
- **Two or more:** keep the one that names the page; demote the rest to `<h2>`
  (keep their classes; if CSS styles `h1` by tag, add a class that preserves the look).
- **None:** promote the element that already acts as the page title (often an
  `<h2>` or a styled `<div>`/`<p>` in a hero) -- do not add new visible text.
- In a shared layout, a logo wrapped in `<h1>` on every page is the usual cause:
  make it a `<div>`/`<a>` and let each page own its H1.

### img-alt <a name="img-alt"></a>

Every `<img>` needs an `alt` attribute.
- Informative image: describe what it shows *in context*, 5-15 words, from the
  filename, caption and surrounding copy. No "image of", no keyword stuffing.
- Decorative (spacer, background flourish, icon next to text that says the same
  thing): `alt=""` -- empty, not missing.
- Next.js `<Image>` requires `alt`; same rules.

### img-dimensions <a name="img-dimensions"></a>

Images without `width`/`height` shift the layout as they load (CLS).
Run `python3 <SCAN> imgsize <file>` for each image's intrinsic size and add
matching `width`/`height` attributes; keep responsive CSS (`max-width: 100%;
height: auto`) so it still scales. Next.js: `<Image width height>` or `fill` in a
sized parent.

---

## Structured data

### schema-valid <a name="schema-valid"></a>

A JSON-LD block that does not parse is ignored entirely. The scanner gives the
block number and the parser's line/column. Common causes: trailing commas,
unescaped quotes in copy, template variables that render empty (`"name": ,`),
HTML entities. Fix at the template/component, re-render, re-scan.
Generate JSON-LD with `JSON.stringify` (or the platform's JSON filter:
`| jsonify`, `| json`, `{{ . | jsonify }}`), never by string concatenation.

### schema-escape <a name="schema-escape"></a>

JSON-LD injected with `dangerouslySetInnerHTML`/`set:html`/`v-html`/`{@html}` must
escape `<`, or a `</script>` inside any string value breaks out of the tag:

```tsx
dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, '\\u003c') }}
```

### schema-org <a name="schema-org"></a> -- input: brand, site_url

Homepage JSON-LD with an Organization-type entity **and** a WebSite entity. Use
`schema-templates.md` (Organization §1; LocalBusiness §10 for local businesses --
pick the most specific subtype, e.g. `Plumber`, `Dentist`). Fill only real values:

```json
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Organization", "@id": "<site_url>/#organization", "name": "<brand>",
      "url": "<site_url>/", "logo": "<site_url>/<logo>", "sameAs": ["<same_as…>"] },
    { "@type": "WebSite", "@id": "<site_url>/#website", "name": "<brand>",
      "url": "<site_url>/", "publisher": { "@id": "<site_url>/#organization" } }
  ]
}
```

Omit `logo`/`sameAs` when those facts are missing. A LocalBusiness additionally
needs a real address and phone -- `input`, never invented. Do not add
`SearchAction` unless the site has a working search URL.

Placement: Next.js -> a `JsonLd` component in `app/page.tsx` (or the root layout
for site-wide entities); Astro/Vue/Svelte -> the home page or base layout; Hugo/
Jekyll/Eleventy -> the home template; static -> `index.html` `<head>`; WordPress ->
SEO plugin settings first, custom `wp_head` hook only for what it lacks; Shopify ->
`theme.liquid`, checking the theme does not already emit one.

### schema-article <a name="schema-article"></a>

Pages under `/blog/`, `/news/`, `/articles/`, `/posts/`, `/guides/` need `Article`
or `BlogPosting` with `headline`, `datePublished`, `dateModified` (real dates from
front matter/CMS), `author` (`Person` with the real name when the content names
one), `image` when the post has one, `mainEntityOfPage`. Generate it in the post
template from the post's data -- never per post by hand. No author in the data ->
use the Organization as `author`/`publisher` and list "named authors" in the report.

---

## Social sharing

### og-tags <a name="og-tags"></a>

`og:title`, `og:description`, `og:type` on every page (and `og:url`, `og:site_name`).

- **Next.js App Router:** root layout `openGraph: { type: 'website', siteName: BRAND, url: './' }`
  and **no** `openGraph.title`/`description`. With that, Next.js fills `og:title` and
  `og:description` from each page's own `title`/`description`, and `url: './'`
  resolves per route (verified on Next.js 15.5, Sep 2026). A root
  `openGraph.title` would be inherited by every page that does not override the
  whole `openGraph` object. Article pages set `openGraph: { type: 'article', … }` in
  `generateMetadata`.
- **Everything else:** emit them in the same head template/component as the title,
  from the same variables, so they can never drift.

### og-image <a name="og-image"></a> -- input: og_image

An absolute `og:image` (1200x630) for link previews.
- Existing asset (`og_image` fact): reference it (Next.js: `openGraph.images`, or
  copy it to `app/opengraph-image.png`).
- **Next.js with no asset:** `app/opengraph-image.tsx` with `ImageResponse` from
  `next/og`, rendering the brand name and the page title as text on a plain
  background (`nextjs-implementation.md` §6). That is derived from existing facts,
  so it counts as `auto` once `brand` is known.
- Other stacks with no asset: ask for one; do not fabricate artwork.
- Relative or `localhost` og:image URLs mean `base-url` is missing.

### twitter-card <a name="twitter-card"></a>

`<meta name="twitter:card" content="summary_large_image">` (or `summary` without an
image). Next.js: root `twitter: { card: 'summary_large_image' }` -- title,
description and image fall back to the Open Graph values. Add `twitter:site` only
with a real handle from `same_as`.

---

## AI search (GEO)

### llms-txt <a name="llms-txt"></a> -- input: brand, site_url

A Markdown file at `/llms.txt` (static file in the web root; Next.js `public/llms.txt`).
[Confidence: Experimental -- a proposed convention; not confirmed to be read by
major AI crawlers as of 2026. Cheap, so it is in scope.] Build it from the site's
real pages -- titles and descriptions from the scan's page table:

```markdown
# <brand>

> <one-sentence description taken from the homepage copy>

## Key pages
- [<page title>](<site_url>/<path>): <its meta description>
```

No invented claims, no competitor comparisons unless the site itself makes them.

### ai-crawlers <a name="ai-crawlers"></a> -- review

An AI *search* or *user-initiated* fetcher (OAI-SearchBot, ChatGPT-User,
Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User) is blocked. That
removes the site from those assistants' cited answers. It may be deliberate: ask,
then allow them as in [robots-present](#robots-present). Training crawlers are
reported but never changed without an explicit instruction.

### server-rendered <a name="server-rendered"></a> -- review

The page's text only exists after JavaScript runs. Search crawlers render it late
and imperfectly; AI crawlers largely do not execute JavaScript. [Confidence:
Widely observed -- see `react-spa-implementation.md` §1.] Fix options, cheapest
first -- present them, let the user choose:

1. **Prerender public routes at build time** (Vite: `vite-react-ssg`/`vike`
   prerender, or a Playwright snapshot step -- `react-spa-implementation.md` §3).
2. **Move marketing pages to a static/SSR framework** (Next.js, Astro) and keep the
   app behind login as an SPA.
3. Nuxt `ssr: false` / SvelteKit `export const ssr = false`: remove the flag for
   public routes (check why it was set first -- browser-only libraries).

This is structural: approve it separately, implement on its own, verify that the
rendered HTML now carries the copy (`server-rendered` pass, word counts in the page
table), then re-run the page-level fixes.

---

## Performance hygiene

### font-display <a name="font-display"></a>

Append `&display=swap` to Google Fonts stylesheet URLs so text renders while the
font downloads. In Next.js, `next/font` does this and self-hosts -- converting is a
small, safe change, but it touches styling, so keep it to the URL parameter unless
approved.

### next-image <a name="next-image"></a> -- review

Raw `<img>` in a Next.js app misses automatic sizing, lazy loading and modern
formats. Converting needs each image's dimensions (`imgsize`) or a sized parent
for `fill`, and remote images need `images.remotePatterns` in `next.config`. It
can change layout, so it is `review`: convert only when approved, then check
the page visually or against a screenshot.

---

## Live site, no code access (fix pack)

When `/seo-fix` gets a URL and no codebase, nothing can be edited directly. Produce
a **fix pack** instead -- a folder the client or their developer applies:

```
seo-fix-pack/<domain>/
  README.md          what to change, in order, per platform (WordPress plugin
                     settings, Shopify theme files, Webflow/Squarespace/Wix panels)
  robots.txt         the live file merged with the fixes above -- never a blank slate
  llms.txt           built from the crawled pages
  schema/home.jsonld.html   <script type="application/ld+json"> ready to paste
  meta/pages.csv     url, current title, proposed title, current description, proposed description
```

Every proposed value follows the rules above: derived from the page's own content,
facts only when verified. Platform instructions come from `cms-implementation.md`.
Re-score the live URL after the client applies the pack to report the change.
