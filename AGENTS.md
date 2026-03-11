# Codex Agent Instructions

> Entry point for OpenAI Codex. Full doctrine lives in the files referenced below.
> Read them in the order listed before starting any work.

---

## Startup Sequence (Every Session, No Exceptions)

1. Read `tasks/lessons.md` — absorb all active rules
2. Read `tasks/todo.md` — find where the last session ended
3. Check for unresolved risk flags
4. Identify active mode: **Standard** / **Light** / **Incident**
5. Only then: begin work

---

## Doctrine Files

| File | When to read it |
|---|---|
| `AGENT_OPS.md` | Always — core execution doctrine |
| `QA_OPS.md` | Before writing, reviewing, or running any tests |
| `DEPLOY_OPS.md` | Before any database change or deployment |
| `SECURITY_OPS.md` | Before any feature ships to production |
| `AGENT_OPS_PROSPECT_INTEL.md` | Always — project-specific rules for this codebase |

---

## Non-Negotiables

- Temporary fixes are future bugs with extra steps
- Tests passing is necessary — not sufficient
- Never fail silently
- Read `tasks/lessons.md` first. Every session. No exceptions.
