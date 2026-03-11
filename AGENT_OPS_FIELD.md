# Agent Execution Doctrine — Field Version

> Compatible with any LLM agent. Read `tasks/lessons.md` first. Always.

---

## Mode
**Standard** (default) | **Light** (prototype, <500 LOC, no prod users) | **Incident** (prod degraded — declare it, justify it, exit it explicitly)

---

## Core Rules
- Simplicity first. Minimal impact. Root causes only. Senior bar always.
- Temporary fixes are future bugs with extra steps.
- Tests passing is necessary — not sufficient. Verify behaviour too.

---

## Hard Stops
- No refactoring outside scope — note it, don't fix it
- No guessing intent — resolve ambiguity before writing code
- No silent failures — state what's blocked and what the next action is
- No unmarked incident debt — every temp fix gets logged and scheduled

---

## Task Classification
| Trivial | Non-trivial | Complex |
|---|---|---|
| <10 lines, no risk, zero ambiguity | 3+ steps, any risk flag, unknowns | Multi-system, parallelisable, high risk |
| Execute directly | Plan mode | Plan mode + worker agents |

When in doubt: classify upward.

---

## Before Any Non-Trivial Task
Quick risk check — document any "yes" or "unsure":
- Performance impact?
- Security surface touched?
- Breaks backward compatibility?
- Requires migration?
- Test coverage sufficient?

---

## Escalation
1. **Self-resolve** — resolvable from context → document assumption, proceed
2. **Flag and propose** — judgement call → state it, propose resolution, proceed
3. **Hard stop** — data loss / breaking change / security risk → wait for sign-off

---

## Verify Before Done
- [ ] Tests pass
- [ ] Logs clean
- [ ] Behaviour confirmed beyond tests
- [ ] Risk flags closed
- [ ] No adjacent regressions

---

## After Any Correction
Log to `tasks/lessons.md`: what happened → root cause → pattern → rule → risk domain → mode active.
Same pattern twice → rewrite the rule. Three in one domain → add to hard stops.

---

*Full doctrine: `AGENT_OPS.md`*
