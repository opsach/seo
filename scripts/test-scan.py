#!/usr/bin/env python3
"""
test-scan.py -- regression tests for seo-scan.py against the fixtures in tests/fixtures.

Each fixture is a small project with known defects (or none). The scanner drives
/seo-fix, so a check that silently flips -- a false pass hides a real defect, a false
fail sends Claude to "fix" correct code -- is a product bug. These tests pin the
verdicts that matter, including the two Next.js behaviours verified against a real
build: a root-layout `canonical: '/'` is inherited by every page, `canonical: './'`
resolves per route.

Run from the repo root:  python3 scripts/test-scan.py      (exit 0 = all pass)
verify.py runs it too.
"""

from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN = os.path.join(ROOT, "scripts", "seo-scan.py")
FIX = os.path.join(ROOT, "tests", "fixtures")

failures: list[str] = []
passed = 0


def ok(cond, label, detail=""):
    global passed
    if cond:
        passed += 1
        print(f"  ok    {label}")
    else:
        failures.append(label)
        print(f"  FAIL  {label}" + (f" -- {detail}" if detail else ""))


def score(*args):
    out = subprocess.run([sys.executable, SCAN, "score", *args, "--json"], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"seo-scan score {' '.join(args)} exited {out.returncode}: {out.stderr[-400:]}")
    return json.loads(out.stdout)


def expect(res, fixture, statuses):
    for cid, want in statuses.items():
        got = res["checks"][cid]["status"]
        ok(got == want, f"{fixture}: {cid} is {want}", f"got {got}: {res['checks'][cid]['evidence'][:2]}")


