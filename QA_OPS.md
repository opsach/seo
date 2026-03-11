# QA Operations Doctrine

> Model-agnostic. Works with Claude, GPT-4o, Gemini, Mistral, or any capable LLM agent.
> Companion to `AGENT_OPS.md`. All base rules apply here.

---

## Purpose

The execution doctrine verifies *changes*. This document governs the *product*.

A task can pass every verification check and still ship the wrong thing. QA_OPS closes that gap — it defines what "done" means at feature level, not just task level.

---

## QA Levels

Four levels. Every feature must declare which levels apply before work begins.

| Level | What it covers | When it applies |
|---|---|---|
| **L1 — Unit** | Individual functions, hooks, utilities in isolation | Always |
| **L2 — Integration** | Component + data layer interaction, API contracts, Supabase queries | Any feature touching data |
| **L3 — End-to-End** | Full user journey through the UI | Any user-facing feature |
| **L4 — Exploratory** | Unscripted manual testing for edge cases and unexpected behaviour | Before any release |

Declare required levels in `tasks/todo.md` during plan mode. Do not skip levels without documented justification.

---

## Definition of Done

A feature is **done** when all of the following are true — not before:

### Functional
- [ ] All acceptance criteria met (defined before implementation — see below)
- [ ] All declared QA levels passed
- [ ] Edge cases identified and handled or explicitly deferred
- [ ] Error states tested — not just the happy path

### Code quality
- [ ] No TypeScript errors (`tsc --noEmit` passes clean)
- [ ] No console errors or warnings in browser
- [ ] No unhandled promise rejections
- [ ] Linter passes clean

### Data integrity
- [ ] Supabase queries return expected shape in all states (data, empty, error)
- [ ] Null/undefined states handled — no silent rendering failures
- [ ] RLS policies tested for both authorised and unauthorised access
- [ ] No data leakage between user sessions (if multi-user)

### Regression
- [ ] Existing tests still pass
- [ ] No adjacent features visually or functionally broken
- [ ] Behaviour diff reviewed against main

### Performance (for data-heavy features)
- [ ] No unnecessary re-renders identified
- [ ] Supabase queries are not N+1
- [ ] Loading states present and accurate

---

## Acceptance Criteria Protocol

Acceptance criteria must be written **before implementation begins**. No exceptions.

**Format:**

```
## Acceptance Criteria — [Feature Name]

**User story:** As a [user], I want to [action] so that [outcome].

**Happy path:**
- Given [state], when [action], then [result]
- Given [state], when [action], then [result]

**Edge cases:**
- Given [empty state], when [action], then [result]
- Given [error state], when [action], then [result]
- Given [unauthorised access], when [action], then [result]

**Out of scope:**
- [Explicitly what this feature does NOT cover]

**QA levels required:** L1 / L2 / L3 / L4
```

Store in the relevant section of `tasks/todo.md` or as `tasks/ac_[feature].md` for complex features.

If acceptance criteria cannot be written before implementation, that is a planning failure — resolve the ambiguity first.

---

## Test Strategy

### What to test at each level

**L1 — Unit tests**
- Pure functions (scoring logic, data transforms, formatters)
- Custom hooks in isolation (use testing-library/react-hooks)
- Utility functions with edge cases (null inputs, empty arrays, boundary values)
- Do NOT test: UI rendering, Supabase calls, third-party libraries

**L2 — Integration tests**
- Component + Supabase query interaction (use MSW or Supabase local for mocking)
- API contract validation — does the query return the expected shape?
- Form submission flows end-to-end within a component
- Auth state changes and their effect on data access

**L3 — End-to-end tests**
- Core user journeys only — not every permutation
- Happy path + one critical error path per journey
- Use Playwright or Cypress against a staging environment, not production

**L4 — Exploratory**
- Run after L1–L3 pass, before release
- Focus: what did the tests not cover?
- Specifically test: rapid interactions, slow networks, unexpected input, mobile viewport

---

## Regression Protocol

Regression must be checked before every merge to main.

**Automated:**
- Unit and integration test suite must pass clean
- TypeScript compilation must pass clean
- No new linter errors introduced

**Manual (for UI changes):**
- Review adjacent pages/components for visual regressions
- Check mobile and desktop viewports
- Verify navigation flows still work end-to-end

**For data model changes:**
- Re-test all features that query the affected table
- Verify RLS still behaves correctly
- Confirm Supabase types have been regenerated

---

## Bug Triage

When a bug is reported or discovered, classify it before acting:

| Severity | Definition | Response |
|---|---|---|
| **P0 — Critical** | Production down, data loss, security breach, auth broken | Activate Incident Mode immediately |
| **P1 — High** | Core feature broken, significant user impact, data incorrect | Fix in current session, do not defer |
| **P2 — Medium** | Feature degraded but workaround exists, visual defect on key page | Fix in next planned session |
| **P3 — Low** | Minor visual issue, edge case with minimal impact | Log in backlog, fix when convenient |

Log all bugs — including P3 — in `tasks/todo.md` backlog. Nothing disappears silently.

**Bug entry format:**
```
## Bug — [Short title]
**Severity:** P0 / P1 / P2 / P3
**Reported:** [Date]
**Description:** [One sentence]
**Steps to reproduce:** [Numbered steps]
**Expected:** [What should happen]
**Actual:** [What happens]
**Root cause hypothesis:** [Initial theory]
```

---

## QA Checklist — Pre-Release

Run this before any code ships to production.

### Functionality
- [ ] All acceptance criteria for included features verified
- [ ] All P0 and P1 bugs resolved
- [ ] No known regressions
- [ ] Exploratory testing completed (L4)

### Data
- [ ] Supabase migrations tested against a copy of production data shape
- [ ] RLS policies verified for all affected tables
- [ ] No hardcoded data or test data in production build
- [ ] Environment variables correct for production target

### Performance
- [ ] No console errors in production build
- [ ] No obvious performance regressions on key pages
- [ ] Supabase query counts reasonable (no N+1 patterns)

### Security
- [ ] See `SECURITY_OPS.md` pre-release checklist

### Deployment
- [ ] See `DEPLOY_OPS.md` pre-release checklist

---

## Project-Specific QA Context

> Fill this section per project deployment.

```
**Test framework:** [e.g. Vitest + Testing Library + Playwright]
**Mock strategy:** [e.g. MSW for API mocking / Supabase local]
**QA environment:** [e.g. Vercel preview deployments / dedicated staging]
**Test file conventions:** [e.g. co-located *.test.ts / dedicated __tests__ folder]
**Coverage threshold:** [e.g. 80% on business logic, no threshold on UI]
**Who runs L4 exploratory:** [Agent / human / both]
```

---

## File Conventions

| File | Purpose |
|---|---|
| `tasks/todo.md` | Acceptance criteria, bug log, backlog |
| `tasks/ac_[feature].md` | Dedicated acceptance criteria for complex features |
| `tasks/lessons.md` | QA failures that become doctrine — same loop as AGENT_OPS |
