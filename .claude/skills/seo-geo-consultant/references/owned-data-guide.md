# Owned-Data Ingestion Guide

How the audit pipeline consumes data the client already owns — Search Console,
Screaming Frog, CrUX/PageSpeed, analytics, backlink tools. Owned data upgrades
findings from *inferred from code* to *data-backed*, and it is always optional:
**no department ever blocks on missing data.** If a file isn't there, proceed
without it and record the gap.

---

## 1. The `seo-data/` Convention

Look for a `seo-data/` directory in the audited project root (or a path the user
names). Match files by content and header row, not just filename — exports get
renamed. Typical drops:

| Data source | Typical files | Telltale headers/content |
|---|---|---|
| GSC Performance export | `gsc-performance*.csv`, `Queries.csv`, `Pages.csv` | `Query`/`Top queries`, `Clicks`, `Impressions`, `CTR`, `Position` |
| GSC Indexing/Coverage export | `Coverage.csv`, `gsc-pages*.csv` | `URL`, `Coverage`/`State`, `Last crawled` |
| Screaming Frog crawl | `internal_all.csv`, `internal_html.csv`, `page_titles*.csv`, `meta_description*.csv`, `response_codes*.csv`, `canonicals*.csv`, `redirect*chains*.csv` | `Address`, `Status Code`, `Indexability`, `Title 1`, `Canonical Link Element 1` |
| PageSpeed / CrUX | `psi*.json`, `crux*.csv/json`, Lighthouse JSON | `lighthouseResult`, `loadingExperience`, LCP/CLS/INP fields |
| Analytics export | `ga4*.csv`, `analytics*.csv`, `referrals*.csv` | `Session source`/`Source / medium`, `Sessions`, `Landing page` |
| Backlink tools | `ahrefs*.csv`, `semrush*.csv`, `backlinks*.csv` | `Referring page`, `Domain rating`, `Target URL` |
| Anything else | keyword lists, support-ticket exports, internal search logs | judge by content |

Rules for reading:
- **Record provenance on first read:** filename, export date range (from the file or
  its metadata), row count. Every claim derived from the file cites
  `filename (date range)`.
- **Data is a snapshot.** A 6-month-old Screaming Frog crawl describes the old site.
  If file dates and current code disagree, the code/live site wins — flag the
  discrepancy, don't average it.
- **Never fabricate rows.** If a needed column is absent, the analysis that needs it
  is simply not available.
- Large files: sample intelligently (top N by clicks/impressions, all non-200 rows,
  all duplicates) rather than reading every row.

## 2. Who Uses What

Departments read only the slices below — no department re-analyzes another's slice.

| Department | Files | What to extract |
|---|---|---|
| **Discovery** | all | Inventory only: what exists, dates, row counts → Data Inventory table in the brief. No analysis. |
| **Technical SEO** | Screaming Frog response codes / canonicals / redirect chains / indexability; GSC Coverage | Non-200 URLs at scale, canonical mismatches, redirect chains, noindexed-but-linked pages, sitemap vs crawl orphans, GSC excluded-page patterns |
| **On-Page** | Screaming Frog page titles / meta descriptions / h1 exports; GSC Performance | Duplicate/overlong titles and metas at scale; **title-rewrite candidates:** queries with position ≤ 10 and CTR clearly below what that position typically earns |
| **Structured Data** | Screaming Frog structured-data reports (if crawl ran with it) | Validation errors/warnings at scale, per-template coverage |
| **Performance** | PSI/Lighthouse/CrUX exports; Screaming Frog response times | Real field CWV per template (this replaces "needs field data"), slowest URL clusters |
| **GEO/AEO** | Analytics referrals; GSC Performance | AI-assistant referral traffic (chatgpt.com, perplexity.ai, copilot sources) as citation evidence; question-form brand queries |
| **Content Strategy** | GSC Performance; internal search logs; support/sales exports; keyword lists | Striking-distance queries (position 5–20 with impressions), query themes with no matching page, cannibalization (two URLs ranking for one query) |
| **Competitive Intel** | Backlink/visibility tool exports if provided | Client-vs-competitor gap only from real exports — never estimate a competitor's traffic |
| **Roadmap Director** | none directly | Reads departments' evidence classes; reports the Data Coverage line and what missing data would change |

## 3. Evidence Classes

Every finding in a Department Report carries one evidence class:

- **data-backed** — derived from an owned-data file (cite file + date range) or a
  direct live fetch.
- **inferred** — derived from reading code/templates; the pattern reliably produces
  the issue but no field data confirms scale.
- **needs-data** — a real question the audit cannot answer without a named export;
  list it in the report's data-request section with *exactly* what to export and
  what it would change.

Confidence tiers (evidence-policy.md) still apply on top: evidence class says *how we
know it's happening here*; confidence tier says *how established the recommendation
practice is*. A finding can be data-backed + Experimental, or inferred +
Standards-based.

## 4. Graceful Degradation (non-negotiable)

1. No data folder, no exports → run the full audit from code/live fetches exactly as
   before. This is normal, not an error.
2. Ask for data **once** at intake (pipeline Stage 1). Never re-ask mid-pipeline;
   never pause a department to wait for a file.
3. Corrupt/unreadable/ambiguous file → skip it, record it under Could Not Verify with
   the reason, continue.
4. Each department's report lists its top 1–3 **needs-data** requests. The director
   consolidates these into one client-facing data request for the next cycle —
   deduplicated, each with the expected payoff.
5. The Data Coverage line in the executive summary states plainly: which sources were
   provided, which findings are data-backed vs inferred, and the single most valuable
   missing export.
