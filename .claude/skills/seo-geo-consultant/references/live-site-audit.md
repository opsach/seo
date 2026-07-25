# Live Site Audit (URL Only)

Procedure for auditing a site when you only have a URL -- no codebase access.
Use for prospect audits, client pitches, and competitor benchmarking. Output the
findings through `audit-report-template.md` exactly like a codebase audit, and
explicitly flag anything that could not be verified without code access.

**The one rule that matters:** every value in the report must have been *measured*.
An SEO audit is a claim about specific bytes a server sent. If you did not see those
bytes, you do not have a finding -- you have a guess, and a guess in a client
deliverable is worse than a blank line.

---

## 0) Preflight -- always first, no exceptions

```bash
# Find the toolkit (works for plugin, project .claude/, or user ~/.claude/ installs)
for d in "$CLAUDE_PLUGIN_ROOT" .claude ../.claude "$HOME/.claude" $(ls -dt "$HOME"/.claude/plugins/cache/*/seo-geo-consultant/*/ 2>/dev/null); do
  [ -n "$d" ] && [ -d "$d/skills/seo-geo-consultant/references" ] || continue
  k=$(cd "$d" && pwd)
  echo "REFERENCES: $k/skills/seo-geo-consultant/references"
  ls "$k/scripts/seo-probe.py" "$k/skills/seo-geo-consultant/scripts/seo-probe.py" 2>/dev/null | head -1 | sed 's/^/PROBE:      /'
  exit 0
done
echo "PLUGIN FILES NOT FOUND" >&2; exit 1
```

Note the absolute paths it prints -- shell variables do not survive between tool
calls, so use the printed `PROBE` path literally from here on:

```bash
python3 /abs/path/to/seo-probe.py preflight https://example.com
```

| Exit | Meaning | What to do |
|---|---|---|
| 0 | Fetching works | Continue to step 1 |
| 3 | **Blocked by network policy** -- the egress proxy refused the tunnel | **Stop.** Report the blocked host and the remediation the probe prints. Do not retry, do not switch to WebFetch, do not infer findings |
| 4 | **Blocked by the site** -- bot protection returned 403/429 | Report it as a finding (AI crawlers are refused the same way). Never try to defeat the protection |
| 5 | Unreachable -- DNS, TLS, or timeout | Report the exact error; confirm the domain with the client |

### Exit 3 in detail: sandboxed environments

This is the most common reason a live audit fails, and it is an environment
permission, not a fault in the plugin or the client's site. Claude Code on the web
runs in a sandbox whose **network policy** is chosen when the environment is created;
if the policy does not allow the client's domain, every fetch -- `curl`, `WebFetch`,
and this probe alike -- is refused before it leaves the machine.

Resolve it one of three ways:

1. Change the environment's network access setting (or add the client domain to its
   allowlist) and start a new session --
   see <https://code.claude.com/docs/en/claude-code-on-the-web>.
2. Run the audit from Claude Code CLI on a machine with normal internet access.
3. Switch to **owned-data mode**: ask the client for Search Console, Screaming Frog,
   and PageSpeed exports and audit those instead (`owned-data-guide.md`). This is
   often *better* evidence than fetching -- it covers the whole site, not a sample.

Say which of these you need. Never quietly downgrade to an audit of remembered facts
about the brand.

---

## 1) Collect the evidence pack

One command covers preflight, canonicalisation, robots, sitemap, llms.txt, and a
representative page sample -- roughly 12 requests total:

```bash
python3 /abs/path/to/seo-probe.py site https://example.com -n 5
```

Run the pieces individually when you only need one domain:

```bash
seo-probe.py redirects example.com      # http/https x www/apex matrix + soft-404 probe
seo-probe.py robots  https://example.com # per-crawler ALLOWED/BLOCKED with line numbers
seo-probe.py sitemap https://example.com # URL count, lastmod honesty, path groups
seo-probe.py page    https://example.com/pricing        # full SEO fact table
seo-probe.py page    https://example.com/pricing --json # same, machine-readable
```

Useful flags:

- `--ua googlebot` -- re-probe as Googlebot. A different response for Googlebot than
  for a generic agent is cloaking or bot-gating; both are findings.
- `--ua gptbot` -- check whether AI crawlers are served differently at the edge, which
  robots.txt alone will not reveal.
- `--out DIR` -- save the raw HTML so you can grep it for anything the probe does not
  summarise.
- `-n N` -- how many sitemap URLs to sample (default 5, max 25).

### What the probe measures per page

