# Agent Instructions

> Entry point for OpenAI Codex and other agents. Identical intent to `CLAUDE.md` —
> read that file for the full operating instructions for this repository.

**This repository is the SEO & GEO Consultant plugin for Claude Code** — a
skill knowledge pack plus stdlib-only Python tooling (`scripts/`). No build; the
test suite is `python3 scripts/verify.py`.

## Startup Sequence

1. Read `tasks/lessons.md` — absorb all active rules
2. Read `tasks/todo.md` — find where the last session ended
3. Mode: **Light** (docs-only repo)
4. Begin work

## Key Rules

- The product is `skills/seo-geo-consultant/` — SKILL.md orchestrates, `references/` holds the depth
- Numeric/benchmark claims require confidence tier + source per `skills/seo-geo-consultant/references/evidence-policy.md`
- Keep README, run-guide, and `.claude-plugin/` manifests consistent with each other
- `docs/doctrine/` is a portable ops framework for *application* projects; the Prospect Intel overlay files in there are templates from another project — not rules for this repo
- Never fail silently
