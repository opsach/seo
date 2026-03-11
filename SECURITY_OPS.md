# Security Operations Doctrine

> Model-agnostic. Works with Claude, GPT-4o, Gemini, Mistral, or any capable LLM agent.
> Companion to `AGENT_OPS.md`. All base rules apply here.

---

## Purpose

Security is not a feature. It is a baseline condition.

The execution doctrine flags security as a risk domain. This document defines what that actually means — the specific rules, checks, and protocols that govern how the system handles data, access, and trust.

A system that functions correctly but leaks data, exposes credentials, or allows unauthorised access has failed — regardless of how clean the code is.

---

## Security Principles

| Principle | Rule |
|---|---|
| **Least privilege** | Every role, key, and user gets only the access they need — nothing more |
| **Zero implicit trust** | Never assume a request is authorised — verify at every layer |
| **Defence in depth** | No single security control is sufficient — layer them |
| **Secrets are secrets** | Credentials never appear in code, logs, or client-side contexts |
| **Fail secure** | When in doubt, deny. An overly restrictive error is recoverable. A data breach is not. |

---

## Authentication Rules

- **Never roll your own auth.** Use Supabase Auth — it exists for this reason.
- **Session tokens must never be stored in localStorage.** Supabase handles this via httpOnly cookies or in-memory — do not override this.
- **Auth state must gate every protected route.** No route that requires login should render for unauthenticated users — not even briefly.
- **Password reset and email verification flows must be tested** before any user-facing release — not assumed to work.
- **OAuth providers** (if added later): verify redirect URLs are locked to your domain in the Supabase dashboard.

---

## Supabase Row Level Security (RLS)

RLS is the primary data access control layer. Treat it as mandatory infrastructure, not optional configuration.

**Rules:**
- RLS must be enabled on every table before it holds any data — no exceptions
- Every table must have explicit policies defining who can SELECT, INSERT, UPDATE, DELETE
- Default stance: deny all, grant explicitly
- Never use `USING (true)` in production — this means "anyone can access everything"
- RLS policies must be tested for both authorised and unauthorised access before a table is considered complete

**RLS policy audit checklist (run for every new table):**
- [ ] RLS is enabled on the table
- [ ] SELECT policy is defined and tested
- [ ] INSERT policy is defined and tested
- [ ] UPDATE policy is defined and tested
- [ ] DELETE policy is defined and tested
- [ ] Tested with authenticated user — expected data returned
- [ ] Tested with unauthenticated user — access correctly denied
- [ ] Tested with a different user's data — cross-user access correctly denied

---

## API Key Management

Supabase provides two keys. They have fundamentally different security profiles.

| Key | Safe client-side? | What it can do |
|---|---|---|
| **Anon key** | Yes | Access data subject to RLS policies |
| **Service role key** | **Never** | Bypasses all RLS — full database access |

**Rules:**
- Service role key must never appear in frontend code, browser context, or version control
- Anon key is safe to expose client-side — RLS is the control layer
- If service role key is ever accidentally committed: rotate it immediately in Supabase dashboard, then treat the old key as compromised
- All keys must be stored as environment variables — never hardcoded

---

## Input Validation

Every piece of data that enters the system from outside must be treated as untrusted.

**Rules:**
- Validate all user inputs on the client before submission — type checks, length limits, format validation
- Do not rely on client-side validation alone — Supabase database constraints are the authoritative validation layer
- Use TypeScript types to enforce data shape at compile time
- Never pass raw user input directly into a Supabase query without sanitisation
- Supabase's parameterised queries protect against SQL injection by default — do not bypass this by constructing raw SQL strings

---

## Data Exposure Rules

- **Only query what you need.** Never `SELECT *` in production queries — specify columns explicitly
- **Never log sensitive data.** No user emails, IDs, scores, or business data in `console.log` statements that survive to production
- **Never expose internal error messages to users.** Catch errors, log internally, show a safe generic message to the UI
- **Pagination and limits on all list queries.** Never return unbounded result sets — set explicit `.limit()` on all Supabase queries

---

## Dependency Security

- Run `npm audit` before any release — review and address high/critical vulnerabilities
- Do not install packages to solve problems that can be solved with 10 lines of code
- Review what a package does before installing it — do not blindly trust npm packages
- Keep Supabase client library up to date — security patches ship regularly

---

## Security Pre-Release Checklist

Run before every production deploy, in addition to `DEPLOY_OPS.md` checklist.

### Authentication
- [ ] All protected routes require authentication — tested unauthenticated
- [ ] Session handling works correctly (login, logout, expiry)
- [ ] No auth bypass possible via direct URL navigation

### Data Access
- [ ] RLS enabled and tested on all tables containing production data
- [ ] No `USING (true)` policies in production
- [ ] Cross-user data access impossible (tested with two separate test accounts if multi-user)
- [ ] Service role key not present in any client-side code or build output

### Secrets
- [ ] No credentials in version control (run `git log --all --full-history -- .env*` to verify)
- [ ] All required secrets set in Vercel production environment
- [ ] `.env.example` contains no real values — only placeholder descriptions

### Code
- [ ] No `console.log` statements containing user data or sensitive information
- [ ] All user inputs validated before submission
- [ ] No raw SQL string construction — parameterised queries only
- [ ] `npm audit` run — no high or critical vulnerabilities unaddressed

### Data
- [ ] No test data or seed data present in production database
- [ ] All list queries have explicit limits — no unbounded result sets

---

## Security Incident Protocol

If a security issue is discovered — suspected data exposure, leaked credentials, unauthorised access, or RLS bypass:

1. **Activate Incident Mode immediately**
2. **Assess blast radius first** — what data could have been accessed? By whom? For how long?
3. **Contain before fixing** — disable the affected feature, rotate compromised credentials, or restrict access before attempting a code fix
4. **Document everything** — timeline, what was exposed, what action was taken
5. **Root cause analysis is mandatory** — add to `tasks/lessons.md` with full context
6. **Consider disclosure obligations** — if user data was exposed, assess whether users need to be notified

**Credential compromise response:**
- Leaked Supabase anon key: rotate in dashboard, update all environments, redeploy
- Leaked service role key: rotate immediately, audit all database access logs for the exposure window, treat as potential full data breach

---

## Project-Specific Security Context

> Fill this section per project deployment.

```
**Auth method:** [e.g. Supabase email/password / magic link / OAuth]
**User data held:** [e.g. email addresses, lead scores, business names — classify sensitivity]
**Tables with RLS:** [List all tables and confirm RLS status]
**Multi-user:** [Yes / No — if yes, cross-user isolation is critical]
**External data sources:** [e.g. n8n webhooks, third-party APIs — list trust level]
**Compliance requirements:** [e.g. GDPR applicable — Irish users = yes]
**Security contact:** [Who to escalate a P0 security incident to]
```

---

## GDPR Note (Applicable — Irish users)

Prospect Intel processes business data. If it ever holds personal data on individuals (contact names, emails, LinkedIn profiles), GDPR obligations apply:

- Data must be held with a lawful basis (legitimate interest for B2B prospecting is generally defensible)
- Users must be able to request deletion of their data
- Data must not be held longer than necessary
- Third-party processors (Supabase, Vercel) must be assessed as adequate — both are GDPR-compliant with EU data residency options

Document this in the Project Context section above when personal data is first introduced.

---

## File Conventions

| File | Purpose |
|---|---|
| `.env.example` | Documented environment variables — no real values |
| `tasks/lessons.md` | Security failures that become doctrine |
| `tasks/todo.md` | Security incident log, RLS audit results |
