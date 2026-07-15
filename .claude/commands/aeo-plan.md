---
description: Create a quarterly AEO measurement plan (prompt set, Share of Model, citation tracking)
argument-hint: "[product/site name or URL]"
---

Create a quarterly AEO (Answer Engine Optimization) measurement plan using the
seo-geo-consultant skill and `references/aeo-measurement-template.md`.

Subject: $ARGUMENTS

Deliver:
1. A 20-30 prompt query set split across intent categories (informational,
   commercial investigation, comparison, use-case), each with prompt ID,
   priority, and owning page. Derive prompts from the product's actual
   positioning -- read the codebase/site content first if available.
2. The platform run log format for ChatGPT Search, Perplexity, and Google AI
   Overviews.
3. Baseline metric definitions: Share of Model, citation rate, competitor
   overlap, freshness sensitivity.
4. An action-mapping table connecting expected observations to owners and
   deadlines.

Follow `references/evidence-policy.md`: measurement targets are hypotheses to
validate, not guaranteed outcomes.
