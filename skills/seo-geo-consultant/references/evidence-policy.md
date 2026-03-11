# SEO/GEO Evidence Policy

Use this policy when making benchmark-style or platform-specific recommendations.

## Purpose

Prevent overconfident guidance and improve trust by separating standards from observed field behavior and experiments.

## Confidence Tiers

### 1) Standards-based
Use when guidance is backed by widely accepted technical standards or official documentation.

Examples:
- Canonical URLs for duplicate management
- JSON-LD syntax correctness
- Robots/sitemap syntax requirements

### 2) Widely observed
Use when behavior is repeatedly reported in field studies, practitioner benchmarks, or large-sample experiments but not formally guaranteed.

Examples:
- Section-level content extractability patterns
- Relative impact of freshness on citation frequency

### 3) Experimental
Use when the tactic is emerging, weakly validated, or platform behavior is volatile.

Examples:
- Novel llms.txt formats beyond baseline conventions
- New bot directives without broad confirmation

## Evidence Requirements

For each benchmark-style claim, include:

1. **Source label** (e.g., first-party docs, third-party study, internal benchmark)
2. **Date context** (month/year)
3. **Scope** (sample size, platform, geography if known)
4. **Limitation note** (what is unknown)

## Claim Formatting Standard

Use this format in reports:

`[Confidence: Widely observed] Claim text. Source: <name>, <month year>, scope: <summary>. Limitation: <summary>.`

## Anti-Hallucination Guardrails

- Do not present estimates as guarantees.
- If no source is available, mark the claim as **hypothesis** and avoid precise percentages.
- If sources conflict, state conflict explicitly and recommend a test plan.

## Minimum Quality Bar (Audit Deliverables)

- No numeric uplift claims without evidence metadata.
- No platform-specific advice without date context.
- Every recommendation must include confidence tier + next verification step.
