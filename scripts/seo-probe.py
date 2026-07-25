#!/usr/bin/env python3
"""
seo-probe -- deterministic SEO/GEO evidence collector for the seo-geo-consultant
plugin.

Why this exists: an SEO audit is only worth what its evidence is worth. Fetching a
page through a markdown-converting tool destroys exactly the things an audit is
about -- <title>, meta description, canonical, hreflang, og:*, JSON-LD, status
codes, redirect chains, and whether the body is an empty SPA shell. This script
fetches raw bytes and reports observed facts, so every finding can cite a value
that was actually measured.

Standard library only. No install step. Honours HTTPS_PROXY / SSL_CERT_FILE.

Usage:
  seo-probe.py preflight <url>              connectivity + fetchability diagnosis
  seo-probe.py page <url> [--ua NAME]       SEO facts for one page
  seo-probe.py redirects <domain>           canonicalisation + soft-404 matrix
  seo-probe.py robots <origin> [--ua NAME]  robots.txt + per-crawler verdicts
  seo-probe.py sitemap <url> [-n N]         sitemap parse + URL sample
  seo-probe.py site <origin> [-n N]         full evidence pack (all of the above)

Options:
  --json              machine-readable output instead of markdown
  --ua NAME           user agent: default | googlebot | gptbot | perplexity | <raw string>
  --timeout SECONDS   per-request timeout (default 20)
  --out DIR           also save raw HTML/robots/sitemap bodies to DIR
  -n, --pages N       how many sitemap URLs to sample (default 5, max 25)

Exit codes:
  0  ok
  3  blocked by network/egress policy (proxy refused the connection)
  4  blocked by the target site (bot protection, 403/429 from the origin)
  5  target unreachable (DNS, TLS, timeout)
  6  usage error
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

VERSION = "1.0"

DEFAULT_UA = f"Mozilla/5.0 (compatible; seo-probe/{VERSION}; +https://github.com/opsach/seo)"
UA_PRESETS = {
    "default": DEFAULT_UA,
    "googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "bingbot": "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "gptbot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.1; +https://openai.com/gptbot",
    "claudebot": "Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)",
    "perplexity": "Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
    "browser": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
}

# Crawlers whose robots.txt access we report on. (search | ai-training | ai-search)
CRAWLERS = [
    ("Googlebot", "search"),
    ("Bingbot", "search"),
    ("Google-Extended", "ai-training"),
    ("GPTBot", "ai-training"),
    ("OAI-SearchBot", "ai-search"),
    ("ChatGPT-User", "ai-user"),
    ("ClaudeBot", "ai-training"),
    ("Claude-SearchBot", "ai-search"),
    ("Claude-User", "ai-user"),
    ("PerplexityBot", "ai-search"),
    ("Perplexity-User", "ai-user"),
    ("Applebot-Extended", "ai-training"),
    ("Amazonbot", "ai-training"),
    ("Bytespider", "ai-training"),
    ("CCBot", "ai-training"),
    ("meta-externalagent", "ai-training"),
]

SHELL_ROOT_IDS = {"root", "app", "__next", "__nuxt", "main", "svelte"}
# Tags whose text content is never visible page copy. <head> is deliberately absent:
# <title> lives there and must still be read; body-word counting starts at <body>.
SKIP_TEXT_TAGS = {"script", "style", "noscript", "template", "svg"}


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------


class Hop:
    def __init__(self, url, status, location, elapsed):
        self.url = url
        self.status = status
        self.location = location
        self.elapsed = elapsed

    def as_dict(self):
        return {
            "url": self.url,
            "status": self.status,
            "location": self.location,
            "elapsed_ms": round(self.elapsed * 1000),
        }


class Result:
    def __init__(self, url):
        self.requested_url = url
        self.final_url = url
        self.status = None
        self.headers = {}
        self.body = b""
        self.chain = []
        self.ttfb = None
        self.total = None
        self.error = None
        self.error_kind = None  # policy | site | network | http

    @property
    def ok(self):
        return self.error is None and self.status is not None

    @property
    def text(self):
        charset = None
        ctype = self.headers.get("content-type", "")
        m = re.search(r"charset=([\w\-]+)", ctype, re.I)
        if m:
            charset = m.group(1)
        if not charset:
            m = re.search(rb'<meta[^>]+charset=["\']?([\w\-]+)', self.body[:4096], re.I)
            if m:
                charset = m.group(1).decode("ascii", "ignore")
        for enc in filter(None, [charset, "utf-8", "latin-1"]):
            try:
                return self.body.decode(enc, "strict")
            except (UnicodeDecodeError, LookupError):
                continue
        return self.body.decode("utf-8", "replace")

    def as_dict(self):
        return {
            "requested_url": self.requested_url,
            "final_url": self.final_url,
            "status": self.status,
            "ttfb_ms": round(self.ttfb * 1000) if self.ttfb else None,
            "total_ms": round(self.total * 1000) if self.total else None,
            "bytes": len(self.body),
            "chain": [h.as_dict() for h in self.chain],
            "headers": self.headers,
            "error": self.error,
            "error_kind": self.error_kind,
        }


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = None


def _opener():
    global _OPENER
    if _OPENER is None:
        ctx = ssl.create_default_context()
        handlers = [
            _NoRedirect(),
            urllib.request.HTTPSHandler(context=ctx),
            urllib.request.ProxyHandler(),  # reads *_proxy env vars
        ]
        _OPENER = urllib.request.build_opener(*handlers)
    return _OPENER


def _classify(exc, url):
    """Turn a fetch exception into (message, kind). Kind drives the exit code."""
    text = str(exc)
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code in (403, 401) and "CONNECT" in text.upper():
            return (f"HTTP {exc.code} from proxy on CONNECT", "policy")
        return (f"HTTP {exc.code} {exc.reason}", "http")
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        low = str(reason).lower()
        # The agent/egress proxy refuses tunnels to hosts outside the allowlist.
        if "tunnel connection failed" in low or "cannot connect to proxy" in low:
            code = re.search(r"\b(40[37])\b", low)
            if code:
                return (
                    f"egress proxy refused CONNECT to {url} ({code.group(1)})",
                    "policy",
                )
            return (f"egress proxy refused CONNECT to {url}", "policy")
        if isinstance(reason, socket.gaierror) or "name or service not known" in low:
            return (f"DNS lookup failed for {url}", "network")
        if "certificate" in low or "ssl" in low:
            return (f"TLS failure: {reason}", "network")
        if "timed out" in low:
            return (f"connection timed out: {reason}", "network")
        return (f"{reason}", "network")
    if isinstance(exc, socket.timeout):
        return ("request timed out", "network")
    return (text, "network")


_PROXY_DENY_MARKERS = (
    "host not in allowlist",
    "not in the allowlist",
    "network egress settings",
    "blocked by network policy",
)


def _is_proxy_denial(headers, body):
    """True when a 403/429 came from the egress proxy rather than the origin.

    The proxy tunnels https://, so a refused CONNECT surfaces as a URLError and is
    caught by _classify. Plaintext http:// has no tunnel to refuse, so the proxy
    answers with an ordinary 403 whose body is the denial notice. Parsing that as
    the origin's response turns an environment permission into fabricated findings
    about the client's site -- a missing title, zero words, no JSON-LD.
    """
    if headers.get("x-deny-reason"):
        return True
    low = body.lower()
    return any(m in low for m in _PROXY_DENY_MARKERS)


def fetch(url, ua=DEFAULT_UA, timeout=20, method="GET", max_redirects=10, max_bytes=3_000_000):
    """Fetch a URL, following redirects manually so the whole chain is evidence."""
    res = Result(url)
    current = url
    started = time.monotonic()
    for _ in range(max_redirects + 1):
        hop_start = time.monotonic()
        req = urllib.request.Request(current, method=method)
        req.add_header("User-Agent", ua)
        req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        req.add_header("Accept-Encoding", "gzip")
        req.add_header("Accept-Language", "en-US,en;q=0.9")
        try:
            resp = _opener().open(req, timeout=timeout)
            status, headers, stream = resp.status, resp.headers, resp
        except urllib.error.HTTPError as exc:
            status, headers, stream = exc.code, exc.headers, exc
        except Exception as exc:  # noqa: BLE001 - classified below
            res.error, res.error_kind = _classify(exc, current)
            res.final_url = current
            res.total = time.monotonic() - started
            return res

        elapsed = time.monotonic() - hop_start
        location = headers.get("Location")
        res.chain.append(Hop(current, status, location, elapsed))
        if res.ttfb is None:
            res.ttfb = elapsed

        if status in (301, 302, 303, 307, 308) and location:
            nxt = urllib.parse.urljoin(current, location)
            if nxt == current:
                res.error, res.error_kind = ("redirect loop", "http")
                break
            current = nxt
            try:
                stream.read(0)
                stream.close()
            except Exception:  # noqa: BLE001
                pass
            continue

        raw = stream.read(max_bytes)
        if headers.get("Content-Encoding", "").lower() == "gzip":
            try:
                raw = gzip.decompress(raw)
            except Exception:  # noqa: BLE001
                pass
        res.status = status
        res.headers = {k.lower(): v for k, v in headers.items()}
        res.body = raw
        res.final_url = current
        break
    else:
        res.error, res.error_kind = ("too many redirects", "http")

    res.total = time.monotonic() - started
    if res.status in (403, 429) and res.error is None:
        head = res.body[:4000].decode("utf-8", "ignore")
        # Proxy denial first: it must never be mistaken for the origin answering.
        if _is_proxy_denial(res.headers, head):
            host = urllib.parse.urlsplit(res.final_url or url).hostname or url
            reason = res.headers.get("x-deny-reason", "host not in allowlist")
            res.error = f"egress proxy refused {host} (HTTP {res.status}, {reason})"
            res.error_kind = "policy"
            res.body = b""
            return res
        blob = (head + json.dumps(res.headers)).lower()
        if any(m in blob for m in ("cloudflare", "captcha", "just a moment", "akamai", "perimeterx", "datadome")):
            res.error_kind = "site"
    return res


# --------------------------------------------------------------------------
# HTML parsing
# --------------------------------------------------------------------------


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts = []
        self.metas = []          # (name_or_property, content)
        self.links = []          # dict(rel, href, hreflang)
        self.headings = []       # (level, text)
        self.images = []         # dict(src, alt, width, height, loading)
        self.anchors = []        # dict(href, rel, text)
        self.jsonld_raw = []
        self.html_lang = None
        self.body_words = 0
        self.shell_roots = []    # ids of likely SPA mount points
        self.script_count = 0
        self.inline_script_bytes = 0
        self.stylesheet_count = 0
        self.has_body = False
        self._skip_depth = 0
        self._in_title = False
        self._in_jsonld = False
        self._in_script = False
        self._jsonld_buf = []
        self._heading_level = None
        self._heading_buf = []
        self._anchor_buf = None
        self._text_runs = []     # (position_index, words) for section analysis

    # -- helpers ---------------------------------------------------------
    def _attrs(self, attrs):
        return {k.lower(): (v or "") for k, v in attrs}

    # -- tags ------------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = self._attrs(attrs)
        if tag in SKIP_TEXT_TAGS:
            if tag == "script":
                self.script_count += 1
                self._in_script = True
                if a.get("type", "").lower() == "application/ld+json":
                    self._in_jsonld = True
                    self._jsonld_buf = []
            self._skip_depth += 1
            return
        if tag == "html":
            self.html_lang = a.get("lang") or None
        elif tag == "body":
            self.has_body = True
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = a.get("name") or a.get("property") or a.get("http-equiv")
            if key:
                self.metas.append((key.lower(), a.get("content", "")))
        elif tag == "link":
            rel = a.get("rel", "").lower()
            if rel:
                self.links.append({"rel": rel, "href": a.get("href", ""), "hreflang": a.get("hreflang", "")})
            if "stylesheet" in rel:
                self.stylesheet_count += 1
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._heading_level = int(tag[1])
            self._heading_buf = []
            self.headings.append([self._heading_level, "", len(self._text_runs)])
        elif tag == "img":
            self.images.append(
                {
                    "src": a.get("src", "") or a.get("data-src", ""),
                    "alt": a.get("alt"),
                    "width": a.get("width", ""),
                    "height": a.get("height", ""),
                    "loading": a.get("loading", ""),
                }
            )
        elif tag == "a":
            self._anchor_buf = {"href": a.get("href", ""), "rel": a.get("rel", ""), "text": ""}
        elif tag == "div" and a.get("id", "").lower() in SHELL_ROOT_IDS:
            self.shell_roots.append(a["id"])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() in SKIP_TEXT_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in SKIP_TEXT_TAGS:
            if tag == "script":
                if self._in_jsonld:
                    self.jsonld_raw.append("".join(self._jsonld_buf))
                    self._in_jsonld = False
                self._in_script = False
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self.headings:
            self.headings[-1][1] = " ".join("".join(self._heading_buf).split())
            self._heading_level = None
        elif tag == "a" and self._anchor_buf is not None:
            self._anchor_buf["text"] = " ".join(self._anchor_buf["text"].split())
            self.anchors.append(self._anchor_buf)
            self._anchor_buf = None

    def handle_data(self, data):
        if self._in_jsonld:
            self._jsonld_buf.append(data)
            self.inline_script_bytes += len(data)
            return
        if self._skip_depth:
            if self._in_script:
                self.inline_script_bytes += len(data)
            return
        if self._in_title:
            self.title_parts.append(data)
            return
        if self._heading_level:
            self._heading_buf.append(data)
        if self._anchor_buf is not None:
            self._anchor_buf["text"] += data
        # Only text inside <body> counts as page copy.
        words = len(data.split()) if self.has_body else 0
        if words:
            self.body_words += words
            self._text_runs.append(words)

    # -- derived ---------------------------------------------------------
    @property
    def title(self):
        return " ".join("".join(self.title_parts).split())

    def meta(self, key):
        key = key.lower()
        for k, v in self.metas:
            if k == key:
                return v
        return None

    def link_href(self, rel):
        for l in self.links:
            if rel in l["rel"].split():
                return l["href"]
        return None

    def section_word_counts(self):
        """Words between consecutive headings -- the GEO 120-180 word check."""
        if not self.headings:
            return []
        out = []
        bounds = [h[2] for h in self.headings] + [len(self._text_runs)]
        for i in range(len(self.headings)):
            out.append(sum(self._text_runs[bounds[i]: bounds[i + 1]]))
        return out

    def jsonld(self):
        """Return (blocks, errors) where each block is (types, raw_len)."""
        blocks, errors = [], []
        for i, raw in enumerate(self.jsonld_raw):
            raw = raw.strip()
            if not raw:
                errors.append((i + 1, "empty <script type=application/ld+json> block"))
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append((i + 1, f"invalid JSON: {exc.msg} (line {exc.lineno}, col {exc.colno})"))
                continue
            blocks.append((sorted(set(_collect_types(data))), len(raw)))
        return blocks, errors


def _collect_types(node, acc=None):
    acc = [] if acc is None else acc
    if isinstance(node, dict):
        t = node.get("@type")
        if isinstance(t, str):
            acc.append(t)
        elif isinstance(t, list):
            acc.extend(x for x in t if isinstance(x, str))
        for v in node.values():
            _collect_types(v, acc)
    elif isinstance(node, list):
        for v in node:
            _collect_types(v, acc)
    return acc


# --------------------------------------------------------------------------
# robots.txt
# --------------------------------------------------------------------------

VALID_DIRECTIVES = {"user-agent", "disallow", "allow", "sitemap", "crawl-delay", "host", "noindex"}


def parse_robots(text):
    """Line-accurate robots.txt parser. Returns groups, sitemaps, problems."""
    groups = []       # {"agents": [...], "rules": [(kind, path, lineno)], "line": n}
    sitemaps = []     # (url, lineno)
    problems = []     # (lineno, message)
    current = None
    expecting_agent = False

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            problems.append((lineno, f"unparseable line (no ':'): {raw.strip()[:80]!r}"))
            continue
        field, value = line.split(":", 1)
        field = field.strip().lower()
        value = value.strip()

        if field == "user-agent":
            if current is None or not expecting_agent:
                current = {"agents": [], "rules": [], "line": lineno}
                groups.append(current)
                expecting_agent = True
            current["agents"].append(value)
            continue

        expecting_agent = False
        if field == "sitemap":
            sitemaps.append((value, lineno))
            continue
        if field in ("allow", "disallow"):
            if current is None:
                problems.append((lineno, f"{field.title()} before any User-agent line -- rule is ignored"))
                continue
            current["rules"].append((field, value, lineno))
            continue
        if field not in VALID_DIRECTIVES:
            problems.append((lineno, f"unknown directive {field!r} -- crawlers ignore it"))

    return groups, sitemaps, problems


def _match_len(pattern, path):
    """robots.txt path matching with * and $. Returns match length or -1."""
    if pattern == "":
        return -1
    regex = ""
    for ch in pattern:
        if ch == "*":
            regex += ".*"
        elif ch == "$":
            regex += "$"
        else:
            regex += re.escape(ch)
    if re.match(regex, path):
        return len(pattern.replace("*", "").replace("$", ""))
    return -1


def robots_verdict(groups, agent, path="/"):
    """Google-style evaluation: most specific group wins, longest match wins."""
    agent_l = agent.lower()
    chosen, star = None, None
    for g in groups:
        for a in g["agents"]:
            al = a.strip().lower()
            if al == "*":
                star = g if star is None else star
            elif al and (agent_l == al or agent_l.startswith(al)):
                chosen = g if chosen is None else chosen
    group = chosen or star
    if group is None:
        return ("allowed", "no matching group", None)

    best = None  # (length, kind, lineno)
    for kind, value, lineno in group["rules"]:
        if kind == "disallow" and value == "":
            continue  # "Disallow:" with empty value means allow all
        n = _match_len(value, path)
        if n >= 0 and (best is None or n > best[0] or (n == best[0] and kind == "allow")):
            best = (n, kind, lineno, value)
    if best is None:
        return ("allowed", f"group at line {group['line']} has no matching rule", group["line"])
    kind, lineno, value = best[1], best[2], best[3]
    return ("allowed" if kind == "allow" else "blocked", f"{kind.title()}: {value}", lineno)


# --------------------------------------------------------------------------
# Output helpers
# --------------------------------------------------------------------------


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join("" if c is None else str(c).replace("|", "\\|") for c in r) + " |")
    return "\n".join(out)


def flag(cond, good="OK", bad="ISSUE"):
    return good if cond else bad


def truncate(s, n=90):
    s = (s or "").replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def normalise_origin(target):
    if not re.match(r"^https?://", target):
        target = "https://" + target
    p = urllib.parse.urlparse(target)
    return f"{p.scheme}://{p.netloc}"


def die(msg, code):
    print(f"\n**seo-probe: {msg}**", file=sys.stderr)
    sys.exit(code)


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

POLICY_HELP = """
The request never left this machine's network boundary -- the egress proxy refused
the tunnel. This is an environment permission, not a fault in the target site, and
retrying will not help.

