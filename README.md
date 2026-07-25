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

**One command.** Pick the line matching where you run Claude Code. Both are safe to
re-run, and both finish by proving the install can actually run an audit -- not just
that files landed.

### Claude Code CLI or desktop -- register it as a plugin

```bash
curl -fsSL https://raw.githubusercontent.com/opsach/seo/main/scripts/install.sh | bash -s -- --plugin
```

This runs `marketplace add` and `install` for you **in the required order** (the
ordering trap below is the single most common install failure), confirms the plugin
appears in `claude plugin list`, then checks that `python3` and the evidence probe
really execute. Re-running it is a no-op on an already-installed plugin.

> **Plugin commands are namespaced.** After this route the commands are
> `/seo-geo-consultant:seo-audit`, `/seo-geo-consultant:seo-pipeline`, and
> `/seo-geo-consultant:aeo-plan`. The bare `/seo-audit` returns *"Unknown command"* --
> that is the namespace, not a broken install. The file route below is the one that
> gives you the short names.

### Claude Code on the web, or to commit the setup into a repo

```bash
curl -fsSL https://raw.githubusercontent.com/opsach/seo/main/scripts/install.sh | bash
```

Run it from the root of the project you want to audit. It copies the skill, the 10
agents, the 3 slash commands, and the evidence probe into that project's `.claude/`
directory. Claude Code auto-loads `.claude/` -- no `/plugin` command, which the web
does not have. Commands keep their short names here: `/seo-audit`, `/seo-pipeline`,
`/aeo-plan`. **Commit `.claude/`** and every future session on that repo -- CLI,
desktop, or web -- gets the full pipeline with zero setup.

### Confirm a client site is reachable before you audit it

```bash
curl -fsSL .../install.sh | bash -s -- --check fitzers.ie
```

`--check` preflights the domain and tells you, at install time, whether live audits
will work from this machine -- rather than letting you discover a blocked host halfway
through an audit. A blocked host is reported as an environment fact and does **not**
fail the install.

```bash
# other useful forms
curl -fsSL .../install.sh | bash -s -- --user           # every project, not just this one
curl -fsSL .../install.sh | bash -s -- --ref my-branch  # install from a branch or tag
./scripts/install.sh --target ../client-site            # from a clone, into another project
./scripts/install.sh --uninstall                        # clean removal
```

<details>
<summary>Doing the plugin install by hand instead</summary>

**Two commands, and the order matters.** Adding the marketplace first is not optional --
installing first fails with an error that sends you the wrong way (see the table below).
This is exactly what `--plugin` automates.

```
/plugin marketplace add opsach/seo
/plugin install seo-geo-consultant@opsach-seo
```

`/plugin` exists in the CLI and desktop app. It is **not** available in Claude Code on
the web.

> **Where you type it matters.** `/plugin ...` goes at the `>` prompt *inside* a running
> Claude Code session. `claude plugin ...` goes in your *terminal*, at the shell prompt.
> Never the `claude` prefix inside the session; never the leading slash outside it.
> Mixing the two is a common install failure, and it does not announce
> itself -- inside a session, a shell command is just read as a message.

The terminal equivalents:

```bash
claude plugin marketplace add opsach/seo
claude plugin install seo-geo-consultant@opsach-seo
claude plugin details seo-geo-consultant   # inventory + token cost
```

Note that the marketplace is named **`opsach-seo`**, not `seo` -- it does not match the
repo path you pass to `marketplace add`. `@opsach-seo` is the suffix `install` wants.

</details>

A correct install reports **Skills (4)** and **Agents (10)**. The three slash commands
are listed under Skills — `aeo-plan`, `seo-audit`, `seo-pipeline`, alongside the
`seo-geo-consultant` skill itself — because current Claude Code surfaces commands and
skills in one inventory. Always-on cost is roughly 2k tokens; the rest loads on invoke.

Verified end to end against `github.com/opsach/seo` on Claude Code CLI 2.1.220.

### Install troubleshooting

**If an install misbehaves, do not guess -- run the doctor:**

```bash
curl -fsSL https://raw.githubusercontent.com/opsach/seo/main/scripts/doctor.sh | bash
```

It checks prerequisites, the CLI version, the files actually on disk in all four
install locations, marketplace and plugin registration, and network reachability --
then prints a deduplicated, ordered list of the exact commands that repair whatever
it found. Exit 0 means the plugin is usable.

The two install routes are alternatives, so the doctor never asks you to run both.
After a file install it reports the unregistered marketplace as expected and
still exits 0; if it ever finds *both* a marketplace plugin and a file copy, it flags
the duplicate -- two copies of the skill, agents and commands load in every session --
and names the one command that removes the redundant one.

