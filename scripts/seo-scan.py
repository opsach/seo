#!/usr/bin/env python3
"""
seo-scan -- codebase and rendered-output SEO/GEO scanner, scorer, and fix planner
for the seo-geo-consultant plugin.

seo-probe answers "what does this live URL serve?". seo-scan answers what a fix run
needs to know: what stack this is, where each SEO surface lives in the code, which
checks fail, which failures can be fixed without a human decision, and whether the
fixes worked. It scores the project out of 10 from deterministic checks, so that
"before" and "after" are measurements rather than impressions.

Evidence, strongest first:
  rendered  HTML the site actually serves -- a build output directory (--html DIR)
            or a running server, local or live (--url URL). Authoritative.
  source    heuristics over the codebase (config, layouts, templates). Used to find
            *where* to fix, and to score what rendered evidence cannot see.

Standard library only. Needs seo-probe.py in the same directory.

Usage:
  seo-scan.py detect  [PATH]                 stack, render recipe, SEO surface map, facts
  seo-scan.py score   [PATH | URL]           scorecard + fix plan
                      [--html DIR]           add rendered evidence from a build output dir
                      [--url URL]            add rendered evidence from a running server
                      [--serve "CMD"]        start CMD (e.g. "npx next start -p 4319"), wait for
                                             --url to answer, scan, then stop it -- always
                      [-n N]                 pages to crawl in --url mode (default 15)
                      [--save [FILE]]        store the result (default: a temp file per target)
                      [--compare [FILE]]     show the change against a saved result
                      [--json]               machine-readable output
  seo-scan.py imgsize FILE [FILE ...]        intrinsic width x height (png/jpg/gif/webp/svg)

Exit codes:
  0  ok (a low score is a result, not an error)
  3  a --url target is blocked by network/egress policy   (same as seo-probe)
  4  a --url target blocks automated clients              (same as seo-probe)
  5  a --url target is unreachable                        (same as seo-probe)
  6  usage error, or seo-probe.py missing
  7  --serve: the local server did not start (its log tail is printed)
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import signal
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = "1.0"


def _load_probe():
    path = os.path.join(HERE, "seo-probe.py")
    if not os.path.isfile(path):
        sys.stderr.write(
            f"seo-scan: seo-probe.py not found next to this script ({HERE}).\n"
            "The two ship together -- re-run the plugin installer.\n")
        sys.exit(6)
    spec = importlib.util.spec_from_file_location("seo_probe", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


probe = _load_probe()

# --------------------------------------------------------------------------
# Check registry
# --------------------------------------------------------------------------
# class:  auto   -- safe to fix without asking: derived from the site itself
#         input  -- fixable once a business fact is supplied (never invented)
#         review -- a behaviour change or business decision: needs approval
# weight: 3 = can deindex or hide the site, 2 = standard requirement, 1 = hygiene

CATEGORIES = [
    ("crawl", "Crawl & index"),
    ("meta", "Metadata"),
    ("content", "On-page structure"),
    ("schema", "Structured data"),
    ("social", "Social sharing"),
    ("geo", "AI search (GEO)"),
    ("perf", "Performance hygiene"),
]

CHECKS = {
    # id: (category, title, weight, class, facts needed)
    "robots-present": ("crawl", "robots.txt is served", 2, "auto", ()),
    "robots-search-open": ("crawl", "Search engines may crawl the site", 3, "review", ()),
    "robots-syntax": ("crawl", "robots.txt parses cleanly", 1, "auto", ()),
    "robots-sitemap": ("crawl", "robots.txt names the sitemap (absolute URL)", 1, "input", ("site_url",)),
    "sitemap-present": ("crawl", "XML sitemap is served", 2, "input", ("site_url",)),
    "sitemap-lastmod": ("crawl", "Sitemap lastmod values are real change dates", 1, "auto", ()),
    "not-found": ("crawl", "Unknown URLs return HTTP 404", 1, "auto", ()),
    "noindex-sitewide": ("crawl", "No accidental sitewide noindex", 3, "review", ()),
    "base-url": ("meta", "Production base URL is configured", 2, "input", ("site_url",)),
    "title": ("meta", "Every page has a title (15-65 chars)", 3, "auto", ()),
    "title-unique": ("meta", "Page titles are unique", 2, "auto", ()),
    "description": ("meta", "Every page has a meta description (70-165 chars)", 2, "auto", ()),
    "description-unique": ("meta", "Meta descriptions are unique", 1, "auto", ()),
    "canonical": ("meta", "Every page has a self-referencing absolute canonical", 2, "input", ("site_url",)),
    "html-lang": ("meta", "<html lang> is set", 2, "auto", ()),
    "viewport": ("meta", "Mobile viewport meta is set", 1, "auto", ()),
    "favicon": ("meta", "A favicon is declared", 1, "input", ("icon",)),
    "h1": ("content", "Exactly one H1 per page", 2, "auto", ()),
    "img-alt": ("content", "Every image has an alt attribute", 2, "auto", ()),
    "schema-org": ("schema", "Homepage has Organization + WebSite JSON-LD", 2, "input", ("brand", "site_url")),
    "schema-valid": ("schema", "All JSON-LD parses", 3, "auto", ()),
    "schema-escape": ("schema", "Inline JSON-LD escapes '<' (XSS-safe)", 1, "auto", ()),
    "schema-article": ("schema", "Article pages carry Article/BlogPosting JSON-LD", 1, "auto", ()),
    "og-tags": ("social", "Open Graph title/description/type on every page", 2, "auto", ()),
    "og-image": ("social", "Absolute og:image for link previews", 2, "input", ("og_image",)),
    "twitter-card": ("social", "twitter:card is set", 1, "auto", ()),
    "llms-txt": ("geo", "/llms.txt is published", 1, "input", ("brand", "site_url")),
    "ai-crawlers": ("geo", "AI search and user fetchers are not blocked", 2, "review", ()),
    "server-rendered": ("geo", "Primary content is in the server HTML", 3, "review", ()),
    "img-dimensions": ("perf", "Images declare width and height (CLS)", 1, "auto", ()),
    "font-display": ("perf", "Web fonts load with font-display: swap", 1, "auto", ()),
    "next-image": ("perf", "Next.js images use next/image", 1, "review", ()),
}

CREDIT = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
CLASS_LABEL = {
    "auto": "Auto-fixable now",
    "input": "Fixable once a fact is supplied",
    "review": "Needs approval",
}

# AI fetchers that decide whether a site can be *cited*. Training crawlers are a
# licensing choice, reported but not scored.
AI_CITATION_BOTS = ["OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot", "Claude-User",
                    "PerplexityBot", "Perplexity-User"]
AI_TRAINING_BOTS = ["GPTBot", "ClaudeBot", "Google-Extended", "Applebot-Extended", "CCBot"]

ORG_TYPES = {
    "Organization", "Corporation", "LocalBusiness", "OnlineStore", "OnlineBusiness",
    "NGO", "NewsMediaOrganization", "EducationalOrganization", "MedicalOrganization",
    "SportsOrganization", "Restaurant", "Store", "ProfessionalService", "Person",
    "Brand", "GovernmentOrganization", "Airline", "Consortium", "Dentist", "Physician",
    "LegalService", "HomeAndConstructionBusiness", "AutomotiveBusiness", "FoodEstablishment",
    "HealthAndBeautyBusiness", "LodgingBusiness", "Hotel", "RealEstateAgent", "TravelAgency",
    "FinancialService", "EntertainmentBusiness", "SportsActivityLocation", "ShoppingCenter",
}
ORG_SUFFIXES = ("Organization", "Business", "Store", "Shop", "Service", "Agency", "Restaurant", "Clinic",
                "Contractor", "Salon", "Club", "Center", "Centre")
ORG_TYPES |= {"Plumber", "Electrician", "HVACBusiness", "RoofingContractor", "GeneralContractor", "Locksmith",
              "MovingCompany", "HousePainter", "AutoRepair", "AutoDealer", "Bakery", "BarOrPub", "CafeOrCoffeeShop",
              "Winery", "Brewery", "MedicalClinic", "Optician", "Pharmacy", "VeterinaryCare", "Attorney", "Notary",
              "AccountingService", "InsuranceAgency", "ChildCare", "DryCleaningOrLaundry", "ExerciseGym", "Florist",
              "Motel", "BedAndBreakfast", "Hostel", "Resort", "Campground", "Library", "SelfStorage", "Winery"}


def is_org_type(t):
    return t in ORG_TYPES or t.endswith(ORG_SUFFIXES)


ARTICLE_TYPES = {"Article", "BlogPosting", "NewsArticle", "TechArticle", "Report",
                 "ScholarlyArticle", "AnalysisNewsArticle", "OpinionNewsArticle"}
ARTICLE_PATH = re.compile(r"^/(?:[a-z]{2}(?:-[a-z]{2})?/)?(blog|news|articles?|posts?|insights|guides|stories|journal)/[^/]+", re.I)

PLACEHOLDER_HOSTS = ("example.com", "example.org", "yourdomain.com", "yoursite.com",
                     "domain.com", "localhost", "127.0.0.1", "0.0.0.0")
DEFAULT_TITLES = {"create next app", "vite + react", "vite + react + ts", "react app", "vite app",
                  "astro", "my site", "welcome to astro", "sveltekit app", "nuxt", "gatsby",
                  "vite + vue", "vite + svelte", "home", "untitled", "document", "index"}

SKIP_DIRS = {"node_modules", ".git", ".next", ".nuxt", ".output", ".svelte-kit", ".astro",
             ".vercel", ".netlify", ".cache", ".turbo", ".parcel-cache", "vendor",
             "bower_components", "coverage", "__pycache__", ".venv", "venv", ".claude",
             ".idea", ".vscode", "storybook-static", ".docusaurus", "resources"}
OUTPUT_DIRS = {"dist", "build", "out", "_site"}
SOURCE_EXT = (".tsx", ".jsx", ".ts", ".js", ".mjs", ".mdx", ".astro", ".vue", ".svelte",
              ".html", ".htm", ".njk", ".liquid", ".php", ".hbs", ".erb", ".md")
MAX_FILES = 25000


# --------------------------------------------------------------------------
# Small utilities
# --------------------------------------------------------------------------


class Finding:
    """The outcome of one check."""

    def __init__(self, status, evidence=None, where=None, note="", basis="source", klass=None):
        self.status = status          # pass | warn | fail | na | unknown
        self.evidence = evidence or []
        self.where = where or []
        self.note = note
        self.basis = basis            # rendered | source
        self.klass = klass            # overrides the registry's fix class for this project

    def as_dict(self, cid=None):
        return {"status": self.status, "evidence": self.evidence, "where": self.where,
                "note": self.note, "basis": self.basis,
                "class": self.klass or (CHECKS[cid][3] if cid else None)}


def md_table(headers, rows):
    return probe.md_table(headers, rows)


def trunc(s, n=80):
    return probe.truncate(s, n)


def is_url(s):
    return bool(re.match(r"^https?://", s or "", re.I))


def good_site_url(u):
    if not u or not is_url(u):
        return False
    host = (urllib.parse.urlsplit(u).hostname or "").lower()
    if not host or host.endswith((".example", ".test", ".invalid", ".localhost", ".local")):
        return False  # RFC 2606 / 6761 reserved names never serve production
    return not any(host == p or host.endswith("." + p) for p in PLACEHOLDER_HOSTS)


def norm_path(u):
    p = urllib.parse.urlsplit(u).path or "/"
    p = re.sub(r"/index\.html?$", "/", p)
    p = re.sub(r"\.html?$", "", p)
    return p.rstrip("/") or "/"


def frac_status(bad, total, warn_at=0.25):
    """0 offenders pass; a minority is a warning; more than warn_at is a failure."""
    if not bad:
        return "pass"
    return "warn" if total and bad / total <= warn_at else "fail"


def js_object_at(text, start):
    """Return the balanced {...} starting at text[start] == '{' (strings respected)."""
    depth, i, n, quote = 0, start, len(text), None
    while i < n:
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "'\"`":
            quote = c
        elif c == "/" and text[i:i + 2] == "//":
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        elif c == "/" and text[i:i + 2] == "/*":
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        elif c in "{[(":
            depth += 1
        elif c in "}])":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    return None


def top_level_keys(obj):
    """Map top-level keys of a JS object literal to their raw value text.
    A spread (`...x`) is recorded as the key '...'."""
    if not obj or obj[0] != "{":
        return {}
    body, out = obj[1:-1], {}
    depth, quote, buf, parts, i = 0, None, [], [], 0
    while i < len(body):
        c = body[i]
        if quote:
            buf.append(c)
            if c == "\\" and i + 1 < len(body):
                buf.append(body[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "'\"`":
            quote = c
            buf.append(c)
        elif c == "/" and body[i:i + 2] == "//":
            j = body.find("\n", i)
            i = len(body) if j == -1 else j
            continue
        elif c in "{[(":
            depth += 1
            buf.append(c)
        elif c in "}])":
            depth -= 1
            buf.append(c)
        elif c == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(c)
        i += 1
    parts.append("".join(buf))
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if part.startswith("..."):
            out["..."] = part[3:]
            continue
        m = re.match(r"""^(?:['"]([^'"]+)['"]|([A-Za-z_$][\w$]*))\s*:\s*(.*)$""", part, re.S)
        if m:
            out[m.group(1) or m.group(2)] = m.group(3).strip()
        elif re.match(r"^[A-Za-z_$][\w$]*$", part):
            out[part] = part  # shorthand property
    return out


def literal(value):
    """The string value of a JS literal, or None when it is computed."""
    if not value:
        return None
    m = re.match(r"""^(['"])(.*)\1$""", value.strip(), re.S)
    if m:
        return m.group(2)
    m = re.match(r"^`([^`$]*)`$", value.strip(), re.S)
    return m.group(1) if m else None


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


# --------------------------------------------------------------------------
# Project model
# --------------------------------------------------------------------------

STACKS = {
    "nextjs-app": ("Next.js (App Router)", "nextjs-implementation.md"),
    "nextjs-pages": ("Next.js (Pages Router)", "nextjs-implementation.md"),
    "vite": ("Vite single-page app", "react-spa-implementation.md"),
    "cra": ("Create React App", "react-spa-implementation.md"),
    "astro": ("Astro", "fix-playbook.md"),
    "nuxt": ("Nuxt", "fix-playbook.md"),
    "sveltekit": ("SvelteKit", "fix-playbook.md"),
    "gatsby": ("Gatsby", "fix-playbook.md"),
    "remix": ("Remix / React Router", "fix-playbook.md"),
    "docusaurus": ("Docusaurus", "fix-playbook.md"),
    "eleventy": ("Eleventy", "fix-playbook.md"),
    "hugo": ("Hugo", "fix-playbook.md"),
    "jekyll": ("Jekyll", "fix-playbook.md"),
    "wordpress": ("WordPress (full install)", "cms-implementation.md"),
    "wordpress-theme": ("WordPress theme", "cms-implementation.md"),
    "shopify-theme": ("Shopify theme", "cms-implementation.md"),
    "static": ("Static HTML", "fix-playbook.md"),
    "unknown": ("Unrecognised", "fix-playbook.md"),
}


class Project:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self._cache = {}
        self.files = self._walk()
        self.pkg = self.json("package.json") or {}
        self.deps = {}
        for k in ("dependencies", "devDependencies", "peerDependencies"):
            self.deps.update(self.pkg.get(k) or {})
        self.stack = self._stack()
        self.label, self.reference = STACKS[self.stack]
        self.public = self._public_dir()

    # -- file access -------------------------------------------------------
    def _walk(self):
        out = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            rel_dir = os.path.relpath(dirpath, self.root).replace(os.sep, "/")
            depth = 0 if rel_dir == "." else rel_dir.count("/") + 1
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS
                                 and not (depth == 0 and d in OUTPUT_DIRS))
            for f in sorted(filenames):
                out.append(f if rel_dir == "." else f"{rel_dir}/{f}")
                if len(out) >= MAX_FILES:
                    return out
        return out

    def has(self, rel):
        return os.path.isfile(os.path.join(self.root, rel))

    def first(self, *rels):
        for r in rels:
            if self.has(r):
                return r
        return None

    def find(self, pattern):
        rx = re.compile(pattern)
        return [f for f in self.files if rx.search(f)]

    def read(self, rel):
        if rel not in self._cache:
            try:
                if os.path.getsize(os.path.join(self.root, rel)) > 2_000_000:
                    self._cache[rel] = ""  # minified bundles and media are never SEO source
                    return ""
                with open(os.path.join(self.root, rel), encoding="utf-8", errors="replace") as fh:
                    self._cache[rel] = fh.read()
            except OSError:
                self._cache[rel] = ""
        return self._cache[rel]

    def json(self, rel):
        if not self.has(rel):
            return None
        try:
            return json.loads(self.read(rel))
        except ValueError:
            return None

    def dep(self, *names):
        return next((n for n in names if n in self.deps), None)

    # -- classification ------------------------------------------------------
    def app_dir(self):
        for d in ("app", "src/app"):
            if self.find(rf"^{re.escape(d)}/(?:\([^/]+\)/)?layout\.(tsx|jsx|ts|js)$"):
                return d
        return None

    def _stack(self):
        if self.dep("next"):
            return "nextjs-app" if self.app_dir() else "nextjs-pages"
        for name, stack in (("astro", "astro"), ("nuxt", "nuxt"), ("nuxt3", "nuxt"),
                            ("@sveltejs/kit", "sveltekit"), ("gatsby", "gatsby"),
                            ("@remix-run/react", "remix"), ("@react-router/dev", "remix"),
                            ("@docusaurus/core", "docusaurus"), ("@11ty/eleventy", "eleventy"),
                            ("react-scripts", "cra"), ("vite", "vite")):
            if self.dep(name):
                return stack
        if self.first("hugo.toml", "hugo.yaml", "hugo.json") or (
                self.first("config.toml", "config.yaml") and (self.has("archetypes/default.md")
                                                                or self.find(r"^layouts/"))):
            return "hugo"
        if self.has("_config.yml") and ("jekyll" in self.read("Gemfile").lower()
                                        or self.find(r"^_(layouts|posts|includes)/")):
            return "jekyll"
        if self.has("layout/theme.liquid"):
            return "shopify-theme"
        if self.has("wp-config.php") or self.find(r"^wp-content/"):
            return "wordpress"
        if self.has("style.css") and "theme name:" in self.read("style.css").lower() \
                and self.has("functions.php"):
            return "wordpress-theme"
        if self.find(r"\.html?$"):
            return "static"
        return "unknown"

    def _public_dir(self):
        if self.stack in ("gatsby", "hugo", "docusaurus", "sveltekit"):
            return "static"
        if self.stack in ("jekyll", "static", "wordpress-theme", "unknown"):
            return ""
        if self.stack == "nuxt" and not os.path.isdir(os.path.join(self.root, "public")) \
                and os.path.isdir(os.path.join(self.root, "static")):
            return "static"
        return "public"

    def pub(self, name):
        """Path of a file served from the web root, if it exists in source."""
        rel = f"{self.public}/{name}" if self.public else name
        return rel if self.has(rel) else None

    def pub_path(self, name):
        return f"{self.public}/{name}" if self.public else name

    # -- package manager and render recipe ---------------------------------
    def package_manager(self):
        if self.has("pnpm-lock.yaml"):
            return "pnpm"
        if self.has("yarn.lock"):
            return "yarn"
        if self.has("bun.lockb") or self.has("bun.lock"):
            return "bun"
        return "npm"

    def render_recipe(self, port=4319):
        """How to get authoritative rendered HTML for this stack."""
        pm = self.package_manager()
        scripts = self.pkg.get("scripts") or {}
        build = f"{pm} run build" if "build" in scripts else None
        installed = os.path.isdir(os.path.join(self.root, "node_modules"))
        install = None if installed or not self.pkg else f"{pm} install"
        s = self.stack
        next_cfg = "".join(self.read(f) for f in self.find(r"^next\.config\.(js|mjs|ts|cjs)$"))
        if s in ("nextjs-app", "nextjs-pages"):
            if re.search(r"output\s*:\s*['\"]export['\"]", next_cfg):
                return dict(kind="html", install=install, build=build, dir="out")
            return dict(kind="url", install=install, build=build,
                        serve=f"npx next start -p {port}", url=f"http://localhost:{port}")
        if s == "astro":
            cfg = "".join(self.read(f) for f in self.find(r"^astro\.config\.(mjs|js|ts|mts)$"))
            if re.search(r"output\s*:\s*['\"]server['\"]", cfg):
                return dict(kind="url", install=install, build=build,
                            serve=f"npx astro preview --port {port}", url=f"http://localhost:{port}")
            return dict(kind="html", install=install, build=build, dir="dist")
        if s in ("vite", "sveltekit"):
            if s == "sveltekit":
                return dict(kind="url", install=install, build=build,
                            serve=f"npx vite preview --port {port} --strictPort",
                            url=f"http://localhost:{port}")
            return dict(kind="html", install=install, build=build, dir="dist")
        if s == "cra":
            return dict(kind="html", install=install, build=build, dir="build")
        if s == "nuxt":
            return dict(kind="html", install=install, build="npx nuxi generate", dir=".output/public")
        if s == "gatsby":
            return dict(kind="html", install=install, build=build or "npx gatsby build", dir="public")
        if s == "docusaurus":
            return dict(kind="html", install=install, build=build, dir="build")
        if s == "eleventy":
            return dict(kind="html", install=install, build=build or "npx @11ty/eleventy", dir="_site")
        if s == "hugo":
            return dict(kind="html", install=None, build="hugo --minify", dir="public")
        if s == "jekyll":
            return dict(kind="html", install="bundle install", build="bundle exec jekyll build", dir="_site")
        if s == "remix":
            return dict(kind="url", install=install, build=build,
                        serve=f"PORT={port} {pm} run start", url=f"http://localhost:{port}")
        if s == "static":
            return dict(kind="html", install=None, build=None, dir=".")
        return dict(kind="url", install=None, build=None, serve=None,
                    url="the live site (no local build for this stack)")


# --------------------------------------------------------------------------
# Facts: values fixes need, discovered from the project (never invented)
# --------------------------------------------------------------------------

SOCIAL_RX = re.compile(
    r"https?://(?:www\.)?(?:twitter\.com|x\.com|linkedin\.com/(?:company|in)|github\.com|"
    r"facebook\.com|instagram\.com|youtube\.com/(?:@|c/|channel/)|tiktok\.com/@|"
    r"threads\.net/@|bsky\.app/profile|mastodon\.social/@)[A-Za-z0-9_.@/-]*[A-Za-z0-9_]")
SOCIAL_NOISE = re.compile(r"/(intent|share|sharer|home\?|search)|github\.com/(vercel|vitejs|facebook|"
                          r"withastro|sveltejs|nuxt|gatsbyjs|remix-run|shadcn|tailwindlabs|"
                          r"opsach|anthropics)|twitter\.com/(vercel|nextjs|vite_js|astrodotbuild)"
                          r"|x\.com/(vercel|nextjs|vite_js|astrodotbuild)", re.I)


def discover_facts(p: Project):
    facts = {}

    def put(key, value, source, confidence="found"):
        if value and key not in facts:
            facts[key] = {"value": value, "source": source, "confidence": confidence}

    # -- site_url ------------------------------------------------------------
    cands = []
    for rel in [f for f in p.files if f.endswith("CNAME")][:3]:
        host = p.read(rel).strip().splitlines()[0].strip() if p.read(rel).strip() else ""
        if host and "." in host:
            cands.append((f"https://{host}", rel))
    patterns = [
        (r"^next\.config\.", r"""(?:siteUrl|SITE_URL)\s*[:=]\s*['"](https?://[^'"]+)"""),
        (r"^(src/)?app/(\([^/]+\)/)?layout\.", r"""metadataBase\s*:\s*new URL\(\s*['"](https?://[^'"]+)"""),
        (r"^astro\.config\.", r"""\bsite\s*:\s*['"](https?://[^'"]+)"""),
        (r"^nuxt\.config\.", r"""\burl\s*:\s*['"](https?://[^'"]+)"""),
        (r"^gatsby-config\.", r"""siteUrl\s*:\s*['"](https?://[^'"]+)"""),
        (r"^docusaurus\.config\.", r"""\burl\s*:\s*['"](https?://[^'"]+)"""),
        (r"^(hugo|config)\.(toml|yaml|yml)$", r"""(?im)^\s*baseurl\s*[:=]\s*['"]?(https?://[^'"\s]+)"""),
        (r"^_config\.yml$", r"""(?m)^url\s*:\s*['"]?(https?://[^'"\s]+)"""),
        (r"^\.env(\.[\w.]+)?$", r"""(?m)^[A-Z_]*(?:SITE|BASE|PUBLIC|APP)_?URL\s*=\s*['"]?(https?://[^'"\s]+)"""),
        (r"^(src/)?(lib|config|constants|utils)/[\w-]*(site|config|constants|seo)[\w-]*\.(ts|js|mjs)$",
         r"""(?:SITE_URL|siteUrl|BASE_URL|baseUrl|url)\s*[:=]\s*['"](https?://[^'"]+)"""),
    ]
    for file_rx, value_rx in patterns:
        for rel in p.find(file_rx)[:6]:
            for m in re.finditer(value_rx, p.read(rel)):
                cands.append((m.group(1), f"{rel}:{line_of(p.read(rel), m.start())}"))
    home = p.pub("index.html") or p.first("index.html", "public/index.html", "src/index.html")
    if home:
        html = p.read(home)
        for rx in (r"""<link[^>]+rel=["']canonical["'][^>]+href=["'](https?://[^"']+)""",
                   r"""<meta[^>]+property=["']og:url["'][^>]+content=["'](https?://[^"']+)"""):
            m = re.search(rx, html, re.I)
            if m:
                cands.append((m.group(1), f"{home}:{line_of(html, m.start())}"))
    homepage = p.pkg.get("homepage")
    if isinstance(homepage, str):
        cands.append((homepage, "package.json homepage"))
    for rel in filter(None, [p.pub("robots.txt"), p.pub("sitemap.xml")]):
        m = re.search(r"(?:Sitemap:\s*|<loc>\s*)(https?://[^\s<]+)", p.read(rel), re.I)
        if m:
            cands.append((m.group(1), rel))
    for value, src in cands:
        if good_site_url(value):
            parts = urllib.parse.urlsplit(value)
            put("site_url", f"{parts.scheme}://{parts.netloc}", src)
            break
    else:
        weak = [(v, s) for v, s in cands if is_url(v)]
        if weak:
            put("site_url", weak[0][0], weak[0][1] + " (placeholder or local -- confirm)", "weak")

    # -- brand -------------------------------------------------------------
    brand_patterns = [
        (r"^(src/)?app/(\([^/]+\)/)?layout\.", r"""siteName\s*:\s*['"]([^'"]{2,60})['"]"""),
        (r"^(src/)?app/(\([^/]+\)/)?layout\.", r"""template\s*:\s*['"`]%s\s*[|\-–—·:]\s*([^'"`]{2,60})['"`]"""),
        (r"^(hugo|config)\.(toml|yaml|yml)$", r"""(?im)^\s*title\s*[:=]\s*['"]?([^'"\n]{2,60})"""),
        (r"^_config\.yml$", r"""(?m)^title\s*:\s*['"]?([^'"\n]{2,60})"""),
        (r"^gatsby-config\.", r"""title\s*:\s*['"]([^'"]{2,60})['"]"""),
        (r"^docusaurus\.config\.", r"""title\s*:\s*['"]([^'"]{2,60})['"]"""),
        (r"(^|/)(site\.webmanifest|manifest\.json)$", r'''"name"\s*:\s*"([^"]{2,60})"'''),
        (r"^(src/)?app/manifest\.(ts|js)$", r"""name\s*:\s*['"]([^'"]{2,60})['"]"""),
    ]
    for file_rx, value_rx in brand_patterns:
        for rel in p.find(file_rx)[:4]:
            m = re.search(value_rx, p.read(rel))
            if m and m.group(1).strip().lower() not in DEFAULT_TITLES:
                put("brand", m.group(1).strip(), f"{rel}:{line_of(p.read(rel), m.start())}")
    if home:
        html = p.read(home)
        m = re.search(r"""<meta[^>]+property=["']og:site_name["'][^>]+content=["']([^"']+)""", html, re.I)
        if m:
            put("brand", m.group(1).strip(), f"{home}:{line_of(html, m.start())}")
        m = re.search(r"<title>([^<]{2,80})</title>", html, re.I)
        if m and m.group(1).strip().lower() not in DEFAULT_TITLES:
            put("brand", re.split(r"\s+[|\-–—·:]\s+", m.group(1).strip())[-1],
                f"{home}:{line_of(html, m.start())} (from <title> -- confirm)", "weak")

    # -- language ----------------------------------------------------------
    lang_files = p.find(r"^(src/)?app/(\([^/]+\)/)?layout\.|^pages/_document\.|^src/pages/_document\."
                        r"|^(src/)?layouts?/.*\.(astro|html|vue|svelte)$|^src/app\.html$|^index\.html$"
                        r"|^public/index\.html$|^layout/theme\.liquid$|^_layouts/.*\.html$")
    for rel in lang_files[:10]:
        m = re.search(r"""<(?:html|Html)[^>]*\blang=["'{]([A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?)["'}]""", p.read(rel))
        if m:
            put("lang", m.group(1), f"{rel}:{line_of(p.read(rel), m.start())}")
            break
    for rel in p.find(r"^(hugo|config)\.(toml|yaml|yml)$|^_config\.yml$")[:2]:
        m = re.search(r"""(?im)^\s*(?:languageCode|defaultContentLanguage|lang)\s*[:=]\s*['"]?([A-Za-z-]{2,8})""",
                      p.read(rel))
        if m:
            put("lang", m.group(1), rel)

    # -- assets ------------------------------------------------------------
    assets = [f for f in p.files if re.search(r"\.(svg|png|jpe?g|webp|ico|avif)$", f, re.I)
              and not re.search(r"(^|/)(node_modules|tests?|fixtures?|__tests__)/", f)]
    logo = [f for f in assets if re.search(r"(^|/)[^/]*logo[^/]*\.(svg|png|webp|jpe?g)$", f, re.I)]
    if logo:
        put("logo", sorted(logo, key=len)[0], "asset in repo")
    og = [f for f in assets if re.search(r"(^|/)(og|opengraph|open-graph|social|share|twitter)[-_.]?"
                                         r"(image|card|default|preview)?[^/]*\.(png|jpe?g|webp)$", f, re.I)]
    og += p.find(r"^(src/)?app/(\([^/]+\)/)?opengraph-image\.(tsx|jsx|ts|js|png|jpe?g)$")
    if og:
        put("og_image", sorted(og, key=len)[0], "asset in repo")
    icon = [f for f in assets if re.search(r"(^|/)(favicon[^/]*\.(ico|png|svg)|icon\.(png|svg|ico)|"
                                           r"apple-touch-icon[^/]*\.png)$", f, re.I)]
    if icon:
        put("icon", sorted(icon, key=len)[0], "asset in repo")

    # -- social profiles (sameAs) -------------------------------------------
    found = {}
    for rel in p.files:
        if not rel.endswith(SOURCE_EXT) or rel.startswith(("docs/", "test", "tests/")):
            continue
        text = p.read(rel)
        if "http" not in text:
            continue
        for m in SOCIAL_RX.finditer(text):
            url = m.group(0).rstrip("/.")
            if not SOCIAL_NOISE.search(url) and url.count("/") >= 3:
                found.setdefault(url, rel)
        if len(found) > 12:
            break
    if found:
        put("same_as", sorted(found), ", ".join(sorted(set(found.values()))[:3]))
    return facts


# --------------------------------------------------------------------------
# Source analysis
# --------------------------------------------------------------------------


def parse_html_file(text):
    parser = probe.PageParser()
    try:
        parser.feed(text)
    except Exception:  # noqa: BLE001 - malformed HTML is itself evidence
        pass
    return parser


def robots_findings(text, where, basis):
    """robots.txt text -> findings for the five robots/AI checks."""
    groups, sitemaps, problems = probe.parse_robots(text)
    out = {"robots-present": Finding("pass", [f"{where} ({len(text.splitlines())} lines)"], [where], basis=basis)}
    blocked = [b for b in ("Googlebot", "Bingbot") if probe.robots_verdict(groups, b)[0] == "blocked"]
    if blocked:
        why = [f"{b}: {probe.robots_verdict(groups, b)[1]} (line {probe.robots_verdict(groups, b)[2]})"
               for b in blocked]
        out["robots-search-open"] = Finding("fail", why, [where],
                                            "If this is a staging robots.txt shipped to production, "
                                            "the whole site is invisible to search.", basis)
    else:
        out["robots-search-open"] = Finding("pass", ["Googlebot and Bingbot allowed at /"], [where], basis=basis)
    ai_blocked = [b for b in AI_CITATION_BOTS if probe.robots_verdict(groups, b)[0] == "blocked"]
    train_blocked = [b for b in AI_TRAINING_BOTS if probe.robots_verdict(groups, b)[0] == "blocked"]
    note = (f"Training crawlers blocked (a licensing choice, not scored): {', '.join(train_blocked)}"
            if train_blocked else "")
    if ai_blocked:
        out["ai-crawlers"] = Finding("fail", [f"blocked at /: {', '.join(ai_blocked)}"], [where], note, basis)
    else:
        out["ai-crawlers"] = Finding("pass", ["AI search and user fetchers allowed at /"], [where], note, basis)
    out["robots-syntax"] = Finding("pass" if not problems else "warn",
                                   [f"line {ln}: {msg}" for ln, msg in problems[:6]] or ["no syntax problems"],
                                   [where], basis=basis)
    absolute = [u for u, _ in sitemaps if is_url(u)]
    if absolute:
        out["robots-sitemap"] = Finding("pass", [f"Sitemap: {absolute[0]}"], [where], basis=basis)
    elif sitemaps:
        out["robots-sitemap"] = Finding("fail", [f"line {sitemaps[0][1]}: relative Sitemap URL {sitemaps[0][0]!r}"],
                                        [where], "The Sitemap directive must be an absolute URL.", basis)
    else:
        out["robots-sitemap"] = Finding("fail", ["no Sitemap: directive"], [where], basis=basis)
    return out


def sitemap_lastmod_finding(entries, where, basis):
    lastmods = [lm for _, lm in entries if lm]
    if not entries:
        return Finding("unknown", ["sitemap has no <url> entries to inspect"], [where], basis=basis)
    if not lastmods:
        return Finding("warn", [f"{len(entries)} URLs, none with <lastmod>"], [where],
                       "No recrawl signal. Add real change dates, or omit lastmod rather than fake it.", basis)
    days = {lm[:10] for lm in lastmods}
    if len(entries) >= 3 and len(set(lastmods)) == 1:
        return Finding("warn", [f"all {len(entries)} URLs share lastmod {lastmods[0]}"], [where],
                       "Every URL has the same timestamp -- it is the build time, not a change date. "
                       "Crawlers learn to ignore lastmod that is not trustworthy.", basis)
    return Finding("pass", [f"{len(lastmods)}/{len(entries)} URLs with lastmod, {len(days)} distinct dates"],
                   [where], basis=basis)


def img_alt_findings(p: Project, rels):
    """JSX/HTML <img>/<Image> tags with no alt attribute, from source."""
    tag_rx = re.compile(r"<(img|Image)\b((?:[^<>{}]|\{(?:[^{}]|\{[^{}]*\})*\})*?)/?>", re.S)
    missing, total, spread = [], 0, 0
    for rel in rels:
        text = p.read(rel)
        for m in tag_rx.finditer(text):
            total += 1
            attrs = m.group(2)
            if re.search(r"\balt\s*=", attrs):
                continue
            if "{..." in attrs:
                spread += 1
                continue
            missing.append(f"{rel}:{line_of(text, m.start())}")
    return missing, total, spread


def next_app_analysis(p: Project, F):
    app = p.app_dir()
    ext = r"(tsx|jsx|ts|js)"
    root_layout = p.first(*[f"{app}/layout.{e}" for e in ("tsx", "jsx", "ts", "js")])
    if not root_layout:
        group_roots = [f for f in p.find(rf"^{re.escape(app)}/\([^/]+\)/layout\.{ext}$") if "<html" in p.read(f)]
        root_layout = group_roots[0] if group_roots else None
    surfaces = []

    def meta_obj(rel):
        """(kind, keys) for a file's metadata export: static | dynamic | None."""
        text = p.read(rel)
        m = re.search(r"export\s+const\s+metadata\b[^=]*=\s*", text)
        if m:
            start = m.end()
            if start < len(text) and text[start] == "{":
                obj = js_object_at(text, start) or "{}"
                return "static", top_level_keys(obj), line_of(text, m.start())
            return "dynamic", {}, line_of(text, m.start())
        m = re.search(r"export\s+(?:async\s+)?function\s+generateMetadata|export\s+const\s+generateMetadata\s*=", text)
        if m:
            body_start = text.find("{", m.end())
            body = js_object_at(text, body_start) or ""
            keys = {k: "?" for k in ("title", "description", "alternates", "openGraph", "twitter", "robots")
                    if re.search(rf"\b{k}\s*:", body)}
            if re.search(r"\.\.\.\s*\w", body):
                keys["..."] = "?"
            return "dynamic", keys, line_of(text, m.start())
        return None, {}, None

    rk, rkeys, rline = meta_obj(root_layout) if root_layout else (None, {}, None)
    rl = f"{root_layout}:{rline}" if rline else root_layout
    dynamic_root = rk == "dynamic" or "..." in rkeys
    where_root = [root_layout] if root_layout else [f"{app}/layout.tsx"]

    def rootkey(k):
        return k in rkeys

    # base URL
    if rootkey("metadataBase"):
        val = rkeys["metadataBase"]
        m = re.search(r"""['"`](https?://[^'"`]+)""", val)
        if m and not good_site_url(m.group(1)):
            F["base-url"] = Finding("fail", [f"{rl}: metadataBase is {m.group(1)}"], where_root,
                                    "A placeholder base URL makes every canonical and og:image point elsewhere.")
        else:
            F["base-url"] = Finding("pass", [f"{rl}: metadataBase = {trunc(val, 60)}"], where_root)
    elif dynamic_root:
        F["base-url"] = Finding("unknown", [f"{rl}: metadata is computed -- check rendered output"], where_root)
    else:
        F["base-url"] = Finding("fail", [f"{rl or where_root[0]}: no metadataBase"], where_root,
                                "Without metadataBase, Next.js resolves og:image and canonical URLs "
                                "against localhost.")

    # head defaults in the root layout
    for key, cid, label in (("openGraph", "og-tags", "openGraph"), ("twitter", "twitter-card", "twitter")):
        if rootkey(key):
            F[cid] = Finding("pass", [f"{rl}: {label} defaults set"], where_root)
        elif not dynamic_root:
            F[cid] = Finding("fail", [f"{rl or where_root[0]}: no {label} in root metadata"], where_root)
    title_val = rkeys.get("title")
    if title_val:
        sub = top_level_keys(title_val) if title_val.startswith("{") else {}
        lit = literal(sub.get("default")) if sub else literal(title_val)
        if lit is not None and lit.strip().lower() in DEFAULT_TITLES:
            F["title"] = Finding("fail", [f"{rl}: default title {lit!r} left from the starter"], where_root)
        elif lit is not None and not 15 <= len(lit) <= 65:
            F["title"] = Finding("warn", [f"{rl}: default title {lit!r} ({len(lit)} chars)"], where_root)
        else:
            F["title"] = Finding("pass", [f"{rl}: title {trunc(title_val, 60)}"], where_root)
    elif not dynamic_root:
        F["title"] = Finding("fail", [f"{rl or where_root[0]}: no title in root metadata"], where_root)
    desc_val = literal(rkeys.get("description"))
    if desc_val is not None and ("generated by create next app" in desc_val.lower() or not desc_val.strip()):
        F["description"] = Finding("fail", [f"{rl}: starter description {desc_val!r}"], where_root)
    elif desc_val is not None and not 70 <= len(desc_val) <= 165:
        F["description"] = Finding("warn", [f"{rl}: description is {len(desc_val)} chars"], where_root)
    elif rootkey("description"):
        F["description"] = Finding("pass", [f"{rl}: description set"], where_root)
    elif not dynamic_root:
        F["description"] = Finding("fail", [f"{rl or where_root[0]}: no description in root metadata"], where_root)
    if root_layout:
        m = re.search(r"<html[^>]*\blang=", p.read(root_layout))
        F["html-lang"] = Finding("pass" if m else "fail",
                                 [f"{root_layout}: <html lang> {'set' if m else 'missing'}"], where_root)
    F["viewport"] = Finding("pass", ["Next.js emits a viewport meta by default"], where_root)
    robots_val = rkeys.get("robots", "")
    if re.search(r"index\s*:\s*false|noindex", robots_val):
        F["noindex-sitewide"] = Finding("fail", [f"{rl}: robots {trunc(robots_val, 60)}"], where_root,
                                        "Root metadata noindexes every page that does not override it.")
    elif not dynamic_root:
        F["noindex-sitewide"] = Finding("pass", ["no noindex in root metadata"], where_root)

    # file conventions
    conv = lambda name, exts="tsx|jsx|ts|js": p.find(rf"^{re.escape(app)}/(\([^/]+\)/)?{name}\.({exts})$")
    icon = conv("(favicon|icon|apple-icon)", "ico|png|svg|jpg|jpeg|tsx|jsx|ts|js") or \
        [f for f in (p.pub("favicon.ico"), p.pub("favicon.svg")) if f]
    F["favicon"] = Finding("pass" if icon or rootkey("icons") else "fail",
                           [", ".join(icon) or ("icons in root metadata" if rootkey("icons") else "no icon file")],
                           icon or [f"{app}/icon.png"])
    ogimg = conv("opengraph-image", "tsx|jsx|ts|js|png|jpg|jpeg")
    og_val = rkeys.get("openGraph", "")
    if ogimg or "images" in og_val:
        F["og-image"] = Finding("pass", [", ".join(ogimg) or f"{rl}: openGraph.images set"], ogimg or where_root)
    elif not dynamic_root:
        F["og-image"] = Finding("fail", ["no opengraph-image file and no openGraph.images"],
                                [f"{app}/opengraph-image.tsx"])
    not_found = conv("not-found")
    F["not-found"] = Finding("pass", [", ".join(not_found) or "Next.js serves its built-in 404 with status 404"],
                             not_found or [f"{app}/not-found.tsx"])
    robots_file = conv("robots", "ts|js") or ([p.pub("robots.txt")] if p.pub("robots.txt") else [])
    sitemap_file = conv("sitemap", "ts|js|xml") or p.find(rf"^{re.escape(app)}/sitemap\.xml/route\.") or \
        ([p.pub("sitemap.xml")] if p.pub("sitemap.xml") else [])
    if not sitemap_file and (p.dep("next-sitemap") or p.find(r"^next-sitemap\.config\.")):
        sitemap_file = p.find(r"^next-sitemap\.config\.") or ["next-sitemap (package)"]
    llms = [f for f in [p.pub("llms.txt")] if f] + p.find(rf"^{re.escape(app)}/llms\.txt/route\.")
    surfaces += [("Root layout", root_layout or "MISSING"), ("robots", ", ".join(robots_file) or "MISSING"),
                 ("sitemap", ", ".join(sitemap_file) or "MISSING"), ("llms.txt", ", ".join(llms) or "MISSING"),
                 ("OG image", ", ".join(ogimg) or "MISSING"), ("Icon", ", ".join(icon) or "MISSING"),
                 ("404 page", ", ".join(not_found) or "built-in")]
    for sm in sitemap_file:
        if sm.endswith((".ts", ".js")) and re.search(r"lastModified\s*:\s*new Date\(\s*\)", p.read(sm)):
            F["sitemap-lastmod"] = Finding("warn", [f"{sm}: lastModified: new Date() stamps every URL with "
                                                    "the build time"], [sm])
    general_files(p, F, robots_file, sitemap_file, llms, f"{app}/robots.ts", f"{app}/sitemap.ts")

    # per-page metadata coverage
    pages = [f for f in p.find(rf"^{re.escape(app)}/(.*/)?page\.(tsx|jsx|ts|js|mdx|md)$")
             if not re.search(r"/(_[^/]+|api)/", "/" + f)]
    no_title, no_desc, no_canon = [], [], []
    for page in pages:
        chain = [page]
        d = os.path.dirname(page)
        while d and d != app and d.startswith(app):
            chain += [f for f in p.find(rf"^{re.escape(d)}/layout\.{ext}$")]
            d = os.path.dirname(d)
        kinds = [meta_obj(f) for f in chain]
        keys = set()
        for _, k, _ in kinds:
            keys |= set(k)
        route = route_of(app, page)
        if route == "/":
            continue
        if "title" not in keys and "..." not in keys:
            no_title.append(f"{route} ({page})")
        if "description" not in keys and "..." not in keys:
            no_desc.append(f"{route} ({page})")
        if "alternates" not in keys and "..." not in keys:
            no_canon.append(f"{route} ({page})")
    routed = len([pg for pg in pages if route_of(app, pg) != "/"])
    if routed:
        F["title-unique"] = Finding("fail" if no_title else "pass",
                                    no_title[:12] or [f"all {routed} routes set their own title"],
                                    [x.split("(")[-1].rstrip(")") for x in no_title[:12]],
                                    "These routes inherit the root title, so several pages share one title."
                                    if no_title else "")
        F["description-unique"] = Finding("fail" if no_desc else "pass",
                                          no_desc[:12] or [f"all {routed} routes set their own description"],
                                          [x.split("(")[-1].rstrip(")") for x in no_desc[:12]])
    canon = rkeys.get("alternates", "")
    root_canon = literal(top_level_keys(canon).get("canonical")) if canon.startswith("{") else None
    if root_canon is not None and root_canon.startswith("./") and not dynamic_root:
        # './' resolves against each route's own path (verified Next.js 15.5).
        F["canonical"] = Finding("pass", [f"{rl}: alternates.canonical = './' resolves per route"]
                                 + ([] if rootkey("metadataBase") else ["needs metadataBase to be absolute"]),
                                 where_root)
    elif root_canon is not None and routed and no_canon:
        F["canonical"] = Finding("fail", [f"{rl}: alternates.canonical = {root_canon!r} in the ROOT layout is "
                                          f"inherited by {len(no_canon)} route(s) that do not override it"]
                                 + no_canon[:8], where_root + [x.split("(")[-1].rstrip(")") for x in no_canon[:8]],
                                 "Every one of those pages declares the homepage as its canonical -- "
                                 "search engines drop them as duplicates.")
    elif routed and no_canon and not dynamic_root:
        F["canonical"] = Finding("fail" if len(no_canon) == routed else "warn",
                                 [f"{len(no_canon)}/{routed} routes set no canonical"] + no_canon[:8],
                                 [x.split("(")[-1].rstrip(")") for x in no_canon[:8]])
    elif routed and not no_canon:
        F["canonical"] = Finding("pass", [f"all {routed} routes set alternates.canonical"], [])

    # JSON-LD and images across the app
    code = [f for f in p.files if f.endswith((".tsx", ".jsx", ".ts", ".js", ".mdx"))
            and (f.startswith((app + "/", "src/", "components/", "lib/")))]
    jsonld_files(p, F, code, [root_layout or f"{app}/layout.tsx", f"{app}/page.tsx"])
    missing, total, spread = img_alt_findings(p, [f for f in code if f.endswith((".tsx", ".jsx", ".mdx"))])
    if total:
        F["img-alt"] = Finding(frac_status(len(missing), total, 0.1),
                               missing[:12] or [f"{total} image tags, all with alt"],
                               [m.rsplit(":", 1)[0] for m in missing[:12]])
    raw_imgs = []
    for rel in code:
        if rel.endswith((".tsx", ".jsx")):
            text = p.read(rel)
            raw_imgs += [f"{rel}:{line_of(text, m.start())}" for m in re.finditer(r"<img\b", text)]
    F["next-image"] = Finding("warn" if raw_imgs else "pass",
                              raw_imgs[:10] or ["no raw <img> tags in components"],
                              [r.rsplit(":", 1)[0] for r in raw_imgs[:10]],
                              "next/image adds sizing, lazy loading and modern formats; converting needs "
                              "known dimensions or a sized container." if raw_imgs else "")
    fonts_source(p, F, code)
    F["server-rendered"] = Finding("pass", ["App Router pages render on the server by default"], [])
    return surfaces, root_layout


def route_of(app, page):
    rel = os.path.dirname(page)[len(app):]
    segs = [s for s in rel.split("/") if s and not s.startswith("(") and not s.startswith("@")]
    return "/" + "/".join(segs)


def general_files(p, F, robots_file, sitemap_file, llms, robots_target, sitemap_target):
    """robots / sitemap / llms findings shared by every stack."""
    static_robots = [f for f in robots_file if f.endswith(".txt")]
    if static_robots:
        F.update(robots_findings(p.read(static_robots[0]), static_robots[0], "source"))
    elif robots_file:
        F["robots-present"] = Finding("pass", [f"{robots_file[0]} generates /robots.txt"], robots_file)
        text = p.read(robots_file[0])
        if re.search(r"sitemap\s*:\s*['\"`]https?://", text):
            F["robots-sitemap"] = Finding("pass", [f"{robots_file[0]}: sitemap URL set"], robots_file)
    else:
        F["robots-present"] = Finding("fail", ["no robots.txt in source"], [robots_target])
        for cid in ("robots-search-open", "ai-crawlers"):
            F[cid] = Finding("pass", ["no robots.txt: crawling is unrestricted by default"])
        F["robots-syntax"] = Finding("na", ["no robots.txt"])
        F["robots-sitemap"] = Finding("fail", ["no robots.txt to carry a Sitemap: line"], [robots_target])
    if sitemap_file:
        F["sitemap-present"] = Finding("pass", [", ".join(sitemap_file)], sitemap_file)
        xml = [f for f in sitemap_file if f.endswith(".xml")]
        if xml:
            _, entries = probe._parse_sitemap(p.read(xml[0]).encode())
            F["sitemap-lastmod"] = sitemap_lastmod_finding(entries, xml[0], "source")
    else:
        F["sitemap-present"] = Finding("fail", ["no sitemap in source"], [sitemap_target])
        F["sitemap-lastmod"] = Finding("na", ["no sitemap"])
    F["llms-txt"] = Finding("pass" if llms else "fail", [", ".join(llms) or "no llms.txt in source"],
                            llms or [p.pub_path("llms.txt")])


def jsonld_files(p, F, code, home_targets):
    # Structured data is often built in one file and emitted by a shared component
    # (<JsonLd data={...} />), so types are read from every file that declares them.
    ld = [f for f in code if "ld+json" in p.read(f) or ("schema.org" in p.read(f) and "@type" in p.read(f))]
    types = set()
    unescaped = []
    for rel in ld:
        text = p.read(rel)
        types |= set(re.findall(r"""['"]?@type['"]?\s*:\s*['"](\w+)['"]""", text))
        if re.search(r"dangerouslySetInnerHTML|set:html|v-html|\{@html", text) and "JSON.stringify" in text \
                and not re.search(r"u003c|replace\(\s*/</g|serialize|safeJson|htmlEscape|escapeJson", text):
            unescaped.append(rel)
    if ld:
        F["schema-escape"] = Finding("fail" if unescaped else "pass",
                                     [f"{u}: JSON.stringify injected without escaping '<'" for u in unescaped[:6]]
                                     or [f"{len(ld)} JSON-LD file(s), escaping present"], unescaped[:6])
    else:
        F["schema-escape"] = Finding("na", ["no inline JSON-LD in source"])
        F["schema-valid"] = Finding("na", ["no JSON-LD in source"])
    org = {t for t in types if is_org_type(t)}
    if org and "WebSite" in types:
        F["schema-org"] = Finding("pass", [f"@type {', '.join(sorted(org | {'WebSite'}))} in {', '.join(ld[:3])}"], ld[:3])
    elif org or "WebSite" in types:
        F["schema-org"] = Finding("warn", [f"only {', '.join(sorted(org or {'WebSite'}))} in {', '.join(ld[:3])}"], ld[:3])
    else:
        F["schema-org"] = Finding("fail", ["no Organization/WebSite JSON-LD in source"], home_targets)


def fonts_source(p, F, code):
    hits = []
    for rel in code + [f for f in p.files if f.endswith((".html", ".css", ".scss", ".astro", ".vue", ".svelte"))]:
        text = p.read(rel)
        for m in re.finditer(r"fonts\.googleapis\.com/css2?\?[^'\"\s)]*", text):
            if "display=" not in m.group(0):
                hits.append(f"{rel}:{line_of(text, m.start())}")
    if hits:
        F["font-display"] = Finding("warn", hits[:8], [h.rsplit(":", 1)[0] for h in hits[:8]],
                                    "Append &display=swap so text renders while the font loads.")
    elif "font-display" not in F:
        F["font-display"] = Finding("na", ["no Google Fonts stylesheet links"])


def html_head_analysis(p: Project, F, rel, basis_note):
    """Checks that one shell/template HTML file answers for every route (SPA index.html)."""
    parser = parse_html_file(p.read(rel))
    pg = PageData("/", rel, 200, parser, {}, rel)
    R = eval_pages([pg], None, site_level=False)
    for cid, fnd in R.items():
        if cid in ("title-unique", "description-unique", "schema-article", "img-dimensions", "h1", "img-alt"):
            continue
        fnd.basis = "source"
        fnd.where = fnd.where or [rel]
        if basis_note:
            fnd.note = (fnd.note + " " + basis_note).strip()
        F[cid] = fnd
    return parser


def spa_analysis(p: Project, F):
    index = p.first("index.html") if p.stack == "vite" else p.first("public/index.html")
    surfaces = [("HTML shell", index or "MISSING")]
    if index:
        html_head_analysis(p, F, index, "")
        # The shell is the only HTML a crawler without JavaScript ever sees.
    helmet = p.dep("react-helmet-async", "react-helmet", "@unhead/react", "@unhead/vue", "vue-meta", "@vueuse/head")
    prerender = p.dep("vike", "vite-plugin-ssr", "vite-ssg", "vite-react-ssg", "react-snap", "vite-plugin-prerender",
                      "@prerenderer/rollup-plugin", "@prerenderer/webpack-plugin", "prerender-spa-plugin",
                      "vite-plugin-ssg") or any("prerender" in (v or "") or "react-snap" in (v or "")
                                                for v in (p.pkg.get("scripts") or {}).values())
    surfaces.append(("Per-route head manager", helmet or "NONE"))
    surfaces.append(("Prerender / SSR", prerender or "NONE"))
    routes = set()
    for rel in p.find(r"^src/.*\.(tsx|jsx|ts|js|vue|svelte)$"):
        routes |= set(re.findall(r"""path\s*[:=]\s*['"](/[^'"]*)['"]""", p.read(rel)))
    if prerender:
        F["server-rendered"] = Finding("pass", [f"prerendering via {prerender}"], [])
    else:
        F["server-rendered"] = Finding("fail", [f"{index or 'index.html'} is a JavaScript shell; "
                                                f"no prerender or SSR step in package.json"],
                                       [index or "index.html", "package.json"],
                                       "AI crawlers do not run JavaScript: they see only the shell. "
                                       "Prerendering public routes is the fix (react-spa-implementation.md §3).")
    if len(routes) > 1 and not prerender:
        F["title-unique"] = Finding("fail", [f"{len(routes)} client routes ({', '.join(sorted(routes)[:6])}) "
                                             f"all serve the same <title> from {index}"],
                                    [index or "index.html"],
                                    "A head manager fixes this for browsers only; crawlers need prerendering.",
                                    klass="review")
        F["description-unique"] = Finding("fail", [f"{len(routes)} routes share one description"],
                                          [index or "index.html"], "Fixed by the same prerendering step.",
                                          klass="review")
    F["not-found"] = Finding("fail" if not prerender else "unknown",
                             ["SPA hosting rewrites unknown paths to index.html with HTTP 200 (soft 404)"],
                             ["hosting config (vercel.json / netlify _redirects / nginx)"],
                             "Serve a real 404 status for unknown routes.")
    code = p.find(r"^src/.*\.(tsx|jsx|ts|js|vue|svelte|mdx)$")
    general_files(p, F, [f for f in [p.pub("robots.txt")] if f], [f for f in [p.pub("sitemap.xml")] if f],
                  [f for f in [p.pub("llms.txt")] if f], p.pub_path("robots.txt"), p.pub_path("sitemap.xml"))
    jsonld_files(p, F, code + ([index] if index else []), [index or "index.html"])
    F["base-url"] = Finding("na", ["an SPA has no framework base-URL setting; canonical and og:url carry it"])
    missing, total, _ = img_alt_findings(p, [f for f in code if f.endswith((".tsx", ".jsx", ".vue", ".svelte"))])
    if total:
        F["img-alt"] = Finding(frac_status(len(missing), total, 0.1), missing[:12] or [f"{total} images, all with alt"],
                               [m.rsplit(":", 1)[0] for m in missing[:12]])
    fonts_source(p, F, code + ([index] if index else []))
    return surfaces


# Signals searched for in template/layout files of stacks without a dedicated analyser.
TEMPLATE_SIGNALS = {
    "title": r"<title|useSeoMeta\(|useHead\(|<svelte:head|\{%-?\s*seo|page_title|title-tag|<Title\b|<Seo\b|<SEO\b",
    "description": r"""name=["']description|description\s*:|useSeoMeta\(|\{%-?\s*seo|page_description|<Seo\b|<SEO\b""",
    "canonical": r"""rel=["']canonical|canonical_url|\{%-?\s*seo|canonical\s*:|<Seo\b|<SEO\b|\.Permalink""",
    "og-tags": r"""property=["']og:|ogTitle|og:title|opengraph|\{%-?\s*seo|_internal/opengraph""",
    "twitter-card": r"""twitter:card|twitterCard|\{%-?\s*seo|_internal/twitter_cards""",
    "html-lang": r"""<html[^>]*\blang=|language_attributes|request\.locale""",
    "viewport": r"""name=["']viewport""",
    "favicon": r"""rel=["'](?:shortcut )?icon|favicon""",
}


def template_analysis(p: Project, F):
    s = p.stack
    globs = {
        "astro": r"^src/(layouts|components)/.*\.astro$",
        "nuxt": r"^(app/)?(app\.vue|layouts/.*\.vue|nuxt\.config\.(ts|js|mjs))$|^nuxt\.config\.",
        "sveltekit": r"^src/app\.html$|^src/routes/\+layout\.svelte$|^src/lib/.*(seo|head|meta).*\.svelte$",
        "gatsby": r"^gatsby-(config|ssr|browser)\.|^src/components/.*(seo|head|meta|layout).*\.(js|jsx|tsx)$",
        "remix": r"^app/root\.(tsx|jsx)$",
        "docusaurus": r"^docusaurus\.config\.",
        "eleventy": r"^(src/)?_includes/.*\.(njk|liquid|html|hbs|11ty\.js)$",
        "hugo": r"^(themes/[^/]+/)?layouts/(_default/baseof|partials/.*(head|seo|meta).*)\.html$",
        "jekyll": r"^_(includes|layouts)/.*\.html$",
        "wordpress-theme": r"^(header|functions)\.php$",
        "wordpress": r"^wp-content/themes/[^/]+/(header|functions)\.php$",
        "shopify-theme": r"^layout/theme\.liquid$|^snippets/.*(meta|seo|social).*\.liquid$",
        "nextjs-pages": r"^(src/)?pages/_(app|document)\.(tsx|jsx|js|ts)$|^(src/)?components/.*(seo|head|meta).*\.(tsx|jsx)$",
        "unknown": r"^$",
    }
    files = p.find(globs.get(s, r"^$"))
    blob = {f: p.read(f) for f in files}
    surfaces = [("Head templates", ", ".join(files[:6]) or "NONE FOUND")]
    for cid, rx in TEMPLATE_SIGNALS.items():
        hits = [f"{f}:{line_of(t, m.start())}" for f, t in blob.items() for m in [re.search(rx, t)] if m]
        if hits:
            F[cid] = Finding("pass", hits[:3], [h.rsplit(":", 1)[0] for h in hits[:3]],
                             "source heuristic -- confirm in rendered output")
        elif files:
            F[cid] = Finding("fail", [f"no {cid} signal in {', '.join(files[:4])}"], files[:3],
                             "source heuristic -- confirm in rendered output")
    if s == "jekyll" and any("{% seo" in t or "{%- seo" in t for t in blob.values()):
        for cid in ("title", "description", "canonical", "og-tags", "twitter-card"):
            F[cid] = Finding("pass", ["jekyll-seo-tag `{% seo %}` emits it"], files[:2])
        F["schema-org"] = Finding("warn", ["jekyll-seo-tag emits WebSite/WebPage JSON-LD; Organization needs "
                                           "`social`/`logo` in _config.yml"], ["_config.yml"])

    # base URL and rendering per stack
    cfg_keys = {
        "astro": (r"^astro\.config\.", r"""\bsite\s*:\s*['"]https?://"""),
        "nuxt": (r"^nuxt\.config\.", r"""(site\s*:\s*\{[^}]*url|siteUrl|NUXT_PUBLIC_SITE_URL)"""),
        "gatsby": (r"^gatsby-config\.", r"siteUrl\s*:"),
        "docusaurus": (r"^docusaurus\.config\.", r"""\burl\s*:\s*['"]https?://"""),
        "hugo": (r"^(hugo|config)\.(toml|yaml|yml|json)$", r"(?im)^\s*\"?baseurl\"?\s*[:=]\s*['\"]?https?://"),
        "jekyll": (r"^_config\.yml$", r"(?m)^url\s*:\s*['\"]?https?://"),
    }
    if s in cfg_keys:
        frx, vrx = cfg_keys[s]
        cfg = p.find(frx)
        ok = [f for f in cfg if re.search(vrx, p.read(f))]
        F["base-url"] = Finding("pass" if ok else "fail",
                                [f"{ok[0]}: base URL set" if ok else f"no production URL in {', '.join(cfg) or 'config'}"],
                                cfg[:1] or [frx])
    else:
        F["base-url"] = Finding("na", [f"{p.label} has no single base-URL setting"])
    if s == "nuxt" and any(re.search(r"\bssr\s*:\s*false", p.read(f)) for f in p.find(r"^nuxt\.config\.")):
        F["server-rendered"] = Finding("fail", ["nuxt.config: ssr: false -- the site is a client-only SPA"],
                                       p.find(r"^nuxt\.config\."))
    elif s == "sveltekit" and any(re.search(r"export\s+const\s+ssr\s*=\s*false", p.read(f))
                                  for f in p.find(r"^src/routes/\+layout\.(ts|js)$")):
        F["server-rendered"] = Finding("fail", ["src/routes/+layout: export const ssr = false"],
                                       p.find(r"^src/routes/\+layout\.(ts|js)$"))
    elif s not in ("unknown",):
        F["server-rendered"] = Finding("pass", [f"{p.label} renders HTML on the server or at build time"], [])

    # robots / sitemap / llms
    robots = [f for f in [p.pub("robots.txt")] if f] + p.find(r"^src/pages/robots\.txt\.|^src/routes/robots\.txt/"
                                                               r"|^layout/robots\.txt|^templates/robots\.txt\.liquid$"
                                                               r"|^layouts/robots\.txt$|^robots\.txt$")
    sitemap = [f for f in [p.pub("sitemap.xml")] if f] + p.find(r"^src/pages/sitemap.*\.(xml\.)?(ts|js)$"
                                                                r"|^src/routes/sitemap\.xml/")
    plug = p.dep("@astrojs/sitemap", "@nuxtjs/sitemap", "nuxt-simple-sitemap", "gatsby-plugin-sitemap",
                 "@docusaurus/plugin-sitemap", "@11ty/eleventy-plugin-sitemap", "svelte-sitemap")
    if plug:
        sitemap.append(f"{plug} (package)")
    if s == "hugo" and "disablekinds" not in "".join(p.read(f).lower() for f in p.find(r"^(hugo|config)\.")):
        sitemap.append("Hugo built-in sitemap")
    if s == "hugo" and any(re.search(r"(?i)enableRobotsTXT\s*[:=]\s*true", p.read(f)) for f in p.find(r"^(hugo|config)\.")):
        robots.append("Hugo enableRobotsTXT")
    if s == "jekyll" and "jekyll-sitemap" in "".join(p.read(f) for f in ("_config.yml", "Gemfile")):
        sitemap.append("jekyll-sitemap plugin")
    if s == "docusaurus":
        sitemap.append("Docusaurus preset sitemap")
    if s == "shopify-theme":
        robots.append("Shopify default robots.txt")
        sitemap.append("Shopify built-in /sitemap.xml")
    if s in ("wordpress", "wordpress-theme"):
        robots.append("WordPress virtual robots.txt")
        sitemap.append("WordPress core /wp-sitemap.xml (5.5+)")
    llms = [f for f in [p.pub("llms.txt")] if f] + p.find(r"^src/pages/llms\.txt\.|^src/routes/llms\.txt/")
    general_files(p, F, robots, sitemap, llms, p.pub_path("robots.txt"), p.pub_path("sitemap.xml"))
    if s in ("astro", "gatsby", "sveltekit", "nuxt", "docusaurus", "eleventy", "hugo", "jekyll"):
        nf = p.find(r"^src/pages/404\.|^src/routes/\+error\.svelte$|^(app/)?error\.vue$|^404\.(html|md)$"
                    r"|^layouts/404\.html$|^content/404\.md$|^src/404\.")
        F["not-found"] = Finding("pass" if nf else "fail", [", ".join(nf) or "no 404 page in source"],
                                 nf or ["404 page"])
    code = [f for f in p.files if f.endswith((".astro", ".vue", ".svelte", ".tsx", ".jsx", ".njk", ".liquid",
                                              ".html", ".php", ".mdx"))]
    jsonld_files(p, F, code, files[:1] or ["homepage template"])
    missing, total, _ = img_alt_findings(p, code)
    if total:
        F["img-alt"] = Finding(frac_status(len(missing), total, 0.1), missing[:12] or [f"{total} images, all with alt"],
                               [m.rsplit(":", 1)[0] for m in missing[:12]])
    fonts_source(p, F, code)
    return surfaces


def file_routes(p: Project):
    """URL path pattern -> source file, for file-based routers."""
    table = []
    specs = {
        "nextjs-app": (p.app_dir() or "app", r"(.*/)?page\.(tsx|jsx|ts|js|mdx|md)$"),
        "nextjs-pages": ("src/pages" if p.find(r"^src/pages/") else "pages", r"(?!_|api/).*\.(tsx|jsx|ts|js|mdx|md)$"),
        "astro": ("src/pages", r".*\.(astro|md|mdx|html)$"),
        "sveltekit": ("src/routes", r"(.*/)?\+page\.svelte$"),
        "nuxt": ("app/pages" if p.find(r"^app/pages/") else "pages", r".*\.vue$"),
        "gatsby": ("src/pages", r".*\.(tsx|jsx|js|ts)$"),
    }
    if p.stack not in specs:
        return table
    base, rx = specs[p.stack]
    for f in p.find(rf"^{re.escape(base)}/{rx}"):
        rel = f[len(base) + 1:]
        rel = re.sub(r"(^|/)(page|\+page)\.[a-z]+$", "", rel)
        rel = re.sub(r"\.[a-z]+$", "", rel)
        rel = re.sub(r"(^|/)index$", "", rel)
        segs = [x for x in rel.split("/") if x and not x.startswith("(") and not x.startswith("@")]
        if any(x.startswith("_") for x in segs):
            continue
        pat = "/" + "/".join(segs)
        parts = []
        for seg in segs:
            if re.match(r"^\[\[?\.\.\..*\]\]?$", seg):
                parts.append(".*")              # catch-all [...slug] / [[...slug]]
            elif re.match(r"^\[.*\]$", seg):
                parts.append("[^/]+")           # dynamic [slug]
            else:
                parts.append(re.escape(seg))
        rx_path = "^/" + "/".join(parts) + "$" if parts else "^/$"
        table.append((pat, re.compile(rx_path), f))
    table.sort(key=lambda t: (t[0].count("["), -len(t[0])))
    return table


def map_where(where, routes):
    """Rewrite rendered page refs (URL paths or build-output files) to 'ref (source file)'."""
    if not routes:
        return where
    out = []
    for w in where:
        path = w
        if not w.startswith("/"):
            if not w.endswith((".html", ".htm")):
                out.append(w)
                continue
            path = "/" + re.sub(r"(^|/)index\.html?$", "", w)
            path = re.sub(r"\.html?$", "", path)
        np = norm_path(path)
        hit = next((f for pat, rx, f in routes if rx.match(np)), None)
        out.append(f"{w} ({hit})" if hit else w)
    return out


def source_findings(p: Project):
    F = {}
    if p.stack == "nextjs-app":
        surfaces, _ = next_app_analysis(p, F)
    elif p.stack in ("vite", "cra"):
        surfaces = spa_analysis(p, F)
    elif p.stack == "static":
        surfaces = [("Pages", "HTML files in the repo are the rendered output")]
        F["base-url"] = Finding("na", ["static HTML has no base-URL setting; canonical and og:url carry it"])
        F["schema-escape"] = Finding("na", ["JSON-LD is literal HTML, not injected by script"])
        F["server-rendered"] = Finding("pass", ["static HTML: every word is in the served file"])
    else:
        surfaces = template_analysis(p, F)
    return F, surfaces


# --------------------------------------------------------------------------
# Rendered evidence
# --------------------------------------------------------------------------


class PageData:
    def __init__(self, url, path, status, parser, headers, file=None):
        self.url, self.path, self.status = url, path, status
        self.parser, self.headers, self.file = parser, headers, file
        robots = (parser.meta("robots") or "") + " " + (headers.get("x-robots-tag") or "")
        self.noindex = "noindex" in robots.lower()
        self.refresh = parser.meta("refresh") is not None

    @property
    def ref(self):
        return self.file or self.path


class Rendered:
    def __init__(self, basis):
        self.basis = basis            # "html:<dir>" | "url:<origin>"
        self.pages = []
        self.robots = None            # (text, where) | None ; False = checked, absent
        self.sitemap = None           # (entries, where) | False
        self.llms = None              # where | False
        self.not_found = None         # (status, detail)
        self.favicon = False


def html_dir_evidence(root, limit=500):
    root = os.path.abspath(root)
    r = Rendered(f"html:{root}")
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and d not in ("_next", "assets", "_astro"))
        for f in sorted(filenames):
            if f.lower().endswith((".html", ".htm")):
                files.append(os.path.join(dirpath, f))
    files.sort(key=lambda f: (f.count(os.sep), f))
    for f in files[:limit]:
        rel = os.path.relpath(f, root).replace(os.sep, "/")
        name = os.path.basename(rel).lower()
        if name in ("404.html", "404.htm"):
            r.not_found = (404, f"{rel} exists (hosts that honour it serve it with status 404)")
            continue
        if name in ("200.html",) or re.match(r"^google[0-9a-f]+\.html$", name) or name.startswith("yandex_"):
            continue
        with open(f, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        path = "/" + rel
        path = re.sub(r"(^|/)index\.html?$", r"\1", path)
        path = re.sub(r"\.html?$", "", path) or "/"
        r.pages.append(PageData(path, path, 200, parse_html_file(text), {}, rel))
    if r.not_found is None:
        r.not_found = (None, "no 404.html in the output -- the host decides what unknown URLs return")
    robots = os.path.join(root, "robots.txt")
    if os.path.isfile(robots):
        with open(robots, encoding="utf-8", errors="replace") as fh:
            r.robots = (fh.read(), "robots.txt")
    else:
        r.robots = False
    maps = [f for f in os.listdir(root) if re.match(r"^sitemap.*\.xml$", f)]
    if maps:
        entries = []
        for m in sorted(maps):
            with open(os.path.join(root, m), "rb") as fh:
                kind, ents = probe._parse_sitemap(fh.read())
            if kind == "urlset":
                entries += ents
        r.sitemap = (entries, ", ".join(sorted(maps)))
    else:
        r.sitemap = False
    r.llms = "llms.txt" if os.path.isfile(os.path.join(root, "llms.txt")) else False
    r.favicon = any(os.path.isfile(os.path.join(root, n)) for n in ("favicon.ico", "favicon.svg", "favicon.png"))
    return r


def url_evidence(target, n=15, timeout=20, seeds=()):
    """Crawl a running site breadth-first from the homepage, the sitemap and any seed
    paths (a project's own routes), staying on one origin."""
    parts = urllib.parse.urlsplit(target if is_url(target) else "https://" + target)
    origin = f"{parts.scheme}://{parts.netloc}"
    r = Rendered(f"url:{origin}")
    home = probe.fetch(origin + "/", timeout=timeout)
    if home.error_kind == "policy":
        return r, 3, home.error
    if home.error_kind == "network" or (home.error and not home.status):
        return r, 5, home.error
    if home.error_kind == "site" or home.status in (403, 429):
        return r, 4, f"HTTP {home.status} -- the site refuses automated clients"

    def page_of(res, url):
        parser = parse_html_file(res.text)
        path = urllib.parse.urlsplit(res.final_url or url).path or "/"
        return PageData(res.final_url or url, path, res.status, parser, res.headers)

    r.pages.append(page_of(home, origin + "/"))
    queue, seen = [], {"/"}

    def enqueue(u):
        s = urllib.parse.urlsplit(urllib.parse.urljoin(origin + "/", u))
        if s.scheme not in ("http", "https") or not s.path:
            return
        if s.netloc and s.netloc != parts.netloc and not _same_site(s.netloc, parts.netloc, r):
            return
        path = s.path
        if re.search(r"\.(png|jpe?g|gif|svg|webp|pdf|zip|xml|txt|css|js|ico|mp4|webm|json)$", path, re.I):
            return
        if path not in seen:
            seen.add(path)
            queue.append(path + (("?" + s.query) if s.query and len(s.query) < 40 else ""))

    rb = probe.fetch(origin + "/robots.txt", timeout=timeout)
    if rb.ok and rb.status == 200 and b"<html" not in rb.body[:400].lower():
        r.robots = (rb.text, f"{origin}/robots.txt")
    else:
        r.robots = False
    sm_url = origin + "/sitemap.xml"
    if r.robots:
        _, sms, _ = probe.parse_robots(r.robots[0])
        if sms:
            s = urllib.parse.urlsplit(sms[0][0])
            sm_url = origin + s.path  # the sitemap may name production; fetch it from this origin
    entries, errors = _sitemap_from(sm_url, origin, timeout)
    if entries:
        r.sitemap = (entries, sm_url)
        r.site_hosts = {urllib.parse.urlsplit(u).netloc for u, _ in entries}
    else:
        r.sitemap = False
    for path in seeds:
        enqueue(path)
    for u, _ in entries:
        enqueue(urllib.parse.urlsplit(u).path or "/")
    for a in r.pages[0].parser.anchors:
        enqueue(a["href"])
    i = 0
    while i < len(queue) and len(r.pages) < n:
        path = queue[i]
        i += 1
        res = probe.fetch(origin + path, timeout=timeout)
        if res.error or not res.status:
            continue
        ctype = res.headers.get("content-type", "")
        if "html" not in ctype and not res.body.lstrip()[:15].lower().startswith((b"<!doctype", b"<html")):
            continue
        pg = page_of(res, origin + path)
        r.pages.append(pg)
        for a in pg.parser.anchors:
            enqueue(a["href"])
    ll = probe.fetch(origin + "/llms.txt", timeout=timeout)
    r.llms = f"{origin}/llms.txt" if ll.ok and ll.status == 200 and b"<html" not in ll.body[:500].lower() else False
    nf = probe.fetch(f"{origin}/seo-scan-missing-{int(time.time())}", timeout=timeout)
    r.not_found = (nf.status, f"GET /seo-scan-missing-* returned HTTP {nf.status}")
    fav = probe.fetch(origin + "/favicon.ico", timeout=timeout)
    r.favicon = bool(fav.ok and fav.status == 200 and fav.body)
    return r, 0, None


class LocalServer:
    """Start a site's own server for the length of one scan, and always stop it.

    Background servers started from separate tool calls outlive the call that knew
    their PID; this keeps start, scan and stop inside one process."""

    def __init__(self, cmd, url, cwd, timeout=150):
        self.cmd, self.url, self.cwd, self.timeout = cmd, url, cwd, timeout
        self.proc = None
        self.log = os.path.join(tempfile.gettempdir(), f"seo-scan-serve-{os.getpid()}.log")

    def __enter__(self):
        busy = probe.fetch(self.url, timeout=3)
        if busy.status:
            raise RuntimeError(f"{self.url} already answers (HTTP {busy.status}) before the server started -- "
                               "another process holds that port, and scanning it would measure the wrong build. "
                               "Stop it or pick another port.")
        kwargs = {"start_new_session": True} if os.name == "posix" else \
            {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
        with open(self.log, "wb") as log:
            self.proc = subprocess.Popen(self.cmd, shell=True, cwd=self.cwd, stdout=log,
                                         stderr=subprocess.STDOUT, **kwargs)
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"`{self.cmd}` exited with code {self.proc.returncode} before answering.\n"
                                   + self.tail())
            if probe.fetch(self.url, timeout=3).status:
                return self
            time.sleep(1)
        self.stop()
        raise RuntimeError(f"`{self.cmd}` did not answer at {self.url} within {self.timeout}s.\n" + self.tail())

    def tail(self, n=25):
        try:
            with open(self.log, encoding="utf-8", errors="replace") as fh:
                return "--- server log (tail) ---\n" + "".join(fh.readlines()[-n:])
        except OSError:
            return ""

    def stop(self):
        if not self.proc or self.proc.poll() is not None:
            return
        try:
            if os.name == "posix":
                os.killpg(self.proc.pid, signal.SIGTERM)
            else:
                self.proc.terminate()
            self.proc.wait(timeout=10)
        except Exception:  # noqa: BLE001
            try:
                if os.name == "posix":
                    os.killpg(self.proc.pid, signal.SIGKILL)
                else:
                    self.proc.kill()
            except Exception:  # noqa: BLE001
                pass

    def __exit__(self, *exc):
        self.stop()
        return False


def _same_site(netloc, origin_netloc, r):
    # Sitemaps and links on a local build usually name the production host.
    hosts = getattr(r, "site_hosts", set())
    return netloc in hosts or netloc.replace("www.", "") == origin_netloc.replace("www.", "")


def _sitemap_from(url, origin, timeout):
    class A:
        pass
    args = A()
    args.ua_string, args.timeout = probe.DEFAULT_UA, timeout
    # Child sitemaps also name production; rewrite them onto the origin being crawled.
    entries, errors, seen, todo = [], [], set(), [url]
    while todo and len(seen) < 12:
        u = todo.pop(0)
        if u in seen:
            continue
        seen.add(u)
        res = probe.fetch(u, timeout=timeout)
        if res.error or res.status != 200:
            errors.append((u, res.error or f"HTTP {res.status}"))
            continue
        kind, ents = probe._parse_sitemap(res.body)
        if kind == "urlset":
            entries += ents
        else:
            todo += [origin + urllib.parse.urlsplit(c).path for c, _ in ents[:10]]
    return entries, errors


# --------------------------------------------------------------------------
# Page-level evaluation (rendered)
# --------------------------------------------------------------------------


def eval_pages(pages, rendered, site_level=True):
    F = {}
    live = [pg for pg in pages if pg.status == 200 and not pg.refresh]
    indexable = [pg for pg in live if not pg.noindex]
    home = next((pg for pg in live if norm_path(pg.path) == "/"), live[0] if live else None)
    basis = "rendered"
    if not live:
        return F
    n = len(indexable) or 1

    # noindex
    if home and home.noindex:
        F["noindex-sitewide"] = Finding("fail", [f"homepage {home.ref} is noindex"], [home.ref], basis=basis)
    elif len(live) > 1 and len(live) - len(indexable) > len(live) / 2:
        F["noindex-sitewide"] = Finding("fail", [f"{len(live) - len(indexable)}/{len(live)} pages are noindex"],
                                        [pg.ref for pg in live if pg.noindex][:8], basis=basis)
    else:
        extra = [pg.ref for pg in live if pg.noindex]
        F["noindex-sitewide"] = Finding("pass", [f"noindex only on: {', '.join(extra[:6])}" if extra
                                                 else "no page is noindex"], basis=basis)
    pages = indexable or live

    def per_page(cid, bad, fmt, warn_at=0.25, fail_any=False, note="", pool=None):
        pool = pages if pool is None else pool
        status = ("fail" if bad else "pass") if fail_any else frac_status(len(bad), len(pool), warn_at)
        F[cid] = Finding(status, [fmt(pg) for pg in bad[:10]] or [f"all {len(pool)} page(s) OK"],
                         [pg.ref for pg in bad[:10]], note, basis)

    # titles
    missing = [pg for pg in pages if not pg.parser.title]
    badlen = [pg for pg in pages if pg.parser.title and not 15 <= len(pg.parser.title) <= 65]
    default = [pg for pg in pages if pg.parser.title.strip().lower() in DEFAULT_TITLES]
    if missing or default:
        F["title"] = Finding("fail", [f"{pg.ref}: MISSING" for pg in missing[:6]] +
                             [f"{pg.ref}: starter title {pg.parser.title!r}" for pg in default[:6]],
                             [pg.ref for pg in (missing + default)[:10]], basis=basis)
    elif badlen:
        F["title"] = Finding("warn", [f"{pg.ref}: {len(pg.parser.title)} chars {trunc(pg.parser.title, 60)!r}"
                                      for pg in badlen[:10]], [pg.ref for pg in badlen[:10]], basis=basis)
    else:
        F["title"] = Finding("pass", [f"all {len(pages)} page(s) have a 15-65 char title"], basis=basis)
    for cid, getter in (("title-unique", lambda pg: pg.parser.title),
                        ("description-unique", lambda pg: pg.parser.meta("description"))):
        groups = {}
        for pg in pages:
            v = (getter(pg) or "").strip()
            if v:
                groups.setdefault(v, []).append(pg)
        dups = [(v, g) for v, g in groups.items() if len(g) > 1]
        if len(pages) < 2:
            F[cid] = Finding("unknown", ["only one page reached -- uniqueness needs two or more"], basis=basis)
            continue
        dup_pages = sum(len(g) for _, g in dups)
        F[cid] = Finding(frac_status(dup_pages, len(pages), 0.2),
                         [f"{len(g)} pages share {trunc(v, 50)!r}: {', '.join(pg.ref for pg in g[:4])}"
                          for v, g in dups[:6]] or [f"{len(pages)} distinct values"],
                         [pg.ref for _, g in dups[:6] for pg in g[:4]], basis=basis)
    # descriptions
    missing = [pg for pg in pages if not (pg.parser.meta("description") or "").strip()]
    badlen = [pg for pg in pages if pg.parser.meta("description") and not 70 <= len(pg.parser.meta("description")) <= 165]
    starter = [pg for pg in pages if "generated by create next app" in (pg.parser.meta("description") or "").lower()]
    if missing or starter:
        status = "fail" if (home in missing or home in starter or len(missing) / n > 0.25 or starter) else "warn"
        F["description"] = Finding(status, [f"{pg.ref}: MISSING" for pg in missing[:8]] +
                                   [f"{pg.ref}: starter description" for pg in starter[:4]],
                                   [pg.ref for pg in (missing + starter)[:10]], basis=basis)
    elif badlen:
        F["description"] = Finding("warn", [f"{pg.ref}: {len(pg.parser.meta('description'))} chars" for pg in badlen[:10]],
                                   [pg.ref for pg in badlen[:10]], basis=basis)
    else:
        F["description"] = Finding("pass", [f"all {len(pages)} page(s) have a 70-165 char description"], basis=basis)

    # canonical
    missing = [pg for pg in pages if not pg.parser.link_href("canonical")]
    relative = [pg for pg in pages if pg.parser.link_href("canonical") and not is_url(pg.parser.link_href("canonical"))]
    local = [pg for pg in pages if is_url(pg.parser.link_href("canonical") or "")
             and not good_site_url(pg.parser.link_href("canonical"))]
    targets = {}
    for pg in pages:
        c = pg.parser.link_href("canonical")
        if c and norm_path(c) != norm_path(pg.path):
            targets.setdefault(norm_path(c), []).append(pg)
    collapsed = [(t, g) for t, g in targets.items() if len(g) >= 2]
    if collapsed:
        t, g = max(collapsed, key=lambda x: len(x[1]))
        F["canonical"] = Finding("fail", [f"{len(g)} pages declare canonical {t}: {', '.join(pg.ref for pg in g[:6])}"],
                                 [pg.ref for pg in g[:8]],
                                 "Those pages tell search engines they are duplicates of another URL.", basis)
    elif local:
        F["canonical"] = Finding("fail", [f"{pg.ref}: canonical {pg.parser.link_href('canonical')}" for pg in local[:6]],
                                 [pg.ref for pg in local[:6]], "Canonical points at a placeholder or local host.", basis)
    elif missing:
        per_page("canonical", missing, lambda pg: f"{pg.ref}: MISSING")
    elif relative:
        F["canonical"] = Finding("warn", [f"{pg.ref}: relative {pg.parser.link_href('canonical')}" for pg in relative[:6]],
                                 [pg.ref for pg in relative[:6]], "Use absolute URLs.", basis)
    else:
        other = [pg for ts in targets.values() for pg in ts]
        F["canonical"] = Finding("warn" if other else "pass",
                                 [f"{pg.ref} -> {pg.parser.link_href('canonical')}" for pg in other[:6]]
                                 or [f"all {len(pages)} page(s) self-canonical"], [pg.ref for pg in other[:6]], basis=basis)

    per_page("html-lang", [pg for pg in live if not pg.parser.html_lang], lambda pg: f"{pg.ref}: no lang",
             fail_any=True)
    per_page("viewport", [pg for pg in live if not pg.parser.meta("viewport")], lambda pg: f"{pg.ref}: no viewport",
             fail_any=True)
    icon = home and any("icon" in lk["rel"].split() for lk in home.parser.links)
    F["favicon"] = Finding("pass" if icon or (rendered and rendered.favicon) else "fail",
                           ["<link rel=icon> on homepage" if icon else
                            ("/favicon.ico served" if rendered and rendered.favicon else "no icon link, no /favicon.ico")],
                           [] if icon else ([home.ref] if home else []), basis=basis)

    # headings and images -- meaningless on an empty JavaScript shell
    shell_refs = {pg.ref for pg in pages if probe._render_check(pg.parser, None)[0].startswith("CLIENT-RENDERED")}
    content = [pg for pg in pages if pg.ref not in shell_refs]
    if content:
        per_page("h1", [pg for pg in content if sum(1 for h in pg.parser.headings if h[0] == 1) != 1],
                 lambda pg: f"{pg.ref}: {sum(1 for h in pg.parser.headings if h[0] == 1)} H1", pool=content)
    imgs = [(pg, im) for pg in content for im in pg.parser.images]
    no_alt = [(pg, im) for pg, im in imgs if im["alt"] is None]
    if imgs:
        F["img-alt"] = Finding(frac_status(len(no_alt), len(imgs), 0.1),
                               [f"{pg.ref}: {trunc(im['src'], 60)}" for pg, im in no_alt[:10]]
                               or [f"{len(imgs)} images, all with alt"],
                               sorted({pg.ref for pg, _ in no_alt})[:10], basis=basis)
        no_dim = [(pg, im) for pg, im in imgs if not (im["width"] and im["height"]) and not im.get("fill")
                  and "aspect-ratio" not in (im.get("style") or "") and not im["src"].startswith("data:")]
        F["img-dimensions"] = Finding("pass" if not no_dim else ("warn" if len(no_dim) / len(imgs) <= 0.5 else "fail"),
                                      [f"{pg.ref}: {trunc(im['src'], 60)}" for pg, im in no_dim[:10]]
                                      or [f"{len(imgs)} images, all sized"],
                                      sorted({pg.ref for pg, _ in no_dim})[:10],
                                      "Use `seo-scan.py imgsize FILE` for the intrinsic size." if no_dim else "", basis)
    elif content:
        F["img-alt"] = Finding("na", ["no <img> tags in the sample"], basis=basis)
        F["img-dimensions"] = Finding("na", ["no <img> tags in the sample"], basis=basis)
    if not content:
        for cid in ("h1", "img-alt", "img-dimensions"):
            F[cid] = Finding("unknown", ["every page is a client-rendered shell -- the content only exists "
                                         "after JavaScript runs; fix `server-rendered` first"], basis=basis)

    # social
    def og(pg, k):
        return pg.parser.meta(k)
    per_page("og-tags", [pg for pg in pages if not all(og(pg, k) for k in ("og:title", "og:description", "og:type"))],
             lambda pg: f"{pg.ref}: missing " + ", ".join(k for k in ("og:title", "og:description", "og:type")
                                                           if not og(pg, k)))
    if home:
        img = og(home, "og:image")
        bad_host = img and is_url(img) and not good_site_url(img)
        if not img:
            F["og-image"] = Finding("fail", [f"{home.ref}: no og:image"], [home.ref], basis=basis)
        elif not is_url(img) or bad_host:
            F["og-image"] = Finding("fail", [f"{home.ref}: og:image {trunc(img, 70)}"], [home.ref],
                                    "og:image must be an absolute URL on the production host.", basis)
        else:
            others = [pg for pg in pages if not og(pg, "og:image")]
            F["og-image"] = Finding("warn" if others else "pass",
                                    [f"{pg.ref}: no og:image" for pg in others[:6]] or [f"og:image {trunc(img, 70)}"],
                                    [pg.ref for pg in others[:6]], basis=basis)
    per_page("twitter-card", [pg for pg in pages if not og(pg, "twitter:card")], lambda pg: f"{pg.ref}: no twitter:card")

    # structured data
    errors = [(pg, e) for pg in live for e in pg.parser.jsonld()[1]]
    all_types = set()
    for pg in live:
        for types, _ in pg.parser.jsonld()[0]:
            all_types |= set(types)
    if any(pg.parser.jsonld_raw for pg in live):
        F["schema-valid"] = Finding("fail" if errors else "pass",
                                    [f"{pg.ref}: block #{i}: {msg}" for pg, (i, msg) in errors[:8]]
                                    or [f"JSON-LD types found: {', '.join(sorted(all_types)[:10])}"],
                                    [pg.ref for pg, _ in errors[:8]], basis=basis)
    else:
        F["schema-valid"] = Finding("na", ["no JSON-LD blocks to validate"], basis=basis)
    if home:
        ht = set()
        for types, _ in home.parser.jsonld()[0]:
            ht |= set(types)
        org = {t for t in ht if is_org_type(t)}
        broken = home.parser.jsonld()[1]
        if broken and not ht:
            F["schema-org"] = Finding("fail", [f"{home.ref}: homepage JSON-LD does not parse ({broken[0][1]})"],
                                      [home.ref], "Fix `schema-valid` first; the entity may already be there.", basis)
        elif org and "WebSite" in ht:
            F["schema-org"] = Finding("pass", [f"homepage @types: {', '.join(sorted(ht))}"], basis=basis)
        elif org or "WebSite" in ht:
            F["schema-org"] = Finding("warn", [f"homepage has {', '.join(sorted(ht))}; needs both an "
                                               f"Organization-type entity and WebSite"], [home.ref], basis=basis)
        else:
            F["schema-org"] = Finding("fail", [f"homepage @types: {', '.join(sorted(ht)) or 'none'}"], [home.ref],
                                      basis=basis)
    articles = [pg for pg in content if ARTICLE_PATH.match(norm_path(pg.path) + "/")]
    if articles:
        bad = [pg for pg in articles if not ({t for ts, _ in pg.parser.jsonld()[0] for t in ts} & ARTICLE_TYPES)]
        F["schema-article"] = Finding("fail" if bad else "pass",
                                      [f"{pg.ref}: no Article/BlogPosting" for pg in bad[:8]]
                                      or [f"{len(articles)} article page(s) typed"], [pg.ref for pg in bad[:8]],
                                      basis=basis)
    else:
        F["schema-article"] = Finding("na", ["no article-like URLs (/blog/..., /news/...) in the sample"], basis=basis)

    # rendering: only a JavaScript mount point with next to no HTML text is a failure.
    # A short page that is fully in the HTML is thin content, not a rendering problem.
    shells, empty = [], []
    for pg in pages:
        verdict, why = probe._render_check(pg.parser, None)
        if verdict.startswith("CLIENT-RENDERED"):
            shells.append((pg, verdict, why))
        elif verdict.startswith("NEARLY EMPTY") and pg.parser.body_words < 15:
            empty.append((pg, verdict, why))
    status = "fail" if shells else ("warn" if empty else "pass")
    F["server-rendered"] = Finding(status,
                                   [f"{pg.ref}: {v} -- {w}" for pg, v, w in (shells + empty)[:6]]
                                   or [f"all {len(pages)} page(s) carry their text in the HTML"],
                                   [pg.ref for pg, _, _ in (shells + empty)[:6]], basis=basis)
    # fonts
    gf = [pg for pg in live for lk in pg.parser.links
          if "stylesheet" in lk["rel"] and "fonts.googleapis.com" in lk["href"] and "display=" not in lk["href"]]
    if any("fonts.googleapis.com" in lk["href"] for pg in live for lk in pg.parser.links):
        F["font-display"] = Finding("warn" if gf else "pass",
                                    [f"{pg.ref}: Google Fonts link without display=swap" for pg in gf[:4]]
                                    or ["Google Fonts links use display="], [pg.ref for pg in gf[:4]], basis=basis)
    else:
        F["font-display"] = Finding("na", ["no Google Fonts stylesheet links in the rendered pages"], basis=basis)

    if not site_level or rendered is None:
        return F
    # site files
    if rendered.robots:
        F.update(robots_findings(rendered.robots[0], rendered.robots[1], basis))
    elif rendered.robots is False:
        F["robots-present"] = Finding("fail", ["/robots.txt not served"], basis=basis)
        for cid in ("robots-search-open", "ai-crawlers"):
            F[cid] = Finding("pass", ["no robots.txt: crawling is unrestricted by default"], basis=basis)
        F["robots-sitemap"] = Finding("fail", ["no robots.txt to carry a Sitemap: line"], basis=basis)
        F["robots-syntax"] = Finding("na", ["no robots.txt"], basis=basis)
    if rendered.sitemap:
        entries, where = rendered.sitemap
        F["sitemap-present"] = Finding("pass", [f"{where}: {len(entries)} URL(s)"], basis=basis)
        F["sitemap-lastmod"] = sitemap_lastmod_finding(entries, where, basis)
        hosts = {urllib.parse.urlsplit(u).netloc for u, _ in entries}
        bad = [h for h in hosts if not good_site_url("https://" + h)]
        if bad:
            F["sitemap-present"] = Finding("fail", [f"sitemap URLs use host {', '.join(bad)}"], [where],
                                           "Sitemap <loc> values must be production URLs.", basis)
    elif rendered.sitemap is False:
        F["sitemap-present"] = Finding("fail", ["no sitemap.xml served"], basis=basis)
        F["sitemap-lastmod"] = Finding("na", ["no sitemap"], basis=basis)
    F["llms-txt"] = Finding("pass" if rendered.llms else "fail", [rendered.llms or "/llms.txt not served"], basis=basis)
    status, detail = rendered.not_found or (None, "")
    if status in (404, 410):
        F["not-found"] = Finding("pass", [detail], basis=basis)
    elif status is None:
        F["not-found"] = Finding("warn", [detail], basis=basis)
    else:
        F["not-found"] = Finding("fail", [detail + " (soft 404)"], basis=basis,
                                 note="Unknown URLs answering 200 let crawlers index unlimited junk URLs.")
    return F


def content_notes(pages):
    """Content signals worth a human's attention. Reported, never scored."""
    notes = []
    live = [pg for pg in pages if pg.status == 200 and not pg.noindex and not pg.refresh]
    thin = [pg for pg in live if pg.parser.body_words < 250 and norm_path(pg.path) != "/"]
    if thin:
        notes.append(f"{len(thin)} thin page(s) under 250 words: " +
                     ", ".join(f"{pg.ref} ({pg.parser.body_words}w)" for pg in thin[:6]))
    band = []
    for pg in live:
        secs = pg.parser.section_word_counts()
        if len(secs) >= 3 and sum(1 for w in secs if 120 <= w <= 180) / len(secs) < 0.3:
            band.append(pg.ref)
    if band:
        notes.append(f"{len(band)} page(s) with few self-contained 120-180 word sections (AI-extraction band): "
                     + ", ".join(band[:6]))
    no_h2 = [pg.ref for pg in live if pg.parser.body_words > 300 and not any(h[0] == 2 for h in pg.parser.headings)]
    if no_h2:
        notes.append(f"{len(no_h2)} long page(s) with no H2 structure: " + ", ".join(no_h2[:6]))
    return notes


# --------------------------------------------------------------------------
# Scoring and output
# --------------------------------------------------------------------------


def assemble(source, rendered_f, stack):
    out = {}
    for cid in CHECKS:
        r, s = rendered_f.get(cid), source.get(cid)
        if r and (r.status in CREDIT or not (s and s.status in CREDIT)):
            f = r
            if s and s.where and f.status in ("fail", "warn"):
                f.where = list(dict.fromkeys(f.where + s.where))[:10]
        elif s:
            f = s
        else:
            f = Finding("unknown", ["no evidence -- needs rendered output (--html or --url)"])
        if cid == "server-rendered" and r and s and r.status == "warn":
            # A near-empty page with no JS mount point: the source decides whether it is
            # a short server-rendered page (fine) or an SPA with an unusual mount id.
            f = Finding(s.status, r.evidence + s.evidence, s.where or r.where,
                        "Short pages are in the HTML; the stack renders on the server."
                        if s.status == "pass" else s.note, "rendered")
        if cid == "next-image" and not stack.startswith("nextjs"):
            f = Finding("na", ["not a Next.js project"])
        if cid in ("base-url", "schema-escape") and stack == "none":
            f = Finding("na", ["no codebase to inspect -- the platform owns this"])
        out[cid] = f
    return out


def score_of(results, upgrade=()):
    tot = got = 0.0
    per = {c: [0.0, 0.0] for c, _ in CATEGORIES}
    for cid, f in results.items():
        cat, _, w, klass, _ = CHECKS[cid]
        klass = f.klass or klass
        status = f.status
        if status in ("warn", "fail") and klass in upgrade:
            status = "pass"
        if status not in CREDIT:
            continue
        tot += w
        got += w * CREDIT[status]
        per[cat][0] += w * CREDIT[status]
        per[cat][1] += w
    overall = round(10 * got / tot, 1) if tot else None
    cats = {c: (round(10 * g / t, 1) if t else None) for c, (g, t) in per.items()}
    return overall, cats


def default_save_path(key):
    h = hashlib.sha1(key.encode()).hexdigest()[:10]
    return os.path.join(tempfile.gettempdir(), f"seo-scan-{h}.json")


def render_markdown(res):
    L = []
    L.append(f"# SEO/GEO scorecard: {res['target']}")
    L.append(f"_scanned {res['time']} by seo-scan {VERSION} -- stack: {res['stack_label']} -- "
             f"evidence: {res['evidence']}_\n")
    s, reach, full = res["score"], res["score_after_fixable"], res["score_after_review"]
    L.append(f"## Score: {s if s is not None else '-'} / 10")
    L.append(f"- After every **auto** + **input** fix: **{reach} / 10**")
    L.append(f"- After approved **review** items as well: **{full} / 10**")
    counts = res["counts"]
    L.append(f"- Checks scored: {counts['scored']} of {len(CHECKS)} "
             f"({counts['rendered']} from rendered HTML, {counts['source']} from source); "
             f"{counts['unknown']} not verified, {counts['na']} not applicable\n")
    L.append(md_table(["Category", "Score", "Pass", "Warn", "Fail"],
                      [[label, res["categories"].get(c) if res["categories"].get(c) is not None else "-",
                        *[sum(1 for cid, f in res["checks"].items() if CHECKS[cid][0] == c and f["status"] == st)
                          for st in ("pass", "warn", "fail")]] for c, label in CATEGORIES]))
    fixes = [(cid, f) for cid, f in res["checks"].items() if f["status"] in ("fail", "warn")]
    fixes.sort(key=lambda x: (["auto", "input", "review"].index(x[1]["class"]),
                              0 if x[1]["status"] == "fail" else 1, -CHECKS[x[0]][2]))
    L.append("\n## Fix plan\n")
    if not fixes:
        L.append("Nothing to fix among the scored checks.")
    for klass in ("auto", "input", "review"):
        items = [(cid, f) for cid, f in fixes if f["class"] == klass]
        if not items:
            continue
        head = CLASS_LABEL[klass]
        if klass == "input":
            needed = sorted({fact for cid, _ in items for fact in CHECKS[cid][4]})
            head += " -- needs: " + ", ".join(
                f"{k}{' = ' + str(res['facts'][k]['value']) if k in res['facts'] else ' (MISSING)'}" for k in needed)
        L.append(f"### {head} ({len(items)})\n")
        rows = []
        for cid, f in items:
            rows.append([f"`{cid}`", f["status"].upper(), CHECKS[cid][2], CHECKS[cid][1],
                         trunc("; ".join(f["evidence"][:3]), 160),
                         trunc(", ".join(f["where"][:4]), 90) or "-"])
        L.append(md_table(["Check", "Status", "Wt", "Requirement", "Evidence", "Where to fix"], rows))
        notes = [f"- `{cid}`: {f['note']}" for cid, f in items if f["note"]]
        if notes:
            L.append("\n" + "\n".join(notes))
        L.append("")
    L.append("Recipes for each check: `fix-playbook.md#<check-id>`.\n")
    passed = [cid for cid, f in res["checks"].items() if f["status"] == "pass"]
    L.append(f"## Passed ({len(passed)})\n")
    L.append(", ".join(f"`{c}`" for c in passed) or "none")
    unknown = [(cid, f) for cid, f in res["checks"].items() if f["status"] == "unknown"]
    if unknown:
        L.append(f"\n## Not verified ({len(unknown)})\n")
        for cid, f in unknown:
            L.append(f"- `{cid}` -- {'; '.join(f['evidence'][:2])}")
    info = [f"- `{cid}`: {f['note']}" for cid, f in res["checks"].items()
            if f["status"] == "pass" and f["note"] and "heuristic" not in f["note"]]
    if info:
        L.append("\n## Notes\n")
        L.extend(info)
    if res.get("pages"):
        L.append(f"\n## Pages ({len(res['pages'])} rendered)\n")
        L.append(md_table(["Page", "Title", "Desc", "H1", "Canonical", "JSON-LD", "Words"],
                          [[trunc(pg["ref"], 45), pg["title_len"], pg["desc_len"], pg["h1"],
                            trunc(pg["canonical"] or "MISSING", 45), trunc(", ".join(pg["types"]) or "-", 40),
                            pg["words"]] for pg in res["pages"][:40]]))
        if len(res["pages"]) > 40:
            L.append(f"\n... {len(res['pages']) - 40} more (see --json)")
    if res.get("content_notes"):
        L.append("\n## Beyond the codebase (content -- not scored)\n")
        L.extend(f"- {n}" for n in res["content_notes"])
        L.append("- Named authors, first-hand expertise, freshness and off-site presence are editorial work: "
                 "see geo-optimization.md.")
    if res["facts"]:
        L.append("\n## Facts found in the project\n")
        L.append(md_table(["Fact", "Value", "Source", "Confidence"],
                          [[k, trunc(", ".join(v["value"]) if isinstance(v["value"], list) else v["value"], 70),
                            trunc(v["source"], 60), v["confidence"]] for k, v in res["facts"].items()]))
    L.append("\n_The score measures technical SEO/GEO readiness from deterministic checks. It is not a "
             "ranking prediction: content quality, authority and field performance are outside it._")
    return "\n".join(L)


def render_compare(before, after):
    L = [f"## Change since {before['time']}\n"]
    L.append(f"**Score: {before['score']} -> {after['score']} / 10**\n")
    rows = []
    for c, label in CATEGORIES:
        b, a = before["categories"].get(c), after["categories"].get(c)
        if b != a:
            rows.append([label, b if b is not None else "-", a if a is not None else "-"])
    if rows:
        L.append(md_table(["Category", "Before", "After"], rows))
    changed = []
    for cid in CHECKS:
        b = before["checks"].get(cid, {}).get("status", "-")
        a = after["checks"].get(cid, {}).get("status", "-")
        if b != a:
            changed.append([f"`{cid}`", b, a, CHECKS[cid][1]])
    if changed:
        L.append("\n" + md_table(["Check", "Before", "After", "Requirement"], changed))
    regress = [r for r in changed if CREDIT.get(r[2], 1) < CREDIT.get(r[1], 0)]
    if regress:
        L.append("\n**REGRESSIONS:** " + ", ".join(r[0] for r in regress) + " -- investigate before shipping.")
    return "\n".join(L)


def build_result(target, project, rendered, rendered_rc_note=None):
    source = {}
    surfaces = []
    facts = {}
    stack, label = "none", "live site (no codebase)"
    if project:
        source, surfaces = source_findings(project)
        facts = discover_facts(project)
        stack, label = project.stack, project.label
    rendered_f = eval_pages(rendered.pages, rendered) if rendered else {}
    if project and rendered_f:
        routes = file_routes(project)
        for f in rendered_f.values():
            f.where = map_where(f.where, routes)
    results = assemble(source, rendered_f, stack)
    if project:
        defaults = {"robots-present": project.pub_path("robots.txt"), "robots-sitemap": project.pub_path("robots.txt"),
                    "robots-syntax": project.pub_path("robots.txt"), "sitemap-present": project.pub_path("sitemap.xml"),
                    "sitemap-lastmod": project.pub_path("sitemap.xml"), "llms-txt": project.pub_path("llms.txt"),
                    "not-found": project.pub_path("404.html") if project.stack in ("static", "vite", "cra")
                    else "404 page"}
        for cid, where in defaults.items():
            if results[cid].status in ("fail", "warn") and not results[cid].where:
                results[cid].where = [where]
    if rendered and project is None:
        # URL-only: make a best guess at the platform so fixes can be phrased for it.
        label = platform_of(rendered) or label
    overall, cats = score_of(results)
    reach, _ = score_of(results, ("auto", "input"))
    full, _ = score_of(results, ("auto", "input", "review"))
    counts = {
        "scored": sum(1 for f in results.values() if f.status in CREDIT),
        "rendered": sum(1 for f in results.values() if f.status in CREDIT and f.basis == "rendered"),
        "source": sum(1 for f in results.values() if f.status in CREDIT and f.basis == "source"),
        "unknown": sum(1 for f in results.values() if f.status == "unknown"),
        "na": sum(1 for f in results.values() if f.status == "na"),
    }
    evidence = []
    if rendered:
        evidence.append(f"rendered {rendered.basis} ({len(rendered.pages)} page(s))")
    if project:
        evidence.append(f"source {project.root}")
    pages = []
    if rendered:
        for pg in rendered.pages:
            if pg.status != 200:
                continue
            types = sorted({t for ts, _ in pg.parser.jsonld()[0] for t in ts})
            pages.append({"ref": pg.ref, "title": pg.parser.title, "title_len": len(pg.parser.title),
                          "desc_len": len(pg.parser.meta("description") or ""),
                          "h1": sum(1 for h in pg.parser.headings if h[0] == 1),
                          "canonical": pg.parser.link_href("canonical"), "types": types,
                          "words": pg.parser.body_words, "noindex": pg.noindex})
    return {
        "target": target, "time": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
        "stack": stack, "stack_label": label,
        "reference": project.reference if project else "live-site-audit.md",
        "evidence": " + ".join(evidence) or "none",
        "score": overall, "categories": cats, "score_after_fixable": reach, "score_after_review": full,
        "counts": counts, "checks": {cid: f.as_dict(cid) for cid, f in results.items()},
        "facts": facts, "surfaces": surfaces, "pages": pages,
        "content_notes": content_notes(rendered.pages) if rendered else [],
    }


def platform_of(rendered):
    if not rendered.pages:
        return None
    pg = rendered.pages[0]
    gen = (pg.parser.meta("generator") or "").lower()
    srcs = " ".join(im["src"] for im in pg.parser.images) + " " + " ".join(lk["href"] for lk in pg.parser.links)
    for needle, name in (("wordpress", "WordPress"), ("wix", "Wix"), ("squarespace", "Squarespace"),
                         ("webflow", "Webflow"), ("shopify", "Shopify"), ("hugo", "Hugo"), ("gatsby", "Gatsby"),
                         ("astro", "Astro"), ("docusaurus", "Docusaurus"), ("jekyll", "Jekyll"), ("ghost", "Ghost"),
                         ("drupal", "Drupal"), ("joomla", "Joomla")):
        if needle in gen:
            return f"{name} (live site, no codebase)"
    if "cdn.shopify.com" in srcs:
        return "Shopify (live site, no codebase)"
    if "/wp-content/" in srcs or "/wp-includes/" in srcs:
        return "WordPress (live site, no codebase)"
    if "/_next/" in srcs:
        return "Next.js (live site, no codebase)"
    return None


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------


def cmd_detect(args):
    p = Project(args.target)
    facts = discover_facts(p)
    source, surfaces = source_findings(p)
    recipe = p.render_recipe()
    if args.json:
        print(json.dumps({"root": p.root, "stack": p.stack, "label": p.label, "reference": p.reference,
                          "public_dir": p.public, "package_manager": p.package_manager(),
                          "render": recipe, "surfaces": surfaces, "facts": facts,
                          "git": os.path.isdir(os.path.join(p.root, ".git"))}, indent=2))
        return 0
    print(f"# Project: {p.root}\n")
    print(f"- **Stack:** {p.label} (`{p.stack}`)")
    ver = p.deps.get({"nextjs-app": "next", "nextjs-pages": "next", "vite": "vite", "cra": "react-scripts",
                      "astro": "astro", "nuxt": "nuxt", "sveltekit": "@sveltejs/kit", "gatsby": "gatsby"}.get(p.stack, ""))
    if ver:
        print(f"- **Version:** {ver}")
    print(f"- **Implementation reference:** `{p.reference}` (fix recipes: `fix-playbook.md`)")
    print(f"- **Web root for static files:** `{p.public or '.'}/`")
    print(f"- **Git repository:** {'yes' if os.path.isdir(os.path.join(p.root, '.git')) else 'NO -- changes cannot be diffed or reverted'}")
    print(f"- **Package manager:** {p.package_manager() if p.pkg else '-'}")
    print("\n## Rendered output (the authoritative evidence)\n")
    if recipe.get("install"):
        print(f"1. Install dependencies: `{recipe['install']}`")
    if recipe.get("build"):
        print(f"{'2' if recipe.get('install') else '1'}. Build: `{recipe['build']}`")
    if recipe["kind"] == "html":
        out = recipe["dir"]
        print(f"- Then score the output: `seo-scan.py score {p.root} --html {os.path.join(p.root, out) if out != '.' else p.root}`")
    elif recipe.get("serve"):
        print(f"- Then score the built site (the scanner starts and stops the server itself):")
        print(f"  `seo-scan.py score {p.root} --serve \"{recipe['serve']}\" --url {recipe['url']}`")
    else:
        print(f"- No local build for this stack: score {recipe.get('url')} with `--url`.")
    print("\n## SEO surfaces\n")
    rows = list(surfaces)
    for cid in ("robots-present", "sitemap-present", "llms-txt", "schema-org", "base-url"):
        f = source.get(cid)
        if f:
            rows.append([CHECKS[cid][1], f"{f.status.upper()}: {trunc('; '.join(f.evidence), 90)}"])
    print(md_table(["Surface", "Status / location"], rows))
    print("\n## Facts (values fixes may use -- never invent missing ones)\n")
    wanted = ["site_url", "brand", "lang", "logo", "og_image", "icon", "same_as"]
    print(md_table(["Fact", "Value", "Source", "Confidence"],
                   [[k, trunc(", ".join(facts[k]["value"]) if isinstance(facts[k]["value"], list) else facts[k]["value"], 70),
                     trunc(facts[k]["source"], 70), facts[k]["confidence"]] if k in facts else [k, "MISSING", "-", "-"]
                    for k in wanted]))
    return 0


def cmd_score(args):
    target = args.target
    project = rendered = None
    rc_note = None
    if is_url(target):
        rendered, rc, err = url_evidence(target, args.pages, args.timeout)
        if rc:
            print(f"**seo-scan: cannot fetch {target}** -- {err}", file=sys.stderr)
            if rc == 3:
                print(probe.POLICY_HELP, file=sys.stderr)
            return rc
    else:
        if not os.path.isdir(target):
            print(f"seo-scan: {target} is neither a directory nor a URL", file=sys.stderr)
            return 6
        project = Project(target)
        if args.serve and not args.url:
            print("seo-scan: --serve needs --url (the address the server will answer on)", file=sys.stderr)
            return 6
        if args.url:
            seeds = [pat for pat, _, _ in file_routes(project) if "[" not in pat]
            if args.serve:
                try:
                    with LocalServer(args.serve, args.url, project.root):
                        rendered, rc, err = url_evidence(args.url, args.pages, args.timeout, seeds)
                except RuntimeError as exc:
                    print(f"**seo-scan: local server failed** -- {exc}", file=sys.stderr)
                    return 7
            else:
                rendered, rc, err = url_evidence(args.url, args.pages, args.timeout, seeds)
            if rc:
                print(f"**seo-scan: cannot fetch {args.url}** -- {err}", file=sys.stderr)
                if rc == 3:
                    print(probe.POLICY_HELP, file=sys.stderr)
                return rc
        elif args.html:
            if not os.path.isdir(args.html):
                print(f"seo-scan: --html {args.html} is not a directory (did the build run?)", file=sys.stderr)
                return 6
            rendered = html_dir_evidence(args.html)
        elif project.stack == "static":
            rendered = html_dir_evidence(project.root)
    res = build_result(os.path.abspath(target) if not is_url(target) else target, project, rendered, rc_note)
    key = res["target"]
    before = None
    if args.compare is not None:
        path = args.compare or default_save_path(key)
        try:
            with open(path, encoding="utf-8") as fh:
                before = json.load(fh)
        except (OSError, ValueError):
            print(f"seo-scan: no baseline at {path} -- run with --save first", file=sys.stderr)
    if args.json:
        if before:
            res["baseline"] = {"score": before["score"], "time": before["time"]}
        print(json.dumps(res, indent=2))
    else:
        print(render_markdown(res))
        if before:
            print("\n" + render_compare(before, res))
    if args.save is not None:
        path = args.save or default_save_path(key)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2)
        print(f"\n_saved to {path} -- compare later with `--compare`_", file=sys.stderr if args.json else sys.stdout)
    return 0