Status and full redirect chain, TTFB, HTML bytes, `title` (+ length), meta
description (+ length), canonical, meta robots, `X-Robots-Tag`, `html lang`, H1 count
and full heading outline, body word count, share of sections in the 120-180 word AI
extraction band, JSON-LD `@type`s and parse errors with positions, `og:`/`twitter:`
coverage, hreflang alternates, image alt gaps, script weight, compression, cache
headers, CDN cache status -- and a **rendering verdict**: is the primary content in
the raw HTML, or is the body an empty SPA mount point?

That rendering verdict is usually the single most valuable line in a URL-only audit.
Client-only rendering is a Critical finding for both SEO and GEO: search crawlers
render it late and inconsistently, and most AI crawlers do not execute JavaScript
at all.

---

## 2) Tool discipline

| Tool | Use it for | Never use it for |
|---|---|---|
| `seo-probe.py` | Every tag-level, status-level, and header-level fact | -- |
| `curl` | Anything the probe does not cover (specific headers, POST behaviour, alternate paths) | -- |
| `WebFetch` | Reading *visible prose* -- tone, claims, whether a page answers a question | `<title>`, meta, canonical, hreflang, `og:*`, JSON-LD, status codes, redirect chains, rendering checks |
| `WebSearch` | Off-site presence, brand mentions, directory listings | Any on-site fact |

WebFetch converts pages to markdown through a summarising model. Everything an SEO
audit is *about* lives in the parts that conversion discards. Citing WebFetch for a
meta-tag finding is how audits end up asserting tags that are not there.

---

## 3) Read what the probe cannot judge

The probe measures; you interpret. After the evidence pack, review by hand:

- **Copy quality** -- is the title compelling as well as correctly sized? Does the
  description earn a click, or just repeat the title?
- **Search intent match** -- does the page answer what someone searching that query
  actually wants?
- **Content structure for AI** -- are sections self-contained? Does each open with
  the answer in the first 40-60 words? (The probe reports the word-count distribution;
  you judge whether the sections stand alone.)
- **E-E-A-T signals** -- named, credentialed authors; visible "last updated" dates;
  cited sources; original data.
- **Schema correctness beyond parsing** -- the probe proves the JSON-LD parses and
  reports its types. You check whether the types are *right* for the page and whether
  required properties are present (`schema-templates.md`).

---

## 4) Off-site GEO spot-check

Search-based, so it works even when direct fetching is blocked:

- SaaS: G2, Capterra, ProductHunt, AlternativeTo listings; Reddit and Hacker News
  mentions; comparison articles that rank for "[brand] vs [competitor]".
- Local: Google Business Profile completeness, Yelp, industry directories, NAP
  consistency across them.
- Both: does the brand appear in the "best X for Y" listicles that AI assistants
  summarise when answering category questions?

Only ~11% of domains overlap between ChatGPT and Perplexity citations -- what third
parties say about a brand matters as much as its own site.

---

## 5) Report

Use `audit-report-template.md`. Additional rules for URL-only audits:

- Add a **"Not verifiable without code access"** list -- exact rendering strategy,
  redirect configuration, image pipeline, middleware, server config. Never guess these.
- Every finding cites the URL, the observed value, and the date of the check.
- State the sample: "5 of 412 sitemap URLs probed on 2026-07-25" is honest;
  "site-wide" is not, unless you probed site-wide.
- Pitch framing: lead with the three highest-impact fixes and estimate effort
  assuming no codebase familiarity.

---

## Limits

- Keep to ~10-15 requests per site, and fewer for competitors. `site -n 5` is one pass.
- Never attempt to bypass bot protection (Cloudflare challenges, CAPTCHAs, rate
  limits). If the site blocks you, that is the finding.
- Field data (CrUX) exists only for sites with enough traffic. Say so when it is
  missing rather than silently substituting lab scores.
- The probe reads the DOM the server sent. It does not execute JavaScript -- which is
  precisely why it detects client-rendering. To see the rendered DOM, you need a
  headless browser; note the difference rather than conflating the two.

## PageSpeed field data (optional, needs network access)

```bash
curl -sS "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://example.com&strategy=mobile" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); le=d.get('loadingExperience',{}).get('metrics',{}); print(json.dumps({k:v.get('percentile') for k,v in le.items()}, indent=2))"
```

Prefer this real-user field data over lab scores in the report. No API key is needed
at low volume. If the call is blocked by the same egress policy as everything else,
record CrUX as unavailable -- do not substitute an estimate.