| Symptom | Cause | Fix |
|---|---|---|
| `Plugin "seo-geo-consultant" not found in marketplace "opsach-seo" ... try marketplace update` | You ran `install` before `marketplace add`. **The suggested `marketplace update` is wrong** -- there is nothing to update yet | `claude plugin marketplace add opsach/seo`, *then* install |
| `Plugin "seo-geo-consultant" not found in marketplace "seo"` | Used the repo name as the marketplace name | The marketplace is `opsach-seo`: `install seo-geo-consultant@opsach-seo` |
| Typing `claude plugin ...` does nothing / is answered as a chat message | Shell command typed at the in-session `>` prompt | Use `/plugin ...` inside a session, `claude plugin ...` in a terminal |
| `claude: command not found` after `npm install -g` | npm's global bin is not on `PATH` | Reopen the terminal; if it persists, use the file install -- it needs no CLI at all |
| `unknown command 'plugin'` | Claude Code 1.x -- the plugin system is 2.x | `npm install -g @anthropic-ai/claude-code@latest` |
| **"`/plugin` isn't available in this environment"** | Expected on Claude Code web — the command exists only in the CLI and desktop app | Use the file install. This is not a broken install |
| A web session "forgets" the plugin next time | Web containers are ephemeral; a `--user` install lives in `~/.claude` and does not survive | Install into the project and **commit `.claude/`** — that is what persists |
| `/seo-audit` does not appear after installing | The session started before the files landed | Start a new session -- commands and agents are loaded at session start |
| `Unknown command: /seo-audit` after a **plugin** install | Plugin commands are namespaced; the short name belongs to the file route | Type `/seo-geo-consultant:seo-audit`, or install via the file route to get the short names |
| Agents report "plugin files not found" | Nothing installed in any of the searched locations | Re-run the installer; every agent resolves the reference and probe paths across plugin, project, and user installs |
| Live audit reports "blocked by network policy" | The sandbox's egress policy does not allow the client's domain -- not an install problem | See [Running against a client website](#running-against-a-client-website) |

Nothing above worked? **The file install cannot fail the way the plugin route can** -- it copies files
and verifies the result, with no marketplace, no registration, and no CLI involved.

Contributors can additionally check a clone with:

```bash
python3 scripts/verify.py    # validates manifests, frontmatter, references, mirrors
```

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

After a **plugin** install these are namespaced: `/seo-geo-consultant:seo-audit`, and
so on. A file install keeps the short names shown above.
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

### Evidence Toolkit: `scripts/seo-probe.py`

An SEO audit is a claim about specific bytes a server sent. `seo-probe.py` fetches
those bytes and reports measured values, so findings cite observations instead of
impressions. Python standard library only -- no pip install, no API keys.

```bash
seo-probe.py preflight https://client.com     # can we fetch at all? if not, exactly why
seo-probe.py site      https://client.com -n 5 # full evidence pack in ~12 requests
seo-probe.py page      https://client.com/pricing [--json] [--ua googlebot]
seo-probe.py robots    https://client.com      # per-crawler ALLOWED/BLOCKED + line numbers
seo-probe.py redirects client.com              # http/https x www/apex matrix + soft-404
seo-probe.py sitemap   https://client.com      # URL count, lastmod honesty, path groups
```

Per page it measures status and redirect chain, TTFB, title and description lengths,
canonical, meta robots and `X-Robots-Tag`, `html lang`, heading outline, body word
count, the share of sections inside the 120-180 word AI-extraction band, JSON-LD
`@type`s **and parse errors with positions**, `og:`/`twitter:` coverage, hreflang,
image alt gaps, script weight, compression and cache headers -- plus a **rendering
verdict**: is the content in the server's HTML, or is the body an empty SPA shell?
That last line is usually the most valuable finding in a URL-only audit.

`robots` evaluates Googlebot, Bingbot, GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot,
Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User, Google-Extended,
Applebot-Extended, Amazonbot, Bytespider, CCBot, and meta-externalagent, and reports
the deciding rule's line number for each.

Why this matters: `WebFetch` converts pages to markdown through a summarising model,
which discards titles, meta tags, canonicals, JSON-LD, and status codes -- everything
an SEO audit is about. The plugin's agents are instructed to treat it as prose-reading
only and never cite it as evidence for a tag-level finding.

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

## Running against a client website

A URL-only audit needs one thing the plugin cannot provide for you: permission to
reach the client's domain from wherever Claude Code is running.

**Always preflight first.**

```bash
python3 .claude/scripts/seo-probe.py preflight https://client.com
```

| Exit | Meaning | What to do |
|---|---|---|
| 0 | Fetching works | Run `/seo-audit https://client.com` or `/seo-pipeline https://client.com` |
| 3 | **Blocked by network policy** | The sandbox refused the connection before it left the machine -- see below |
| 4 | **The site blocks bots** | Report it as a finding; AI crawlers are refused the same way. Never work around bot protection |
| 5 | Unreachable | DNS, TLS, or timeout -- confirm the domain with the client |

### Exit 3: the sandbox blocked it

Claude Code on the web runs in a sandbox whose **network policy** is chosen when the
environment is created. If that policy does not allow the client's domain, every
fetch is refused -- `curl`, `WebFetch`, and the probe alike. This is an environment
permission, not a bug, and retrying will not help. Three ways forward:

1. **Change the environment's network access** setting (or allowlist the client
   domain) and start a new session --
   see <https://code.claude.com/docs/en/claude-code-on-the-web>.
2. **Run from Claude Code CLI** on a machine with normal internet access.
3. **Switch to owned-data mode** -- ask the client for Search Console, Screaming Frog,
   and PageSpeed exports, drop them in a `seo-data/` folder, and audit those. Often
   *better* evidence than fetching, because it covers the whole site rather than a
   sample. See `owned-data-guide.md`.

The agents enforce this: on exit 3 they stop and report the blocked host instead of
falling back to remembered facts about the brand. An audit that invents findings is
worth less than no audit.

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

Originally based on [seo-geo-consultant by AndreasH96](https://github.com/AndreasH96/seo-geo-consultant) (MIT). This fork adds the AEO measurement framework, evidence/confidence policy, audit report template, run guide, live-site audit workflow, keyword/content strategy, React SPA and WordPress/Shopify implementation guides, site-migration and local SEO checklists, LocalBusiness schema support, slash commands, plugin packaging, the `seo-probe.py` evidence collector, and the
installer/verifier scripts.

## License

MIT -- see [LICENSE](LICENSE) (original copyright retained).
