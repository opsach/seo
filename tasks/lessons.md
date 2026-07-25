# tasks/lessons.md

> Accumulated rules derived from real mistakes.
> Read this at the start of every session. No exceptions.
> Same pattern twice → rewrite the rule. Three in one domain → promote to hard stops in CLAUDE.md.

---

## Active Rules

> Rules promoted from lessons. These are standing instructions.

1. **Duplicated content must be generated, never hand-copied.** If a file exists in
   two places (source + `.claude/` mirror), a script produces the copy and
   `scripts/verify.py` proves they match. Hand-copies drift silently.
2. **Instructions that span tool calls must carry absolute paths.** Shell variables,
   `cd` state, and exported env do not survive between Bash tool calls. Any agent
   instruction of the form "set X then use $X later" is broken by construction.
3. **Ship the failure path, not just the happy path.** Every external dependency
   (network, file location, tool availability) needs a check that produces a specific
   diagnosis and a specific remedy. "It didn't work" is the bug.
4. **Run `python3 scripts/verify.py` before every commit.** It is the only test this
   repo has.
5. **A blocked fetch is identified by provenance, never inferred from the body.** A
   403 carrying `x-deny-reason` or an allowlist-denial phrase is exit 3 with an empty
   body — never page content. Exercise every fetch path over both `http://` and
   `https://`; they fail differently.
6. **Installation is a failure path too, and it must be diagnosable.** A clone that
   passes `verify.py` proves nothing about a user's machine. Every install route
   carries `scripts/doctor.sh`, which names the failing step and the exact repair
   command. Where an upstream tool's own error message points the wrong way, say so
   in the docs — do not restate it.
7. **A diagnostic gathers evidence before it judges, and never plans two mutually
   exclusive remedies.** Where more than one route reaches the same working state,
   the check must first establish which route is in use — otherwise it condemns a
   valid setup. Alternatives are shown as alternatives, never as consecutive steps
   in a repair plan.
8. **Verify the user's literal next keystroke, once per install route.** "The component
   is loaded" is not "the command runs" — plugin installs namespace their commands,
   file installs do not. Every script that closes with "now run X" must pick X from the
   route actually in use.
9. **A configurable root is resolved through its override, never hardcoded to its
   default.** `${CLAUDE_CONFIG_DIR:-$HOME/.claude}` once, reused everywhere; searches
   that could legitimately match either location check both.

---

## Lesson Log

> Append new entries here after every correction. Never delete entries.

## [2026-07-25] — Every doc told plugin users to type a command that does not exist

**What happened:** Verifying install-and-run in Claude Code CLI, the plugin route was
confirmed working — skill, 10 agents, 3 commands all discovered — and then `/seo-audit`
returned **`Unknown command: /seo-audit`**. Plugin-installed commands are namespaced as
`/seo-geo-consultant:seo-audit`; only the file route (`.claude/commands/`) gives the
short name. README, run-guide, `install.sh` and `doctor.sh` all closed with "try
`/seo-audit`", so every plugin user's first action after a successful install failed in
a way that reads exactly like a broken install.
**Root cause:** The two install routes were verified for *component discovery* — does
the session see the skill, the agents, the commands — and discovery was assumed to
imply invocability. Nothing ever typed the command the docs prescribe. The inventory
listing even showed the namespaced name (`seo-geo-consultant:seo-audit`) and it was
read as cosmetic.
**Pattern:** Same shape as the `http://`-vs-`https://` lesson: a path verified in one
configuration was assumed to hold in the other. Here the two configurations are the two
*install routes*, and the untested one was the route the CLI's own docs steer users to.
**Rule:** Verify the user's literal next keystroke, not a proxy for it. "The component
is loaded" is not "the command runs" — type the exact string the docs tell the user to
type, once per install route, and make the closing hint of every script route-aware.
**Risk domain:** verification
**Mode active:** Light

## [2026-07-25] — `--user` installed into a directory nothing reads