Fix (pick one):
  * Claude Code on the web: the session environment's network policy does not allow
    this host. Change the environment's network access setting (or add the host to
    its allowlist) and start a new session.
    Docs: https://code.claude.com/docs/en/claude-code-on-the-web
  * Run the audit from Claude Code CLI on a machine with normal internet access.
  * If the client can share exports (Search Console, Screaming Frog, PageSpeed),
    run the audit in owned-data mode instead -- see owned-data-guide.md.

Do NOT write an audit finding about a page you could not fetch.
""".strip()


def cmd_preflight(args):
    origin = normalise_origin(args.target)
    print(f"## Preflight: {origin}\n")
    res = fetch(origin + "/", ua=args.ua_string, timeout=args.timeout)

    if res.error_kind == "policy":
        print(f"**Result: BLOCKED BY NETWORK POLICY** — {res.error}\n")
        print(POLICY_HELP)
        return 3
    if res.error_kind == "network":
        print(f"**Result: UNREACHABLE** — {res.error}\n")
        print("Check the domain spelling, then confirm the site is up from a browser.")
        return 5
    if res.error_kind == "site" or (res.status in (403, 429)):
        print(f"**Result: BLOCKED BY THE SITE** — HTTP {res.status} for UA `{args.ua_string[:60]}`\n")
        print(
            "The origin refused an automated fetcher (bot protection). That is itself a\n"
            "reportable GEO finding: AI crawlers are likely refused the same way.\n"
            "Try `--ua googlebot` to see whether search crawlers are treated differently,\n"
            "and report the difference rather than working around the protection."
        )
        return 4
    if res.error:
        print(f"**Result: FAILED** — {res.error}\n")
        return 5

    print(f"**Result: OK** — HTTP {res.status}, {len(res.body):,} bytes, "
          f"TTFB {round(res.ttfb * 1000)}ms\n")
    if res.chain[:-1]:
        print("Redirect chain:")
        for h in res.chain[:-1]:
            print(f"- {h.status} {h.url} → {h.location}")
        print()
    print(f"Final URL: {res.final_url}")
    print("\nFetching works. Proceed with the audit.")
    return 0


def _page_facts(res, parser):
    """Return a list of (label, value, verdict) rows for one page."""
    title = parser.title
    desc = parser.meta("description")
    canonical = parser.link_href("canonical")
    robots_meta = parser.meta("robots")
    x_robots = res.headers.get("x-robots-tag")
    sections = parser.section_word_counts()
    in_band = sum(1 for w in sections if 120 <= w <= 180)
    h1s = [h for h in parser.headings if h[0] == 1]
    imgs_no_alt = [i for i in parser.images if i["alt"] is None]
    imgs_empty_alt = [i for i in parser.images if i["alt"] == ""]
    blocks, jsonld_errors = parser.jsonld()
    types = sorted({t for b in blocks for t in b[0]})
    ogs = {k for k, _ in parser.metas if k.startswith("og:")}
    tws = {k for k, _ in parser.metas if k.startswith("twitter:")}
    hreflangs = [l for l in parser.links if "alternate" in l["rel"].split() and l["hreflang"]]

    rows = [
        ("HTTP status", res.status, flag(res.status == 200)),
        ("TTFB", f"{round(res.ttfb * 1000)}ms", flag(res.ttfb < 0.8, "OK", "SLOW")),
        ("HTML bytes", f"{len(res.body):,}", ""),
        ("Redirect hops", len(res.chain) - 1, flag(len(res.chain) - 1 <= 1)),
        ("title", f"{truncate(title)!r} ({len(title)} chars)" if title else "MISSING",
         flag(title and 15 <= len(title) <= 65)),
        ("meta description", f"{truncate(desc)!r} ({len(desc)} chars)" if desc else "MISSING",
         flag(desc and 70 <= len(desc) <= 165)),
        ("canonical", canonical or "MISSING",
         flag(canonical and canonical.startswith("http"))),
        ("meta robots", robots_meta or "(none)",
         flag(not robots_meta or "noindex" not in robots_meta.lower())),
        ("X-Robots-Tag", x_robots or "(none)",
         flag(not x_robots or "noindex" not in x_robots.lower())),
        ("html lang", parser.html_lang or "MISSING", flag(bool(parser.html_lang))),
        ("H1 count", len(h1s), flag(len(h1s) == 1)),
        ("H1 text", truncate(h1s[0][1]) if h1s else "-", ""),
        ("Headings (h2/h3)",
         f"{sum(1 for h in parser.headings if h[0] == 2)}/{sum(1 for h in parser.headings if h[0] == 3)}", ""),
        ("Body word count", parser.body_words,
         flag(parser.body_words >= 250, "OK", "THIN")),
        ("Sections 120-180w (GEO)", f"{in_band}/{len(sections)}" if sections else "0/0",
         flag(sections and in_band / max(1, len(sections)) >= 0.3, "OK", "REVIEW")),
        ("JSON-LD blocks", len(blocks) + len(jsonld_errors), flag(bool(blocks))),
        ("JSON-LD @types", ", ".join(types) or "NONE", flag(bool(types))),
        ("JSON-LD parse errors", len(jsonld_errors), flag(not jsonld_errors)),
        ("og: tags", ", ".join(sorted(ogs)) or "NONE",
         flag({"og:title", "og:description", "og:image"} <= ogs)),
        ("twitter: tags", ", ".join(sorted(tws)) or "NONE", flag(bool(tws))),
        ("hreflang alternates", len(hreflangs), ""),
        ("Images", f"{len(parser.images)} total, {len(imgs_no_alt)} missing alt, "
                   f"{len(imgs_empty_alt)} empty alt", flag(not imgs_no_alt)),
        ("Links", f"{len(parser.anchors)} anchors", ""),
        ("Scripts", f"{parser.script_count} tags, ~{parser.inline_script_bytes:,}B inline", ""),
        ("content-encoding", res.headers.get("content-encoding", "NONE"),
         flag(res.headers.get("content-encoding"))),
        ("cache-control", res.headers.get("cache-control", "(none)"), ""),
        ("server / CDN", res.headers.get("server", "?") + " " +
         " ".join(f"{k}={v}" for k, v in res.headers.items()
                  if k in ("cf-cache-status", "x-vercel-cache", "x-cache", "age")), ""),
    ]
    return rows, jsonld_errors, sections


def _render_check(parser, res):
    """Is the primary content server-rendered? The single most important GEO check."""
    shell = parser.shell_roots
    words = parser.body_words
    if words < 60 and shell:
        return ("CLIENT-RENDERED (critical)",
                f"body has {words} words and a `<div id=\"{shell[0]}\">` mount point — "
                "primary content is injected by JavaScript. Search crawlers render this "
                "with delay; AI crawlers largely do not execute JS at all.")
    if words < 60:
        return ("NEARLY EMPTY (critical)",
                f"raw HTML carries only {words} words of visible text — verify the content "
                "is not client-injected or behind an auth wall.")
    if words < 250:
        return ("THIN (review)", f"{words} words of server-rendered text.")
    return ("SERVER-RENDERED (ok)", f"{words} words of visible text present in raw HTML.")


def cmd_page(args):
    url = args.target if re.match(r"^https?://", args.target) else "https://" + args.target
    res = fetch(url, ua=args.ua_string, timeout=args.timeout)
    if res.error:
        print(f"## Page: {url}\n\n**FETCH FAILED ({res.error_kind}):** {res.error}\n")
        if res.error_kind == "policy":
            print(POLICY_HELP)
            return 3
        return 4 if res.error_kind == "site" else 5

    parser = PageParser()
    try:
        parser.feed(res.text)
    except Exception as exc:  # noqa: BLE001 - malformed HTML is itself a finding
        print(f"(HTML parser stopped early: {exc})")

    rows, jsonld_errors, sections = _page_facts(res, parser)
    verdict, why = _render_check(parser, res)

    if args.json:
        blocks, _ = parser.jsonld()
        print(json.dumps({
            "response": res.as_dict(),
            "title": parser.title,
            "description": parser.meta("description"),
            "canonical": parser.link_href("canonical"),
            "robots_meta": parser.meta("robots"),
            "lang": parser.html_lang,
            "headings": [[h[0], h[1]] for h in parser.headings],
            "body_words": parser.body_words,
            "section_words": sections,
            "jsonld_types": sorted({t for b in blocks for t in b[0]}),
            "jsonld_errors": jsonld_errors,
            "images_missing_alt": sum(1 for i in parser.images if i["alt"] is None),
            "rendering": verdict,
        }, indent=2))
        return 0

    print(f"## Page: {res.final_url}")
    print(f"_probed {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} as `{args.ua}`_\n")
    if len(res.chain) > 1:
        print("**Redirect chain:** " + " → ".join(f"{h.status}" for h in res.chain[:-1]) +
              f" → {res.status} {res.final_url}\n")
    print(f"**Rendering: {verdict}** — {why}\n")
    print(md_table(["Signal", "Observed value", "Verdict"], rows))
    if jsonld_errors:
        print("\n**JSON-LD errors:**")
        for idx, msg in jsonld_errors:
            print(f"- block #{idx}: {msg}")
    if parser.headings:
        print("\n**Heading outline:**")
        for level, text, _ in parser.headings[:25]:
            print(f"{'  ' * (level - 1)}- H{level}: {truncate(text, 70)}")
        if len(parser.headings) > 25:
            print(f"  … {len(parser.headings) - 25} more")
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        name = re.sub(r"[^a-zA-Z0-9]+", "_", urllib.parse.urlparse(res.final_url).path or "index")[:60]
        path = os.path.join(args.out, f"{name or 'index'}.html")
        with open(path, "wb") as fh:
            fh.write(res.body)
        print(f"\n_raw HTML saved to {path}_")
    return 0


def cmd_redirects(args):
    origin = normalise_origin(args.target)
    host = urllib.parse.urlparse(origin).netloc
    apex = host[4:] if host.startswith("www.") else host
    variants = [
        f"http://{apex}/",
        f"http://www.{apex}/",
        f"https://{apex}/",
        f"https://www.{apex}/",
    ]
    print(f"## Canonicalisation matrix: {apex}\n")
    rows, finals = [], []
    blocked = None
    for v in variants:
        r = fetch(v, ua=args.ua_string, timeout=args.timeout, method="GET")
        if r.error:
            rows.append([v, "-", "-", f"FAILED: {r.error}"])
            if r.error_kind == "policy":
                blocked = r.error
            continue
        hops = len(r.chain) - 1
        rows.append([v, r.status, hops, r.final_url])
        finals.append(r.final_url)
    print(md_table(["Requested", "Final status", "Hops", "Final URL"], rows))

    if blocked:
        print(f"\n**BLOCKED:** {blocked}\n")
        print(POLICY_HELP)
        return 3

    distinct = {f.rstrip("/") for f in finals}
    print()
    if len(finals) < 2:
        print(f"**Verdict: INSUFFICIENT DATA** — only {len(finals)} of 4 variants responded. "
              "Report the failures above rather than a canonicalisation verdict.")
    elif len(distinct) == 1:
        print(f"**Verdict: OK** — all {len(finals)} responding variants converge on `{finals[0]}`.")
    else:
        print(f"**Verdict: ISSUE** — variants resolve to {len(distinct)} different URLs: "
              + ", ".join(f"`{d}`" for d in sorted(distinct))
              + ". Split link equity and duplicate indexing risk.")
    if any(isinstance(r[2], int) and r[2] > 1 for r in rows):
        print("\n**Redirect chains longer than one hop detected** — each extra hop costs "
              "crawl budget and leaks a little link equity.")

    # Soft-404 probe, against whichever origin actually answered.
    live = urllib.parse.urlparse(finals[0]) if finals else urllib.parse.urlparse(origin)
    probe = f"{live.scheme}://{live.netloc}/seo-probe-nonexistent-{int(time.time())}"
    r404 = fetch(probe, ua=args.ua_string, timeout=args.timeout)
    print("\n### Soft-404 check\n")
    if r404.error:
        print(f"- probe failed: {r404.error}")
    else:
        ok = r404.status in (404, 410)
        print(f"- `{probe}` → **HTTP {r404.status}** — "
              + ("correct" if ok else "**SOFT 404**: a missing page returns a success status, "
                                      "so search engines index unlimited junk URLs"))
    return 0


def cmd_robots(args):
    origin = normalise_origin(args.target)
    url = origin + "/robots.txt"
    res = fetch(url, ua=args.ua_string, timeout=args.timeout)
    print(f"## robots.txt: {url}\n")
    if res.error:
        print(f"**FETCH FAILED ({res.error_kind}):** {res.error}\n")
        if res.error_kind == "policy":
            print(POLICY_HELP)
            return 3
        return 5
    if res.status != 200:
        print(f"**HTTP {res.status}** — no robots.txt served. Crawling is unrestricted by "
              "default, but there is also no sitemap directive and no explicit AI-crawler "
              "policy. Recommend adding one.")
        return 0

    text = res.text
    groups, sitemaps, problems = parse_robots(text)
    print(f"Served {len(res.body):,} bytes, {len(text.splitlines())} lines, "
          f"{len(groups)} user-agent group(s).\n")

    rows = []
    for name, kind in CRAWLERS:
        verdict, why, lineno = robots_verdict(groups, name)
        rows.append([name, kind, verdict.upper(), why, lineno or "-"])
    print(md_table(["Crawler", "Class", "Homepage access", "Deciding rule", "Line"], rows))

    print("\n### Sitemap directives\n")
    if sitemaps:
        for u, ln in sitemaps:
            print(f"- line {ln}: `{u}`")
    else:
        print("- **MISSING** — no `Sitemap:` directive in robots.txt.")

    if problems:
        print("\n### Syntax problems\n")
        for ln, msg in problems:
            print(f"- line {ln}: {msg}")

    blocked_ai = [r[0] for r in rows if r[2] == "BLOCKED" and r[1].startswith("ai")]
    blocked_search = [r[0] for r in rows if r[2] == "BLOCKED" and r[1] == "search"]
    print("\n### Verdict\n")
    if blocked_search:
        print(f"- **CRITICAL** — search crawlers blocked at `/`: {', '.join(blocked_search)}")
    if blocked_ai:
        print(f"- AI crawlers blocked at `/`: {', '.join(blocked_ai)} — intentional or not, "
              "this removes the site from those assistants' answers.")
    if not blocked_ai and not blocked_search:
        print("- No crawler in the checked set is blocked at `/`.")
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "robots.txt"), "wb") as fh:
            fh.write(res.body)
    return 0


def _parse_sitemap(body):
    """Return (kind, entries) where kind is 'index' or 'urlset'."""
    if body[:2] == b"\x1f\x8b":
        try:
            body = gzip.decompress(body)
        except Exception:  # noqa: BLE001
            pass
    text = body.decode("utf-8", "replace")
    kind = "index" if "<sitemapindex" in text else "urlset"
    entries = []
    for m in re.finditer(r"<(?:url|sitemap)\b.*?</(?:url|sitemap)>", text, re.S | re.I):
        chunk = m.group(0)
        loc = re.search(r"<loc>\s*(.*?)\s*</loc>", chunk, re.S | re.I)
        lastmod = re.search(r"<lastmod>\s*(.*?)\s*</lastmod>", chunk, re.S | re.I)
        if loc:
            entries.append((loc.group(1).strip(), lastmod.group(1).strip() if lastmod else None))
    return kind, entries


def collect_sitemap_urls(url, args, depth=0, seen=None):
    seen = seen if seen is not None else set()
    if url in seen or depth > 2:
        return [], []
    seen.add(url)
    res = fetch(url, ua=args.ua_string, timeout=args.timeout)
    if res.error or res.status != 200:
        return [], [(url, res.error or f"HTTP {res.status}")]
    kind, entries = _parse_sitemap(res.body)
    if kind == "urlset":
        return entries, []
    urls, errors = [], []
    for child, _ in entries[:10]:
        u, e = collect_sitemap_urls(child, args, depth + 1, seen)
        urls.extend(u)
        errors.extend(e)
    return urls, errors


def cmd_sitemap(args):
    url = args.target if args.target.endswith(".xml") or "/" in urllib.parse.urlparse(
        args.target if re.match(r"^https?://", args.target) else "https://" + args.target).path.strip("/") \
        else normalise_origin(args.target) + "/sitemap.xml"
    print(f"## Sitemap: {url}\n")
    entries, errors = collect_sitemap_urls(url, args)
    if errors and not entries:
        first = errors[0][1]
        print(f"**FETCH/PARSE FAILED:** {first}\n")
        if "proxy refused" in str(first):
            print(POLICY_HELP)
            return 3
        print("If the sitemap lives elsewhere, check the `Sitemap:` directive in robots.txt.")
        return 5

    lastmods = [lm for _, lm in entries if lm]
    distinct_lastmod = len(set(lastmods))
    print(f"- URLs found: **{len(entries):,}**")
    print(f"- With `<lastmod>`: {len(lastmods):,} ({distinct_lastmod} distinct values)")
    if lastmods:
        print(f"- lastmod range: {min(lastmods)} → {max(lastmods)}")
        if distinct_lastmod == 1:
            print("- **ISSUE** — every URL shares one lastmod: the dates are generated, not real. "
                  "Crawlers learn to ignore lastmod when it is not trustworthy.")
    else:
        print("- **ISSUE** — no `<lastmod>` anywhere: crawlers get no recrawl signal.")
    if errors:
        print("\n**Child sitemaps that failed:**")
        for u, e in errors:
            print(f"- `{u}` — {e}")

    # Group by path shape so the sample is representative rather than the first N.
    buckets = {}
    for u, _ in entries:
        seg = urllib.parse.urlparse(u).path.strip("/").split("/")
        buckets.setdefault(seg[0] if seg and seg[0] else "(root)", []).append(u)
    print("\n### URL groups\n")
    print(md_table(["First path segment", "Count", "Example"],
                   [[k, len(v), truncate(v[0], 70)] for k, v in
                    sorted(buckets.items(), key=lambda kv: -len(kv[1]))[:15]]))

    sample = []
    for k, v in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
        sample.append(v[0])
        if len(sample) >= args.pages:
            break
    print("\n### Recommended sample for page-level audit\n")
    for u in sample:
        print(f"- {u}")
    return 0


def cmd_site(args):
    origin = normalise_origin(args.target)
    print(f"# SEO evidence pack: {origin}")
    print(f"_collected {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} by "
          f"seo-probe {VERSION} as `{args.ua}`_\n")
    print("> Every value below was measured, not inferred. Cite these values directly;\n"
          "> anything not listed here was not verified.\n")

    rc = cmd_preflight(args)
    if rc != 0:
        return rc
    print("\n---\n")
    cmd_redirects(args)
    print("\n---\n")
    cmd_robots(args)
    print("\n---\n")

    sitemap_url = origin + "/sitemap.xml"
    entries, _ = collect_sitemap_urls(sitemap_url, args)
    if not entries:
        robots_res = fetch(origin + "/robots.txt", ua=args.ua_string, timeout=args.timeout)
        if robots_res.ok and robots_res.status == 200:
            _, sitemaps, _ = parse_robots(robots_res.text)
            if sitemaps:
                sitemap_url = sitemaps[0][0]
                entries, _ = collect_sitemap_urls(sitemap_url, args)
    saved_target = args.target
    args.target = sitemap_url
    cmd_sitemap(args)
    args.target = saved_target
    print("\n---\n")

    # llms.txt
    llms = fetch(origin + "/llms.txt", ua=args.ua_string, timeout=args.timeout)
    print("## llms.txt\n")
    if llms.ok and llms.status == 200 and b"<html" not in llms.body[:500].lower():
        print(f"- Present: {len(llms.body):,} bytes, {len(llms.text.splitlines())} lines")
        print(f"- First lines:\n```\n{chr(10).join(llms.text.splitlines()[:8])}\n```")
    else:
        print(f"- **MISSING** (HTTP {llms.status}) — no `/llms.txt`. "
              "Optional and not yet honoured by every assistant, but cheap to add.")
    print("\n---\n")

    pages = []
    if entries:
        buckets = {}
        for u, _ in entries:
            seg = urllib.parse.urlparse(u).path.strip("/").split("/")
            buckets.setdefault(seg[0] if seg and seg[0] else "(root)", []).append(u)
        for _, v in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
            pages.append(v[0])
            if len(pages) >= args.pages:
                break
    if origin + "/" not in pages:
        pages.insert(0, origin + "/")
    pages = pages[: args.pages + 1]

    print(f"# Page-level probes ({len(pages)} pages)\n")
    for u in pages:
        args.target = u
        cmd_page(args)
        print("\n---\n")
    args.target = saved_target
    return 0


# --------------------------------------------------------------------------


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="seo-probe",
        description="Deterministic SEO/GEO evidence collector (stdlib only).",
    )
    ap.add_argument("command",
                    choices=["preflight", "page", "redirects", "robots", "sitemap", "site"])
    ap.add_argument("target", help="URL, origin, or domain")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--ua", default="default",
                    help="default | googlebot | bingbot | gptbot | claudebot | perplexity | browser | <raw UA>")
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--out", help="directory to save raw bodies into")
    ap.add_argument("-n", "--pages", type=int, default=5,
                    help="sitemap URLs to sample (default 5, max 25)")
    args = ap.parse_args(argv)
    args.pages = max(1, min(25, args.pages))
    args.ua_string = UA_PRESETS.get(args.ua, args.ua)

    handlers = {
        "preflight": cmd_preflight,
        "page": cmd_page,
        "redirects": cmd_redirects,
        "robots": cmd_robots,
        "sitemap": cmd_sitemap,
        "site": cmd_site,
    }
    try:
        return handlers[args.command](args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
