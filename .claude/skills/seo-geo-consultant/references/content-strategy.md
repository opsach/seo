# Keyword & Content Strategy

The strategic layer that decides WHAT to create before the technical layer
optimizes it. Read this when the user asks about keyword research, content
planning, topic clusters, "what should we write", internal linking strategy,
or why traffic is flat despite clean technical SEO.

## 1. Search Intent First

Every target query maps to one of four intents, and intent dictates the page
type. Mismatched intent is the most common reason a technically fine page
doesn't rank.

| Intent | User wants | Page type that wins | Example query |
|---|---|---|---|
| Informational | An answer or explanation | Guide, blog post, glossary entry | "what is data orchestration" |
| Commercial investigation | To compare options | Comparison page, "best X" list, case study | "best crm for restaurants" |
| Transactional | To buy/sign up now | Product, pricing, landing page | "acme crm pricing" |
| Navigational | A specific site | Brand homepage, login | "acme login" |

Check intent empirically: search the query and look at what already ranks. If
the SERP is all comparison lists, a product page will not rank there --
build the page type the SERP demands.

**GEO overlay:** AI assistants collapse the funnel -- a single conversational
query ("what should I use for X, and how much does it cost?") mixes intents.
This is why comparison content and concrete pricing on your own pages earn
outsized AI citations (see `geo-optimization.md`).

## 2. Keyword Research Process

Work from data the client already owns outward:

1. **Google Search Console (first, always)** -- Queries report, filter to
   positions 5-20: these are "striking distance" terms where improving an
   existing page beats writing a new one. Also mine queries with high
   impressions and low CTR (title/description problem, not content problem).
2. **Autocomplete + People Also Ask** -- type seed terms into Google/Bing;
   collect the question variants. PAA questions are direct H2 candidates and
   AI-prompt proxies.
3. **Competitor gap** -- for the top 3 competitors, list what they rank for /
   get cited for that the client doesn't (tooling if available; manual SERP
   checks if not).
4. **Sales/support mining** -- questions from sales calls and support tickets
   are pre-validated commercial queries phrased in the customer's own words.
   This is the highest-signal source for AI-assistant phrasing.
5. **AI-prompt set** -- reuse the 20-30 tracked prompts from
   `aeo-measurement-template.md` as first-class keyword targets.

### Prioritization

Score each candidate: **relevance to offer (1-5) x business value of the
searcher (1-5) / difficulty (1-5)**. Rank by score; be honest about difficulty
-- a new domain does not win "crm" head terms, it wins long-tail and
comparison queries. Volume estimates from third-party tools are directional,
not facts; never present them to clients as measurements.

## 3. Topic Clusters (Hub and Spoke)

Organize content into clusters, not one-off posts:

- **Pillar page** -- comprehensive "What is [category]" / "[Category] guide"
  page targeting the head term. This is also your category-defining GEO asset.
- **Cluster pages** -- each targets one specific subtopic/long-tail query
  (one page = one primary query; multiple pages on the same query cannibalize).
- **Linking rule** -- every cluster page links up to the pillar with
  descriptive anchor text; the pillar links down to every cluster page.
  Cluster pages link sideways only when genuinely relevant.

A cluster is the unit of authority: search engines and AI systems both reward
sites that cover a topic completely over sites with scattered posts.

## 4. Content Brief Template

Produce one of these before any page is written:

```markdown
## Content Brief: [working title]
- Primary query: [one query] | Intent: [type] | Cluster: [pillar it belongs to]
- Secondary queries: [2-5 variants to weave in naturally]
- Page type: [guide / comparison / landing / glossary]
- Target reader: [who + what they already know]
- The ONE question this page answers: [state it]
- Answer-first opening: [the 40-60 word direct answer -- draft it in the brief]
- H2 outline: [question-style headings, each a self-contained 120-180 word section]
- Entities to include: [products, standards, people, competitors]
- Facts/stats needed: [with sources -- per evidence-policy.md]
- FAQs (3-5): [from PAA + sales questions -> FAQPage schema]
- Schema: [types from schema-templates.md]
- Internal links: [up to pillar, sideways to N cluster pages, with anchors]
- Author: [named, credentialed -- no "content team"]
- Refresh owner + next review date: [per the 3-month freshness cycle]
```

## 5. Internal Linking Architecture

- Every page reachable within 3 clicks of the homepage
- Descriptive anchors ("restaurant lead scoring guide", never "click here")
- Fix orphans first: pages with zero internal inbound links are invisible
  regardless of quality -- cross-check sitemap vs crawl
- Money pages (pricing, product, comparisons) deserve the most internal links;
  blog posts should funnel toward them
- Navigation and footer links are sitewide -- reserve those slots for the
  pages that matter commercially

## 6. Cannibalization & Consolidation

Symptoms: two URLs alternating in rankings for one query, or several thin
posts on near-identical topics. Fix by consolidating: keep the strongest URL,
merge unique content into it, 301 the rest to it. One strong page beats three
weak ones for both Google rankings and AI citation probability.

## 7. Editorial Cadence That Feeds GEO

- **Refresh beats net-new** once core clusters exist -- update statistics,
  dates, screenshots quarterly (`dateModified` + visible "Last updated")
- Each quarter, let the AEO measurement results (`aeo-measurement-template.md`)
  pick priorities: prompts where competitors get cited and you don't define
  the next brief
- Maintain the off-site half in the same calendar: directory listings,
  community answers, and syndication (see `geo-optimization.md`, Off-Site GEO)