**What happened:** `install.sh --user` wrote to `$HOME/.claude` unconditionally, and
`doctor.sh` searched only `$HOME/.claude` and `$HOME/.claude/plugins/cache`. With
`CLAUDE_CONFIG_DIR` set, Claude Code reads none of those: a `--user` install reported
success while the commands never appeared, and the doctor called a healthy
plugin install "no installed copy found" and prescribed a second, redundant copy.
**Root cause:** `$HOME/.claude` was treated as the location of the user-level tree
rather than as its *default*. Both scripts hardcoded the default and never consulted
the variable that relocates it.
**Pattern:** Encoding a default as an invariant. The setup that exercises the override
is exactly the setup nobody tests on, because the maintainer's machine uses the default.
**Rule:** Resolve configurable roots through their override once
(`${CLAUDE_CONFIG_DIR:-$HOME/.claude}`) and use that everywhere; where a search can
legitimately hit either location, search both. Proven by executing a session with the
override set — the files-present/commands-absent split is invisible to a file check.
**Risk domain:** verification
**Mode active:** Light

## [2026-07-25] — The install path had no failure path of its own

**What happened:** A user reported "can not install plugin ... always giving error"
and could not say which step failed. Nothing in the repo could answer the question:
`verify.py` checks a *clone*, not an *install*, and every install document described
only the successful sequence. The best available help was a guess between four
possible causes.
**Root cause:** Active Rule 3 ("ship the failure path") had been applied to the
plugin's runtime dependencies — network fetches got preflight and exit codes — but
never to the plugin's own installation. Installing is itself an external dependency
chain (npm → PATH → CLI version → git → GitHub → marketplace registration → on-disk
files), and not one link had a diagnosis.
**Aggravating factor:** the CLI's own error for the most likely mistake actively
misdirects. Running `install` before `marketplace add` returns *"not found in
marketplace ... try `claude plugin marketplace update`"* — and `update` cannot fix a
marketplace that was never added, so following the advice loops.
**Pattern:** Verification aimed at the artifact, not at the user's first contact with
it. A repo that validates perfectly can still be uninstallable, and the maintainer
never sees it because the maintainer's machine is already set up.
**Rule:** Every install route ships a diagnostic that names the failing step and the
command that repairs it (`scripts/doctor.sh`). When an upstream tool's error message
is wrong, the docs must contradict it explicitly rather than repeat it.
**Risk domain:** verification
**Mode active:** Light

## [2026-07-25] — Probe audited the egress proxy's denial page as if it were the client site

**What happened:** Asked to audit `http://fitzers.ie`, `seo-probe.py page` returned a
complete, confident audit — "title MISSING", "H1 count 0", "0 words", "Rendering:
NEARLY EMPTY (critical)", "JSON-LD ISSUE" — and exited 0. Every row described the
egress proxy's 97-byte denial notice. The site was never contacted. `preflight` was
wrong in the other direction: it called the same 403 "BLOCKED BY THE SITE" (exit 4)
and invited a finding that fitzers.ie refuses Googlebot and AI crawlers.
**Root cause:** The proxy tunnels `https://`, so a refused CONNECT raises a URLError
and was already classified `policy`. Plaintext `http://` has no tunnel to refuse, so
the proxy answers with an ordinary 403 whose body is the denial text. `fetch()` only
scanned 403 bodies for *bot-protection* vendors (Cloudflare, DataDome …); with no
match it left `error`unset, so every caller treated the denial as the origin's own
response. The exit-3 path existed and was well documented — one transport shape just
never reached it.
**Pattern:** A failure path verified on one transport was assumed to hold on all of
them. `https://` was tested; `http://` — what a client actually types — was not.
**Rule:** Classify blocked-vs-real by *provenance*, not by guessing from body text: an
`x-deny-reason` header or a denial phrase means policy, exit 3, empty body. Any new
fetch path must be tested with both schemes before it is trusted.
**Risk domain:** verification
**Mode active:** Light

## [2026-07-25] — Hand-copied `.claude/` mirror drifted from source