def load_scan():
    spec = importlib.util.spec_from_file_location("seo_scan", SCAN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    scan = load_scan()

    print("\nstatic-fixed -- a correct site must reach 10/10")
    res = score(os.path.join(FIX, "static-fixed"))
    ok(res["score"] == 10.0, "static-fixed scores 10.0", str(res["score"]))
    bad = {k: v["status"] for k, v in res["checks"].items() if v["status"] in ("fail", "warn")}
    ok(not bad, "static-fixed has no fail/warn", str(bad))

    print("\nstatic-broken")
    res = score(os.path.join(FIX, "static-broken"))
    expect(res, "static-broken", {
        "robots-search-open": "fail", "ai-crawlers": "fail", "robots-syntax": "warn",
        "schema-valid": "fail", "schema-org": "fail", "title": "fail", "title-unique": "fail",
        "h1": "fail", "img-alt": "fail", "html-lang": "fail", "viewport": "fail",
        "canonical": "fail", "font-display": "warn", "server-rendered": "pass",
    })
    ok(res["score"] <= 3.0, "static-broken scores <= 3", str(res["score"]))
    ok(res["checks"]["robots-search-open"]["class"] == "review",
       "blocking search engines is a review item, never an auto fix")

    print("\nnext-app-broken -- source analysis")
    res = score(os.path.join(FIX, "next-app-broken"))
    expect(res, "next-app-broken", {
        "base-url": "fail", "canonical": "fail", "title": "fail", "title-unique": "fail",
        "description": "fail", "html-lang": "fail", "schema-escape": "fail", "schema-org": "warn",
        "sitemap-lastmod": "warn", "img-alt": "fail", "next-image": "warn", "og-tags": "fail",
        "server-rendered": "pass", "not-found": "pass",
    })
    ok("ROOT layout" in " ".join(res["checks"]["canonical"]["evidence"]),
       "root-layout canonical '/' is reported as inherited by every route")
    ok(any("app/about/page.tsx" in w for w in res["checks"]["title-unique"]["where"]),
       "title-unique points at the page file that lacks metadata")

    print("\nnext-app-fixed -- verified Next.js patterns must pass")
    res = score(os.path.join(FIX, "next-app-fixed"))
    expect(res, "next-app-fixed", {
        "base-url": "pass", "canonical": "pass", "title": "pass", "title-unique": "pass",
        "description": "pass", "description-unique": "pass", "html-lang": "pass", "og-tags": "pass",
        "og-image": "pass", "twitter-card": "pass", "favicon": "pass", "schema-org": "pass",
        "schema-escape": "pass", "robots-present": "pass", "robots-sitemap": "pass",
        "sitemap-present": "pass", "llms-txt": "pass", "img-alt": "pass", "next-image": "pass",
    })
    ok(res["score"] == 10.0, "next-app-fixed scores 10.0 on its scored checks", str(res["score"]))

    print("\nvite-spa -- client-rendered shell")
    res = score(os.path.join(FIX, "vite-spa"))
    expect(res, "vite-spa", {"server-rendered": "fail", "title": "fail", "title-unique": "fail",
                             "img-alt": "fail", "not-found": "fail", "base-url": "na"})
    ok(res["checks"]["title-unique"]["class"] == "review",
       "SPA unique titles need prerendering, so they are a review item")
    ok(res["checks"]["server-rendered"]["class"] == "review", "prerendering is a review item")

    print("\n--serve + --url: the full local-server lifecycle")
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    cmd = f'"{sys.executable}" -m http.server {port} --bind 127.0.0.1'
    res = score(os.path.join(FIX, "static-fixed"), "--serve", cmd, "--url", url)
    ok(len(res["pages"]) >= 3, "crawl reached all pages over HTTP", str(len(res["pages"])))
    ok(res["score"] == 10.0, "static-fixed over HTTP scores 10.0", str(res["score"]))
    ok(res["checks"]["not-found"]["status"] == "pass", "a real 404 is measured as pass")
    with socket.socket() as s:
        ok(s.connect_ex(("127.0.0.1", port)) != 0, "--serve stopped the server after the scan")

    print("\nsave / compare")
    with tempfile.TemporaryDirectory() as tmp:
        base = os.path.join(tmp, "base.json")
        subprocess.run([sys.executable, SCAN, "score", os.path.join(FIX, "static-broken"), "--save", base],
                       capture_output=True, check=True)
        out = subprocess.run([sys.executable, SCAN, "score", os.path.join(FIX, "static-fixed"), "--compare", base],
                             capture_output=True, text=True, check=True).stdout
        ok("## Change since" in out and "-> 10.0 / 10" in out, "--compare reports the score change")

    print("\nunits")
    groups, _, _ = scan.probe.parse_robots(
        "User-agent: *\nDisallow: /\n\nUser-agent: OAI-SearchBot\nUser-agent: PerplexityBot\nAllow: /\n")
    ok(scan.probe.robots_verdict(groups, "PerplexityBot")[0] == "allowed"
       and scan.probe.robots_verdict(groups, "OAI-SearchBot")[0] == "allowed"
       and scan.probe.robots_verdict(groups, "Googlebot")[0] == "blocked",
       "consecutive User-agent lines form one group (the playbook's robots.txt relies on it)")
    ok(not scan.good_site_url("https://shop.example") and not scan.good_site_url("http://localhost:3000")
       and scan.good_site_url("https://yourbrand.com"), "reserved and local hosts are never a production URL")
    keys = scan.top_level_keys("{ title: { default: 'A', template: '%s | B' }, description: 'x, y', ...rest }")
    ok(set(keys) == {"title", "description", "..."}, "JS object keys parse at depth 1 only", str(keys))
    ok(scan.literal("'x, y'") == "x, y" and scan.literal("`a ${b}`") is None, "string literals vs computed values")
    ok(scan.sitemap_lastmod_finding([("https://a.com/x", None)] * 3, "s", "rendered").status == "pass",
       "an omitted lastmod passes (the playbook's honest option)")
    ok(scan.sitemap_lastmod_finding([("https://a.com/x", "2026-01-01")] * 3, "s", "rendered").status == "warn",
       "identical lastmod on every URL warns (build-time stamps)")
    out = subprocess.run([sys.executable, SCAN, "len", "x" * 60, "y" * 150], capture_output=True, text=True).stdout
    ok("| 60 | fits | short |" in out and "| 150 | long | fits |" in out, "len reports the title/description bands")
    svg = os.path.join(FIX, "static-fixed", "img", "team.svg")
    ok(scan.image_size(svg) == (640, 360), "imgsize reads SVG dimensions")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as fh:
        import struct
        import zlib
        raw = b"\x00" + b"\x00\x00\x00" * 3
        chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
        fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 3, 1, 8, 2, 0, 0, 0))
                 + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    ok(scan.image_size(fh.name) == (3, 1), "imgsize reads PNG dimensions")
    os.unlink(fh.name)

    print(f"\n{passed} passed, {len(failures)} failed")
    for f in failures:
        print(f"  - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
