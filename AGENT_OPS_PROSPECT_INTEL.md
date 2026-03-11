# Prospect Intel — Project Overlay

> This overlay extends the base execution doctrine (`AGENT_OPS.md`).
> All base rules apply. This file adds project-specific constraints.

---

## Project Context

**Product:** Prospect Intel — internal restaurant lead intelligence dashboard for Moolah Media
**Owner:** Alex Opsenica / Moolah Media
**Purpose:** Prospecting workflow automation — lead scoring, pipeline visibility, outreach triggering

**Stack:**
- Frontend: React + TypeScript + Tailwind CSS
- Backend/DB: Supabase (PostgreSQL + Auth + Realtime)
- Automation: n8n (Phase 2 — not yet in scope)
- Hosting: TBD (likely Vercel)

**Active Mode:** Standard

---

## Architecture

```
/src
  /components       — UI components (atomic, no business logic)
  /pages            — Route-level views
  /hooks            — Custom React hooks (data fetching, state)
  /lib              — Supabase client, utilities, helpers
  /types            — Shared TypeScript types and interfaces
  /store            — Global state (if applicable)
/supabase
  /migrations       — All schema changes via migration files only
  /functions        — Edge functions (Phase 2+)
tasks/
  todo.md           — Active task plan
  lessons.md        — Accumulated rules
```

---

## Coding Conventions

- **TypeScript strict mode** — no `any`, no implicit types
- **No default exports** — named exports only
- **All Supabase queries typed end-to-end** — use generated types from `supabase gen types`
- **Component naming:** PascalCase for components, camelCase for hooks (`useLeadScore`, not `LeadScoreHook`)
- **Hook naming:** always prefixed with `use`
- **No inline styles** — Tailwind utility classes only
- **Error boundaries** on all async data surfaces — never let a failed fetch crash the view
- **Loading and error states** are required for every data-fetching component — not optional

---

## Supabase Rules

- **Schema changes via migration files only** — never alter tables directly in the Supabase dashboard
- **Row Level Security (RLS) must be enabled** on every table before it holds real data
- **Never expose service role key client-side** — anon key only in the browser
- **All queries must handle null/empty states** — Supabase returns empty arrays, not errors, on no results
- **Realtime subscriptions** must be cleaned up on component unmount — no memory leaks

---

## Known Failure Patterns

- **Supabase type drift** — generated types go stale after schema changes. Run `supabase gen types typescript` after every migration.
- **RLS gaps** — easy to forget RLS on new tables. Check before considering any table "done."
- **Tailwind class purging** — dynamically constructed class strings get purged. Use complete class names only.
- **n8n dependency assumption** — Phase 2 automation is not yet in scope. Do not architect Phase 1 components around n8n hooks that don't exist yet.

---

## Risk Flags (Project-Specific)

These trigger automatic non-trivial classification regardless of line count:

- Any change to Supabase schema or RLS policies
- Any change to authentication flow or session handling
- Any component that reads or writes lead scoring logic
- Any change that affects how data is surfaced to the outreach workflow

---

## Off-Limits

- `/supabase/migrations` — never edit existing migration files. Add new ones only.
- Lead scoring algorithm — do not refactor without explicit instruction. It is the core business logic.

---

## Phase Boundaries

**Phase 1 (current):** React UI + Supabase data pipeline + lead scoring dashboard
**Phase 2 (future):** n8n automation, outreach triggering, enrichment pipeline

> Do not build Phase 2 infrastructure in Phase 1. Note ideas in `tasks/todo.md`, do not implement.

---

## Verification Additions (Prospect Intel specific)

Beyond base verification checklist, also confirm:
- [ ] RLS policies correct and tested for new tables
- [ ] Supabase types regenerated after any schema change
- [ ] No hardcoded lead scoring weights — all configurable
- [ ] Empty/null states handled in all data-fetching components

---

*Base doctrine: `AGENT_OPS.md` | Field version: `AGENT_OPS_FIELD.md`*