**What happened:** The committed `.claude/` mirror still contained the pre-fix agent
files; the manual-install path (the one users on Claude Code web actually use) had
been shipping stale agents since 2026-07-15. Nobody noticed because nothing compared
the two trees.
**Root cause:** The mirror was created by hand-running `cp` in one session, and the
follow-up edits landed only in `agents/`. A duplicate with no generator and no check
is guaranteed to drift.
**Pattern:** Duplication without automation. The second copy is always the stale one.
**Rule:** Generate every duplicate with `scripts/install.sh`; prove equality with
`scripts/verify.py` before commit.
**Risk domain:** verification
**Mode active:** Light

## [2026-07-25] — Agent instructions assumed shell state persists

**What happened:** The first version of the file-resolver block told agents to set
`SEO_KIT=...` in one Bash call and use `"$SEO_KIT/scripts/seo-probe.py"` in later
calls. Each Bash tool call is a fresh shell, so every later command would have
expanded to `/scripts/seo-probe.py` and failed.
**Root cause:** Wrote the instructions as if for an interactive terminal session
rather than for a sequence of independent tool calls.
**Pattern:** Authoring agent instructions against the wrong execution model.
**Rule:** Resolver commands print absolute paths; instructions tell the agent to reuse
the printed value literally. `verify.py` fails the build on any `$SEO_KIT` reference.
**Risk domain:** verification
**Mode active:** Light

## [2026-07-25] — Live audits had no failure path

**What happened:** URL-only audits could not run in a sandboxed environment, and the
plugin had nothing to say about it: `curl` and `WebFetch` both returned an opaque 403
from the egress proxy, with no instruction on what that meant or what to do.
**Root cause:** The live-audit procedure documented only the successful path. The
possibility that fetching is refused before it leaves the machine was never modelled.
**Pattern:** Designing for the happy path leaves the agent to improvise on failure —
and an improvising auditor writes findings it did not measure.
**Rule:** Every external dependency gets a preflight with distinct exit codes and a
named remedy per code. Agents stop on a failed preflight; they never downgrade to
recalled facts.
**Risk domain:** verification
**Mode active:** Light

## [2026-07-25] — The doctor called a healthy install broken

**What happened:** `install.sh --user` installed correctly and verified clean, then
`doctor.sh` reported "marketplace 'opsach-seo' is NOT registered", exited 1, and
prescribed `marketplace add` + `plugin install` — which would have added a *second*
copy of the skill, agents and commands on top of the working one.
**Root cause:** The doctor checked marketplace registration before it checked the files
on disk, so the marketplace section had no way to know an install already existed. It
treated the two install routes as layers of one install rather than as alternatives.
**Pattern:** A diagnostic whose checks run in the wrong order judges a valid
configuration against a rule that does not apply to it — and its remedy makes things
worse than the imagined defect.
**Rule:** A check that can be satisfied by more than one route must establish which
route is in use before it reports. Order the sections so evidence precedes judgement,
and never emit two mutually exclusive remedies into one ordered plan.
**Risk domain:** verification
**Mode active:** Light

---

### Template

```
## [YYYY-MM-DD] — [Short title]

**What happened:** [One sentence describing the error]
**Root cause:** [Why it happened — not what, but why]
**Pattern:** [The generalised failure mode]
**Rule:** [Imperative that prevents recurrence]
**Risk domain:** [scope / verification / planning / communication / escalation / incident / other]
**Mode active:** [Standard / Light / Incident]
```

---

## Domain Tracker

> Track how many lessons fall into each domain. When a domain hits 3, escalate to hard stops.

| Domain | Count | Escalated? |
|---|---|---|
| Scope | 0 | — |
| Verification | 8 | Yes — Active Rules 1-9; `scripts/verify.py` enforces 1, 2, 4, 6, 7, 8 and 9 |
| Planning | 0 | — |
| Communication | 0 | — |
| Escalation | 0 | — |
| Incident | 0 | — |
| Other | 0 | — |

