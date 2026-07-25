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
   body — never page content.
6. **Verify the invocation we publish, not a convenient equivalent.** Every entry
   point has more than one shape, and they fail differently: a fetch over `http://`
   vs `https://`, an installer run from a clone vs piped through `curl | bash`. The
   documented form is the one users actually run — exercise it literally, and put a
   check in `verify.py` that exercises it too.

---

## Lesson Log

> Append new entries here after every correction. Never delete entries.

## [2026-07-25] — The published `curl | bash` install was never the one we tested

**What happened:** `install.sh` was verified repeatedly — fresh install, re-run,
uninstall, four layouts — always by executing the file from a clone. The command the
README publishes pipes it into `bash`, where `"$0"` is `bash`, not a path. In that
shape `dirname "$0"` is `.`, so the script treated the **caller's parent directory**
as a local checkout: running the documented command from any directory whose parent
happened to contain `skills/seo-geo-consultant/` installed from that unrelated tree,
announced "Installing from local checkout", and silently ignored `--ref`. When the
decoy tree was incomplete the copy died mid-way on a raw `cp: cannot stat`, leaving a
half-installed `.claude/` — a skill with no agents, which Claude Code loads happily
and `/seo-pipeline` then fails on at runtime. `--help` was broken in the same shape:
it ran `sed` against a file named `bash`.
**Root cause:** The local-checkout branch keyed off a path derived from `$0` without
first establishing that the script exists on disk. Testing only ever used the shape
where that assumption holds.
**Pattern:** Same shape as the `http://` vs `https://` probe bug — a path verified in
one invocation mode, assumed to hold in the mode users actually run. Second instance,
so Active Rule 5 was split and generalised into Rule 6.
**Rule:** Resolve a local checkout only when `BASH_SOURCE`/`$0` names a real file;
validate the whole source tree before copying anything; stage the install and swap it
in only after verification, so a failure leaves the previous install intact.
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
| Verification | 5 | Yes — Active Rules 1-6; `scripts/verify.py` enforces 1, 2, 4 and 6 |
| Planning | 0 | — |
| Communication | 0 | — |
| Escalation | 0 | — |
| Incident | 0 | — |
| Other | 0 | — |