def image_size(path):
    """(width, height) from the file header, or None. PNG, GIF, JPEG, WebP, SVG."""
    with open(path, "rb") as fh:
        head = fh.read(64 * 1024)
    if head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR":
        return struct.unpack(">II", head[16:24])
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", head[6:10])
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        chunk = head[12:16]
        if chunk == b"VP8 ":
            w, h = struct.unpack("<HH", head[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if chunk == b"VP8L":
            b = head[21:25]
            w = 1 + (((b[1] & 0x3F) << 8) | b[0])
            h = 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
            return w, h
        if chunk == b"VP8X":
            w = 1 + int.from_bytes(head[24:27], "little")
            h = 1 + int.from_bytes(head[27:30], "little")
            return w, h
    if head[:2] == b"\xff\xd8":
        i = 2
        while i < len(head) - 9:
            if head[i] != 0xFF:
                i += 1
                continue
            marker = head[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", head[i + 5:i + 9])
                return w, h
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            i += 2 + struct.unpack(">H", head[i + 2:i + 4])[0]
    text = head.decode("utf-8", "ignore")
    if "<svg" in text:
        m = re.search(r"<svg\b[^>]*>", text, re.S)
        tag = m.group(0) if m else ""
        w = re.search(r"""\bwidth=["']([\d.]+)(px)?["']""", tag)
        h = re.search(r"""\bheight=["']([\d.]+)(px)?["']""", tag)
        if w and h:
            return round(float(w.group(1))), round(float(h.group(1)))
        vb = re.search(r"""viewBox=["'][\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)""", tag)
        if vb:
            return round(float(vb.group(1))), round(float(vb.group(2)))
    return None


def cmd_imgsize(args):
    rc = 0
    for f in args.files:
        try:
            size = image_size(f)
        except OSError as exc:
            print(f"{f}\tERROR {exc}")
            rc = 6
            continue
        print(f"{f}\t{size[0]}x{size[1]}" if size else f"{f}\tUNKNOWN (unsupported format)")
    return rc


def main(argv=None):
    ap = argparse.ArgumentParser(prog="seo-scan", description="Codebase + rendered-output SEO/GEO scanner (stdlib only).")
    sub = ap.add_subparsers(dest="command")
    d = sub.add_parser("detect", help="stack, render recipe, SEO surfaces, facts")
    d.add_argument("target", nargs="?", default=".")
    d.add_argument("--json", action="store_true")
    s = sub.add_parser("score", help="scorecard and fix plan")
    s.add_argument("target", nargs="?", default=".", help="project directory, build output directory, or URL")
    s.add_argument("--html", help="build output directory to score as rendered evidence")
    s.add_argument("--url", help="running server (e.g. http://localhost:4319) to score as rendered evidence")
    s.add_argument("--serve", help="command that starts the site's server; stopped after the scan")
    s.add_argument("-n", "--pages", type=int, default=15, help="pages to crawl in URL mode (default 15, max 100)")
    s.add_argument("--timeout", type=float, default=20.0)
    s.add_argument("--json", action="store_true")
    s.add_argument("--save", nargs="?", const="", default=None, metavar="FILE")
    s.add_argument("--compare", nargs="?", const="", default=None, metavar="FILE")
    i = sub.add_parser("imgsize", help="intrinsic image dimensions")
    i.add_argument("files", nargs="+")
    args = ap.parse_args(argv)
    if not args.command:
        ap.print_help()
        return 6
    if args.command == "score":
        args.pages = max(1, min(100, args.pages))
    try:
        return {"detect": cmd_detect, "score": cmd_score, "imgsize": cmd_imgsize}[args.command](args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
