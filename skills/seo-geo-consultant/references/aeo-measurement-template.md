# AEO Measurement Template (Quarterly)

Use this template to measure Answer Engine Optimization (AEO) progress consistently across major AI answer platforms.

## 1) Query Set Definition

Track 20-30 prompts split across intent categories:

- **Informational** (e.g., "What is [category]?")
- **Commercial investigation** (e.g., "Best [category] tool for [audience]")
- **Comparison** (e.g., "[Your product] vs [Competitor]")
- **Use-case/problem solving** (e.g., "How do I [task]?")

For each prompt, store:

| Field | Description |
|---|---|
| Prompt ID | Stable unique identifier |
| Prompt text | Exact user-facing phrasing |
| Intent type | Informational / Commercial / Comparison / Use-case |
| Priority | P1 / P2 / P3 |
| Owning page | URL expected to satisfy the prompt |

---

## 2) Platform Runs

Run each prompt on:

- ChatGPT Search
- Perplexity
- Google AI Overviews

Record outcomes:

| Date | Platform | Prompt ID | Brand mentioned? | Brand cited? | Rank/order in answer | Competitors cited | Citation URL(s) |
|---|---|---|---|---|---|---|---|

---

## 3) Core Metrics

### Share of Model (SoM)

`SoM = (Prompts where your brand is mentioned) / (Total prompts)`

Track by platform and overall.

### Citation Rate

`Citation Rate = (Prompts with at least one direct citation to your domain) / (Total prompts)`

### Competitor Overlap

- Which competitors appear most often when you do not?
- Which domains are cited repeatedly for your target prompts?

### Freshness Sensitivity

Record whether cited pages were updated within the last 90 days.

---

## 4) Action Mapping

Every quarter, map metric deltas to specific actions:

| Observation | Root cause hypothesis | Action | Owner | Deadline |
|---|---|---|---|---|
| Low citation rate on comparison prompts | Missing comparison landing pages | Publish 3 comparison pages with schema + tables | Content | YYYY-MM-DD |
| Mentioned but not cited | Weak structured data / missing canonical clarity | Improve JSON-LD + canonical + source references | SEO/Eng | YYYY-MM-DD |

---

## 5) Confidence Tiers for Recommendations

Tag every recommendation in your roadmap:

- **Standards-based**: Backed by established technical SEO standards and search documentation
- **Widely observed**: Repeatedly observed in field studies and operator reports but not formally guaranteed
- **Experimental**: Emerging tactic; monitor and validate before scaling

Use this to avoid overcommitting to unproven GEO tactics.
