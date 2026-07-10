# Agent Execution Doctrine — Complete System

> Model-agnostic. Compatible with Claude, GPT-4o, Gemini, Mistral, or any capable LLM agent.
> Full development lifecycle coverage: Build → Test → Ship → Secure.

---

## File Index

| File | Covers | Stage |
|---|---|---|
| `AGENT_OPS.md` | Planning, execution, risk, escalation, self-improvement | Build |
| `AGENT_OPS_FIELD.md` | Compressed 1-page field version of above | Build |
| `AGENT_OPS_PROSPECT_INTEL.md` | Project overlay — Prospect Intel specific | Build |
| `QA_OPS.md` | Test strategy, acceptance criteria, bug triage, definition of done | Test |
| `DEPLOY_OPS.md` | Environment model, migration protocol, deploy checklist, rollback | Ship |
| `SECURITY_OPS.md` | Auth, RLS, secrets, input validation, pre-release security checklist | Secure |
| `tasks/todo.md` | Active task plan template | All stages |
| `tasks/lessons.md` | Self-improvement log template | All stages |

---

## Lifecycle Coverage

```
BUILD          TEST           SHIP           SECURE
─────────      ─────────      ─────────      ─────────
AGENT_OPS  →  QA_OPS     →  DEPLOY_OPS  →  SECURITY_OPS
   │               │               │               │
Plan           Acceptance     Environment    Auth rules
Execute        Criteria       Variables      RLS protocol
Risk           Test levels    Migrations     Secrets mgmt
Escalate       Bug triage     Checklists     Input validation
Verify         Definition     Rollback       GDPR baseline
Learn          of Done        Monitoring     Incident response
```

---

## Deployment Instructions

### Any new project
1. Copy `AGENT_OPS.md`, `AGENT_OPS_FIELD.md` to project root
2. Copy `QA_OPS.md`, `DEPLOY_OPS.md`, `SECURITY_OPS.md` to project root
3. Copy `tasks/todo.md` and `tasks/lessons.md` to `/tasks/`
4. Fill in all `## Project-Specific Context` sections across all four ops files
5. Set active mode (Standard or Light) in `AGENT_OPS.md`
6. Begin

### Prospect Intel (ready to deploy)
1. Copy all files
2. `AGENT_OPS_PROSPECT_INTEL.md` is pre-filled — use as active build overlay
3. Fill in project-specific context sections in `QA_OPS.md`, `DEPLOY_OPS.md`, `SECURITY_OPS.md`
4. Mode: Standard
5. Begin

### New project overlay
1. Duplicate `AGENT_OPS_PROSPECT_INTEL.md` → rename to `AGENT_OPS_[PROJECT].md`
2. Replace all Prospect Intel specifics
3. Fill in the project context sections in the other three ops files

---

## Operating Cadence

**Every session:**
1. Read `tasks/lessons.md`
2. Read `tasks/todo.md`
3. Declare mode
4. Work

**Before any feature ships:**
1. QA pre-release checklist (`QA_OPS.md`)
2. Deploy checklist (`DEPLOY_OPS.md`)
3. Security pre-release checklist (`SECURITY_OPS.md`)

**After any correction:**
1. `tasks/lessons.md` entry with root cause, pattern, rule, domain, mode
2. Domain tracker updated — promote to hard stops at 3 entries

**After any incident:**
1. Exit Incident Mode explicitly
2. Full incident entry in `tasks/lessons.md`
3. Temp fixes logged as tracked debt in `tasks/todo.md`

---

## Which Docs to Use When

| Situation | Primary doc | Supporting docs |
|---|---|---|
| Writing new code | `AGENT_OPS.md` | — |
| Planning a feature | `AGENT_OPS.md` | `QA_OPS.md` (acceptance criteria) |
| Before writing tests | `QA_OPS.md` | — |
| Touching the database | `DEPLOY_OPS.md` | `SECURITY_OPS.md` |
| Preparing a release | `QA_OPS.md` | `DEPLOY_OPS.md`, `SECURITY_OPS.md` |
| Production incident | `AGENT_OPS.md` (Incident Mode) | `DEPLOY_OPS.md` (rollback) |
| Security concern raised | `SECURITY_OPS.md` | `AGENT_OPS.md` (Incident Mode) |
| Post-incident review | `tasks/lessons.md` | All four ops docs |

---

## Version History

| Version | Changes |
|---|---|
| v1 | Raw CLAUDE.md — good ideas, broken formatting. Rating: 4.0 |
| v2 | Clean structure, decision tables. Rating: 7.5 |
| v3 | Anti-patterns, risk assessment, async plan mode. Rating: 8.5 |
| v4 | Session startup, autonomy model, escalation ladder, subagent orchestration. Rating: 9.6 |
| v5 | Operating modes — Standard / Light / Incident. Rating: 9.9 |
| v6 | Model-agnostic rename, full file system. Rating: 10.0 |
| v7 (current) | Complete lifecycle — QA, Deploy, Security ops added |

---

## Model Entry Points

Different tools auto-read different filenames. Use the right entry point for your tool.

| Tool | File to use | How it works |
|---|---|---|
| **Claude Code** | `CLAUDE.md` | Auto-read from project root on every session |
| **OpenAI Codex** | `AGENTS.md` | Auto-read before any work begins; can be layered per folder |
| **Cursor** | `.cursorrules` | Rename `CLAUDE.md` to `.cursorrules` — auto-read on every session |
| **Windsurf** | `.windsurfrules` | Rename `CLAUDE.md` to `.windsurfrules` — auto-read on every session |
| **ChatGPT Projects** | `CHATGPT_PROJECT_INSTRUCTIONS.md` | Paste contents into Project Instructions — not a file drop |
| **ChatGPT Custom GPT** | `CHATGPT_PROJECT_INSTRUCTIONS.md` | Paste into System Instructions when configuring the GPT |
| **API / any other agent** | Paste `AGENT_OPS.md` | No auto-read — inject as system prompt manually |

**Note:** `CLAUDE.md` and `AGENTS.md` are identical in content. They exist as separate files only because Claude Code and Codex look for different filenames. Keep both in the project root to cover both tools simultaneously.
