# Deployment Operations Doctrine

> Model-agnostic. Works with Claude, GPT-4o, Gemini, Mistral, or any capable LLM agent.
> Companion to `AGENT_OPS.md`. All base rules apply here.

---

## Purpose

The execution doctrine governs how code is written. This document governs how it ships.

A codebase that passes every test can still cause a production incident through a bad deploy. DEPLOY_OPS defines the protocol from code complete to production live — and what to do when it goes wrong.

---

## Environment Model

Three environments. Always. No exceptions.

| Environment | Purpose | Who touches it |
|---|---|---|
| **Local** | Development and unit testing | Agent / developer only |
| **Staging** | Integration testing, QA, pre-release verification | Agent / developer, never real users |
| **Production** | Live system | Real users — treat with maximum care |

**Rules:**
- Never develop directly against production
- Never test features on production data
- Staging must mirror production configuration as closely as possible
- If staging doesn't exist yet, create it before the first external user touches anything

---

## Environment Variables

Environment variables are a deployment failure vector. Treat them as such.

**Rules:**
- All environment variables must be documented in `.env.example` with descriptions — never leave keys undocumented
- Never commit `.env`, `.env.local`, or any file containing real secrets to version control
- Production secrets are set in the hosting platform (Vercel dashboard) — never in files
- Staging must use its own separate Supabase project — never point staging at production DB
- After any deploy, verify environment variables are loading correctly before marking complete

**Required variables (Prospect Intel baseline):**
```
VITE_SUPABASE_URL=           # Supabase project URL
VITE_SUPABASE_ANON_KEY=      # Supabase anon key (public — safe client-side)
# NEVER expose service role key client-side
```

**Verification step:** After every deploy, open the network tab and confirm no 401/403 errors on initial data load.

---

## Supabase Migration Protocol

Database migrations are the highest-risk deployment operation. One wrong migration can corrupt production data with no easy undo.

**Mandatory sequence:**

1. **Write migration** in `/supabase/migrations/` — never alter tables directly in the Supabase dashboard
2. **Test locally** — run `supabase db reset` to apply from scratch and verify
3. **Test on staging** — apply migration to staging Supabase project and run full integration tests
4. **Regenerate types** — run `supabase gen types typescript --local > src/types/supabase.ts`
5. **Verify application** — confirm all queries still work against the new schema
6. **Apply to production** — only after staging is verified clean
7. **Verify production** — check that application loads and queries return expected data

**Hard rules:**
- Never skip staging for schema changes — not even "small" ones
- Never run destructive migrations (DROP, DELETE, column removal) without a backup or verified rollback
- Rollback plan must exist before any destructive migration is run — document it in `tasks/todo.md`
- If a migration fails mid-way, activate Incident Mode immediately

---

## Deployment Checklist

Run in full before every production deploy. No shortcuts.

### Pre-deploy
- [ ] All acceptance criteria for this release verified (see `QA_OPS.md`)
- [ ] All P0 and P1 bugs resolved
- [ ] QA pre-release checklist passed
- [ ] Security pre-release checklist passed (see `SECURITY_OPS.md`)
- [ ] All pending Supabase migrations tested on staging
- [ ] Supabase types regenerated and committed
- [ ] `.env.example` updated if any new variables added
- [ ] No debug code, console.logs, or test data in production build
- [ ] TypeScript compiles clean (`tsc --noEmit`)
- [ ] Linter passes clean
- [ ] All tests pass on staging

### Deploy
- [ ] Confirm correct environment variables set in Vercel dashboard
- [ ] Trigger deploy from main branch only — never deploy from feature branches to production
- [ ] Monitor deploy logs in real time — do not close until deploy is confirmed successful
- [ ] Run Supabase migrations (if any) immediately after deploy, not before

### Post-deploy verification (run within 5 minutes of deploy)
- [ ] Application loads without errors
- [ ] Authentication flow works end-to-end
- [ ] Core data queries return expected results
- [ ] No console errors in production browser
- [ ] No 4xx/5xx errors in Supabase logs
- [ ] Key user journeys navigable end-to-end

**If post-deploy verification fails on any item → activate Incident Mode immediately.**

---

## Rollback Protocol

Know the rollback plan before every deploy. Not after.

### Application rollback (Vercel)
- Vercel keeps deployment history — previous deploys can be instantly re-promoted
- Go to Vercel dashboard → Deployments → select last known good deploy → Redeploy
- Application rollback takes ~30 seconds

### Database rollback
- Supabase does not have one-click rollback
- Rollback strategy must be defined per migration:
  - **Additive migrations** (add column, add table): write a corresponding DOWN migration file before deploying
  - **Destructive migrations** (drop column, alter type): take a manual backup snapshot in Supabase dashboard before running
  - **Data migrations**: test with a transaction and ROLLBACK before committing

**Rollback entry format (add to `tasks/todo.md` before any risky deploy):**
```
## Rollback Plan — [Deploy description]
**Application rollback:** Vercel redeploy to [previous deploy ID]
**DB rollback:** [DOWN migration filename / backup snapshot / not required]
**Verification after rollback:** [Steps to confirm system is healthy]
```

---

## Release Notes Protocol

For any deploy that changes user-facing behaviour, write release notes before deploying.

**Format:**
```
## Release — [Date] — [Version or short description]

**What changed:**
- [Feature or fix, one line each]

**Known issues:**
- [Any P2/P3 bugs not addressed in this release]

**Rollback window:** [How long you'll monitor before considering stable]
```

Store in `tasks/releases/` or append to `tasks/todo.md`.

---

## CI/CD Rules

- **Main branch is always deployable.** Never merge broken code to main.
- **Feature branches only.** All work happens on branches — never commit directly to main.
- **Deploy from main only.** No production deploys from feature or development branches.
- **Automated checks must pass before merge:** TypeScript, linter, unit tests minimum.

---

## Project-Specific Deploy Context

> Fill this section per project deployment.

```
**Hosting:** [e.g. Vercel]
**Database:** [e.g. Supabase — project URL for staging / production]
**Branch strategy:** [e.g. main → production, develop → staging]
**CI platform:** [e.g. GitHub Actions / Vercel automatic]
**Deploy trigger:** [e.g. push to main / manual promotion]
**Migration tool:** [e.g. Supabase CLI]
**Monitoring:** [e.g. Vercel logs / Supabase logs / Sentry]
**Rollback owner:** [Who authorises and executes a production rollback]
```

---

## File Conventions

| File | Purpose |
|---|---|
| `.env.example` | Documented list of all required environment variables |
| `supabase/migrations/` | All schema changes — append only, never edit existing |
| `tasks/todo.md` | Rollback plans, deploy notes, post-deploy verification log |
| `tasks/releases/` | Release notes archive |
