#!/usr/bin/env python3
"""
aeo-crawl.py — Fetch and parse website data for AEO (Agent Engine Optimization) audit.

Pure Python stdlib. No dependencies beyond the standard library.

Usage:
    python3 aeo-crawl.py <url> [--max-pages N] [--timeout SECONDS] [--max-bytes BYTES] [--no-ssl-verify]

Output: JSON to stdout
"""

import sys
import json
import re
import argparse
import urllib.request
import urllib.error
import urllib.parse
import ssl
from html.parser import HTMLParser
from html import unescape
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from collections import defaultdict
from urllib.parse import urlparse


# ─── Constants ───────────────────────────────────────────────────────────────

USER_AGENT = "Mozilla/5.0 (compatible; AEO-Toolkit/1.0)"

AI_CRAWLERS = {
    "GPTBot": "OpenAI — training data",
    "ChatGPT-User": "OpenAI — live browsing",
    "OAI-SearchBot": "OpenAI — search indexing",
    "ClaudeBot": "Anthropic — training data",
    "Claude-User": "Anthropic — live queries",
    "Claude-SearchBot": "Anthropic — search indexing",
    "Google-Extended": "Google — AI training (separate from Googlebot)",
    "PerplexityBot": "Perplexity",
    "Bytespider": "ByteDance",
    "CCBot": "Common Crawl",
    "FacebookBot": "Meta",
    "Applebot-Extended": "Apple — AI training",
    "TiktokBot": "TikTok",
}

COOKIE_PATTERNS = [
    r"cookie", r"consent", r"gdpr", r"privacy", r"accept.all",
    r"cookie-banner", r"cookie-consent", r"cookie-notice",
    r"cc-banner", r"cc-window", r"onetrust", r"cookieyes",
    r"quantcast", r"consentmanager", r"borlabs",
]

ANTIBOT_PATTERNS = [
    r"cloudflare", r"captcha", r"challenge.platform",
    r"just.a.moment", r"checking.your.browser",
    r"distilnetworks", r"incapsula", r"akamai",
    r"ddos.guard", r"access.denied", r"ratelimit",
    r"403.forbidden", r"bot.management",
]

SEMANTIC_TAGS = {"header", "main", "article", "nav", "footer", "section", "aside"}

SKIP_EXTENSIONS = re.compile(
    r"\.(jpg|jpeg|png|gif|svg|ico|webp|pdf|zip|gz|tar|css|js|woff|woff2|ttf|eot|mp[34]|avi|mov)(\?|$)",
    re.IGNORECASE,
)

API_PATTERNS = [
    r"/api/", r"/v\d+/", r"/rest/", r"/graphql",
    r"\.json\b", r"/webhook", r"/oauth", r"/auth/",
    r"/checkout", r"/booking", r"/reserve", r"/payment",
    r"/subscribe", r"/register", r"/login",
]


# ─── HTML Parser ─────────────────────────────────────────────────────────────

class AEOParser(HTMLParser):
    """Extract AEO-relevant metadata from HTML."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_description = ""
        self.meta_tags = {}
        self.canonical = ""
        self.json_ld_blocks = []
        self.semantic_tags_found = set()
        self.iframes = []
        self.links = []
        self.script_srcs = []

        self._in_title = False
        self._in_json_ld = False
        self._current_json_ld = ""
        self._in_head = True
        self._in_body = False
        self._in_noscript = False
        self._body_chars = 0
        self._has_cookie = False
        self._has_antibot = False

    # ── tag events ──

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        ad = {k.lower(): (v or "") for k, v in attrs}

        if t == "head":
            self._in_head = True
        elif t == "body":
            self._in_head = False
            self._in_body = True
        if t == "noscript":
            self._in_noscript = True

        # title
        if t == "title" and self._in_head:
            self._in_title = True

        # meta
        if t == "meta":
            name = ad.get("name", "").lower()
            prop = ad.get("property", "").lower()
            content = ad.get("content", "")
            if name == "description":
                self.meta_description = content
            elif prop:
                self.meta_tags[prop] = content
            elif name:
                self.meta_tags[name] = content

        # link (canonical, other)
        if t == "link":
            rel = ad.get("rel", "").lower()
            href = ad.get("href", "")
            if "canonical" in rel:
                self.canonical = href
            if href.startswith("http"):
                self.links.append(href)

        # script (JSON-LD + src)
        if t == "script":
            if ad.get("type", "") == "application/ld+json":
                self._in_json_ld = True
                self._current_json_ld = ""
            src = ad.get("src", "")
            if src:
                self.script_srcs.append(src)

        # semantic
        if t in SEMANTIC_TAGS:
            self.semantic_tags_found.add(t)

        # iframe
        if t == "iframe":
            src = ad.get("src", "")
            if src:
                self.iframes.append(src)

        # anchor links
        if t == "a":
            href = ad.get("href", "")
            if href:
                self.links.append(href)

        # cookie / anti-bot detection via class + id
        haystack = ad.get("class", "") + " " + ad.get("id", "")
        if not self._has_cookie:
            self._has_cookie = any(re.search(p, haystack, re.I) for p in COOKIE_PATTERNS)
        if not self._has_antibot:
            self._has_antibot = any(re.search(p, haystack, re.I) for p in ANTIBOT_PATTERNS)

    def handle_endtag(self, tag):
        t = tag.lower()
        if t == "title":
            self._in_title = False
        if t == "head":
            self._in_head = False
        if t == "noscript":
            self._in_noscript = False
        if t == "script" and self._in_json_ld:
            self._in_json_ld = False
            raw = self._current_json_ld.strip()
            if raw:
                self.json_ld_blocks.append(raw)

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_json_ld:
            self._current_json_ld += data
        if self._in_body and not self._in_noscript and not self._in_json_ld:
            stripped = data.strip()
            if stripped:
                self._body_chars += len(stripped)

    def handle_comment(self, data):
        if not self._has_antibot:
            self._has_antibot = any(re.search(p, data, re.I) for p in ANTIBOT_PATTERNS)

    # ── derived properties ──

    @property
    def has_substantial_content(self):
        return self._body_chars > 500

    @property
    def body_char_count(self):
        return self._body_chars

    @property
    def has_cookie_consent(self):
        return self._has_cookie

    @property
    def has_anti_bot(self):
        return self._has_antibot


# ─── Helpers ─────────────────────────────────────────────────────────────────

def fetch(url, timeout=15, max_bytes=524288, verify_ssl=True):
    """Return (status, content_type, body_text, error_string)."""
    try:
        ctx = None
        if not verify_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml,text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = resp.read(max_bytes)
            return resp.status, resp.headers.get("Content-Type", ""), body.decode("utf-8", errors="replace"), None
    except urllib.error.HTTPError as e:
        try:
            body = e.read(max_bytes).decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return e.code, "", body, None
    except Exception as e:
        return 0, "", "", str(e)


def parse_html(html_text):
    """Parse HTML and return an AEOParser instance."""
    p = AEOParser()
    try:
        p.feed(html_text)
    except Exception:
        pass
    return p


def extract_schema_types(json_ld_blocks):
    """Return deduplicated list of @type values from JSON-LD blocks."""
    types = set()
    for block in json_ld_blocks:
        try:
            data = json.loads(block) if isinstance(block, str) else block
        except (json.JSONDecodeError, TypeError):
            continue
        _walk_types(data, types)
    return sorted(types)


def _walk_types(obj, types):
    """Recursively collect @type values."""
    if isinstance(obj, dict):
        if "@type" in obj:
            t = obj["@type"]
            if isinstance(t, str):
                types.add(t)
            elif isinstance(t, list):
                types.update(t)
        for v in obj.values():
            _walk_types(v, types)
    elif isinstance(obj, list):
        for item in obj:
            _walk_types(item, types)


def detect_api_endpoints(links, script_srcs):
    """Find URLs matching API patterns."""
    endpoints = set()
    for url in set(links + script_srcs):
        if any(re.search(p, url, re.I) for p in API_PATTERNS):
            endpoints.add(url)
    return sorted(endpoints)


def page_result(url, parser, status, content_type):
    """Build the per-page result dict."""
    schema_types = extract_schema_types(parser.json_ld_blocks)
    parsed_ld = []
    for block in parser.json_ld_blocks:
        try:
            parsed_ld.append(json.loads(block))
        except json.JSONDecodeError:
            parsed_ld.append({"_raw_preview": block[:300]})

    apis = detect_api_endpoints(parser.links, parser.script_srcs)
    return {
        "url": url,
        "status": status,
        "content_type": content_type or "",
        "title": parser.title.strip(),
        "meta_description": parser.meta_description.strip(),
        "canonical": parser.canonical,
        "og_tags": {k: v for k, v in parser.meta_tags.items() if k.startswith("og:")},
        "robots_meta": parser.meta_tags.get("robots", ""),
        "json_ld": parsed_ld,
        "json_ld_count": len(parsed_ld),
        "schema_types": schema_types,
        "semantic_html": {t: t in parser.semantic_tags_found for t in sorted(SEMANTIC_TAGS)},
        "semantic_tag_count": len(parser.semantic_tags_found),
        "has_substantial_content": parser.has_substantial_content,
        "body_char_count": parser.body_char_count,
        "has_iframes": len(parser.iframes) > 0,
        "iframe_count": len(parser.iframes),
        "iframe_sources": parser.iframes[:10],
        "has_cookie_consent": parser.has_cookie_consent,
        "has_anti_bot": parser.has_anti_bot,
        "api_endpoints": apis[:15],
        "link_count": len(set(parser.links)),
    }


# ─── robots.txt ──────────────────────────────────────────────────────────────

def parse_robots_txt(text):
    """Parse robots.txt. Return structured dict."""
    result = {
        "exists": True,
        "ai_crawlers": {},
        "standard_crawlers": {},
        "sitemaps": [],
    }

    current_agent = None
    current_rules = []

    def flush():
        nonlocal current_agent, current_rules
        if not current_agent:
            return
        entry = {"rules": current_rules}
        if current_agent in AI_CRAWLERS:
            entry["description"] = AI_CRAWLERS[current_agent]
            # Determine status
            disallow_all = any(
                r["type"] == "disallow" and r["path"] in ("/", "*")
                for r in current_rules
            )
            has_allow = any(r["type"] == "allow" for r in current_rules)
            if disallow_all and not has_allow:
                entry["status"] = "blocked"
            elif not current_rules:
                entry["status"] = "not_configured"
            elif has_allow and disallow_all:
                entry["status"] = "partial"
            else:
                entry["status"] = "allowed"
            result["ai_crawlers"][current_agent] = entry
        else:
            result["standard_crawlers"][current_agent] = current_rules
        current_rules = []

    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.lower().startswith("user-agent:"):
            flush()
            current_agent = line.split(":", 1)[1].strip()
        elif line.lower().startswith("disallow:"):
            current_rules.append({"type": "disallow", "path": line.split(":", 1)[1].strip()})
        elif line.lower().startswith("allow:"):
            current_rules.append({"type": "allow", "path": line.split(":", 1)[1].strip()})
        elif line.lower().startswith("sitemap:"):
            result["sitemaps"].append(line.split(":", 1)[1].strip())

    flush()
    return result


def ai_crawler_summary(robots_data):
    """Summarise AI crawler access."""
    blocked, allowed, not_configured = [], [], []
    for agent in AI_CRAWLERS:
        if agent in robots_data.get("ai_crawlers", {}):
            st = robots_data["ai_crawlers"][agent].get("status", "unknown")
            if st == "blocked":
                blocked.append(agent)
            elif st == "partial":
                not_configured.append(f"{agent} (partial)")
            else:
                allowed.append(agent)
        else:
            not_configured.append(agent)
    return {
        "blocked": blocked,
        "allowed": allowed,
        "not_configured": not_configured,
        "has_any_ai_rules": len(robots_data.get("ai_crawlers", {})) > 0,
    }


# ─── sitemap.xml ─────────────────────────────────────────────────────────────

def parse_sitemap(text, base_url):
    """Parse sitemap.xml. Return list of {url, priority, lastmod}."""
    urls = []
    try:
        # Strip namespaces for simpler parsing
        clean = re.sub(r'\sxmlns[^"]*"[^"]*"', '', text, flags=re.DOTALL)
        root = ET.fromstring(clean)

        # <urlset> — direct URLs
        for url_el in root.iter("url"):
            loc, pri, mod = "", None, None
            for child in url_el:
                if child.tag == "loc" and child.text:
                    loc = child.text.strip()
                elif child.tag == "priority" and child.text:
                    try:
                        pri = float(child.text)
                    except ValueError:
                        pass
                elif child.tag == "lastmod" and child.text:
                    mod = child.text.strip()
            if loc:
                urls.append({"url": loc, "priority": pri, "lastmod": mod})

        # <sitemap> — sitemap index
        if not urls:
            for sm_el in root.iter("sitemap"):
                loc = ""
                for child in sm_el:
                    if child.tag == "loc" and child.text:
                        loc = child.text.strip()
                if loc:
                    urls.append({"url": loc, "priority": None, "lastmod": None})
    except ET.ParseError:
        # Regex fallback
        for m in re.finditer(r"<loc>\s*(.*?)\s*</loc>", text):
            urls.append({"url": m.group(1).strip(), "priority": None, "lastmod": None})

    urls.sort(key=lambda u: (u["priority"] is not None, u["priority"] or 0), reverse=True)
    return urls


# ─── Main crawl ──────────────────────────────────────────────────────────────

def crawl(url, max_pages=10, timeout=15, max_bytes=524288, verify_ssl=True, page_type_mode=False):
    """Run full AEO crawl. Return result dict."""

    parsed = urllib.parse.urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    result = {
        "url": url,
        "base_url": base,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "homepage": None,
        "robots_txt": None,
        "ai_crawler_summary": None,
        "sitemap": None,
        "llms_txt": None,
        "agents_brief_txt": None,
        "additional_pages": [],
        "aggregate": {},
        "errors": [],
    }

    # 1. robots.txt
    st, _, body, err = fetch(f"{base}/robots.txt", timeout, max_bytes, verify_ssl)
    if st == 200 and body and not err:
        result["robots_txt"] = parse_robots_txt(body)
    else:
        result["robots_txt"] = {"exists": False, "ai_crawlers": {}, "standard_crawlers": {}, "sitemaps": []}
    result["ai_crawler_summary"] = ai_crawler_summary(result["robots_txt"])

    # 2. Homepage
    st, ct, body, err = fetch(url, timeout, max_bytes, verify_ssl)
    if err and st == 0:
        result["homepage"] = {"url": url, "status": 0, "error": err}
        result["errors"].append(f"Homepage fetch failed: {err}")
        # Still try other checks
    else:
        is_html = "text/html" in (ct or "").lower() or "<html" in (body or "")[:500].lower()
        if is_html and body:
            p = parse_html(body)
            result["homepage"] = page_result(url, p, st, ct)
        else:
            result["homepage"] = {"url": url, "status": st, "content_type": ct, "is_html": False, "error": "Not HTML"}
            result["errors"].append(f"Homepage is not HTML (content-type: {ct})")

    # 3. llms.txt
    st, _, body, _ = fetch(f"{base}/llms.txt", timeout, max_bytes, verify_ssl)
    if st == 200 and body:
        has_h1 = bool(re.search(r"^#\s+", body, re.M))
        has_bq = ">" in body[:500]
        has_h2 = bool(re.search(r"^##\s+", body, re.M))
        has_links = bool(re.search(r"\[.+\]\(http", body))
        result["llms_txt"] = {
            "exists": True,
            "size_bytes": len(body.encode("utf-8")),
            "has_h1": has_h1,
            "has_blockquote": has_bq,
            "has_h2_sections": has_h2,
            "has_links": has_links,
            "follows_spec": has_h1,  # H1 is the only required element per spec
            "content_preview": body[:600].strip(),
        }
    else:
        result["llms_txt"] = {"exists": False}

    # 4. agents-brief.txt
    st, _, body, _ = fetch(f"{base}/agents-brief.txt", timeout, max_bytes, verify_ssl)
    if st == 200 and body:
        result["agents_brief_txt"] = {
            "exists": True,
            "size_bytes": len(body.encode("utf-8")),
            "content_preview": body[:600].strip(),
        }
    else:
        result["agents_brief_txt"] = {"exists": False}

    # 5. Sitemap discovery
    sitemap_urls = result["robots_txt"].get("sitemaps", [])
    if not sitemap_urls:
        sitemap_urls = [f"{base}/sitemap.xml"]

    all_sitemap_pages = []
    for sm_url in sitemap_urls:
        st, _, body, _ = fetch(sm_url, timeout, max_bytes, verify_ssl)
        if st == 200 and body:
            pages = parse_sitemap(body, base)
            all_sitemap_pages.extend(pages)

    # Deduplicate
    seen = set()
    unique = []
    for p in all_sitemap_pages:
        if p["url"] not in seen:
            seen.add(p["url"])
            unique.append(p)

    # Filter out the audited URL and non-page resources
    crawl_urls = [
        p for p in unique
        if p["url"] not in (url, url + "/")
        and not SKIP_EXTENSIONS.search(p["url"])
        and p["url"].startswith("http")
    ]

    result["sitemap"] = {
        "exists": len(unique) > 0,
        "url_count": len(unique),
        "crawlable_count": len(crawl_urls),
        "top_urls": [{"url": p["url"], "priority": p["priority"], "lastmod": p["lastmod"]} for p in unique[:30]],
    }

    # 6. Crawl additional pages
    if page_type_mode and crawl_urls:
        # Smart sampling: pick one URL per page type
        samples = select_page_type_samples(
            [{"url": p["url"], "priority": p["priority"], "lastmod": p["lastmod"]} for p in crawl_urls],
            base,
        )
        sample_urls = {s["url"] for s in samples}
        crawl_urls = [p for p in crawl_urls if p["url"] in sample_urls]
        result["page_type_mode"] = True
        result["page_types_sampled"] = [{"url": s["url"], "type": classify_page_type(s["url"])} for s in samples]
    elif max_pages > 0:
        crawl_urls = crawl_urls[:max_pages]

    for page_info in crawl_urls:
        pu = page_info["url"]
        st, ct, body, err = fetch(pu, timeout, max_bytes, verify_ssl)
        if err and st == 0:
            result["additional_pages"].append({"url": pu, "status": 0, "error": err})
            continue
        is_html = "text/html" in (ct or "").lower() or "<html" in (body or "")[:500].lower()
        if is_html and body:
            p = parse_html(body)
            pr = page_result(pu, p, st, ct)
            pr["priority"] = page_info["priority"]
            pr["lastmod"] = page_info["lastmod"]
            pr["page_type"] = classify_page_type(pu, pr.get("title", ""), pr.get("meta_description", ""))
            result["additional_pages"].append(pr)
        else:
            result["additional_pages"].append({
                "url": pu, "status": st, "content_type": ct,
                "is_html": False, "priority": page_info["priority"],
            })

    # 7. Aggregate stats
    all_pages = []
    hp = result.get("homepage")
    if hp and hp.get("is_html", True) and not hp.get("error"):
        hp["page_type"] = "homepage"
        all_pages.append(hp)
    all_pages.extend([p for p in result["additional_pages"] if p.get("is_html", True)])

    total = len(all_pages)
    with_json_ld = sum(1 for p in all_pages if p.get("json_ld_count", 0) > 0)
    with_content = sum(1 for p in all_pages if p.get("has_substantial_content", False))
    js_rendered = sum(1 for p in all_pages if not p.get("has_substantial_content", True))
    with_semantic = sum(1 for p in all_pages if p.get("semantic_tag_count", 0) >= 3)
    with_cookie = sum(1 for p in all_pages if p.get("has_cookie_consent", False))
    with_antibot = sum(1 for p in all_pages if p.get("has_anti_bot", False))
    with_iframes = sum(1 for p in all_pages if p.get("has_iframes", False))

    all_schema = set()
    all_apis = set()
    page_types_found = set()
    for p in all_pages:
        all_schema.update(p.get("schema_types", []))
        all_apis.update(p.get("api_endpoints", []))
        pt = p.get("page_type", "unknown")
        page_types_found.add(pt)

    result["aggregate"] = {
        "pages_crawled": total,
        "pages_with_json_ld": with_json_ld,
        "pages_with_substantial_content": with_content,
        "pages_js_rendered": js_rendered,
        "pages_with_semantic_html": with_semantic,
        "pages_with_cookie_consent": with_cookie,
        "pages_with_anti_bot": with_antibot,
        "pages_with_iframes": with_iframes,
        "schema_types_found": sorted(all_schema),
        "api_endpoints": sorted(all_apis),
        "page_types_found": sorted(page_types_found),
    }

    return result


# ─── Page-Type Classification ───────────────────────────────────────────────

# URL patterns that suggest different page types
PAGE_TYPE_PATTERNS = {
    "product": [
        r"/(?:product|item|sku)/[^/]+$",
        r"/(?:skills?|tools?|plugins?|extensions?|apps?)/[^/]+$",
        r"/(?:courses?|lessons?|tutorials?)/[^/]+$",
        r"/(?:listing|offer|deal|package)s?/[^/]+$",
    ],
    "category": [
        r"/(?:categor|tag|topic)s?(/[^/]+)?/?$",
        r"/(?:skills?|tools?|plugins?|products?|services?|courses?|blog)s?/?$",
        r"/(?:collections?|departments?|industries?)s?/?$",
        r"/(?:docs?|learn|guides?|help|support)s?/?$",
    ],
    "content": [
        r"/(?:blog|article|post|news|story|press|journal)s?/[^/]+$",
        r"/(?:docs?|guide|tutorial|how-to|about|faq)s?/[^/]+$",
        r"/(?:page|wp|content)/[^/]+$",
        r"/\d{4}/\d{2}/",  # date-based blog URLs
    ],
}


def classify_page_type(url, title="", meta_desc=""):
    """Classify a URL into a page type: homepage, product, category, content, or other."""
    path = urlparse(url).path.rstrip("/")

    # Homepage detection
    if path in ("", "/") or url.rstrip("/").endswith(urlparse(url).netloc):
        return "homepage"

    for page_type, patterns in PAGE_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, path, re.I):
                return page_type

    # Fallback: use title/meta cues
    text = (title + " " + meta_desc).lower()
    if any(w in text for w in ["product", "sku", "price", "buy", "add to cart"]):
        return "product"
    if any(w in text for w in ["blog", "article", "post", "news", "author"]):
        return "content"
    if any(w in text for w in ["browse", "all", "catalog", "directory", "collection"]):
        return "category"

    return "other"


def select_page_type_samples(sitemap_pages, base_url, max_per_type=1):
    """Pick one URL per page type from the sitemap. Returns list of {url, type, priority, lastmod}."""
    typed = defaultdict(list)
    homepage_url = None

    for page in sitemap_pages:
        url = page["url"]
        ptype = classify_page_type(url)
        if ptype == "homepage":
            homepage_url = page
            continue
        typed[ptype].append(page)

    samples = []
    # Prefer higher priority pages within each type
    for ptype, pages in typed.items():
        pages.sort(key=lambda p: (p["priority"] is not None, p["priority"] or 0), reverse=True)
        samples.extend(pages[:max_per_type])

    return samples


# ─── Compare Mode ──────────────────────────────────────────────────────────

def compare_results(results):
    """Compare two or more crawl results side-by-side. Returns comparison dict."""
    if len(results) < 2:
        return {"error": "Need at least 2 URLs to compare"}

    comparison = {
        "urls": [],
        "scores": {},
        "dimension_deltas": {},
        "recommendations": [],
    }

    for r in results:
        url = r["url"]
        score = calculate_score(r)
        comparison["urls"].append(url)
        comparison["scores"][url] = score

    # Dimension-level comparison
    dimensions = ["ai_crawler", "ai_readability", "structured_data", "content_access", "technical"]
    for dim in dimensions:
        vals = {}
        for r in results:
            s = calculate_score(r)
            vals[r["url"]] = s.get(dim, 0)
        comparison["dimension_deltas"][dim] = vals

    # Find the biggest competitive gaps
    url_a, url_b = results[0]["url"], results[1]["url"]
    score_a = comparison["scores"][url_a]
    score_b = comparison["scores"][url_b]

    for dim in dimensions:
        diff = comparison["dimension_deltas"][dim].get(url_b, 0) - comparison["dimension_deltas"][dim].get(url_a, 0)
        if abs(diff) >= 5:
            leader = url_a if diff < 0 else url_b
            gainer = url_b if diff < 0 else url_a
            comparison["recommendations"].append({
                "dimension": dim,
                "gap": diff,
                "leader": leader,
                "suggestion": f"{gainer} could gain {abs(diff)} pts by improving {dim}",
            })

    comparison["recommendations"].sort(key=lambda r: abs(r["gap"]), reverse=True)
    return comparison


def calculate_score(crawl_data):
    """Calculate visibility score from crawl data. Returns dict with per-dimension scores."""
    score = {"total": 0, "ai_crawler": 0, "ai_readability": 0, "structured_data": 0, "content_access": 0, "technical": 0}

    # AI Crawler Access (20)
    ai = crawl_data.get("ai_crawler_summary", {})
    if crawl_data.get("robots_txt", {}).get("exists"):
        score["ai_crawler"] += 5
    if not ai.get("blocked"):
        score["ai_crawler"] += 10
    if ai.get("allowed"):
        score["ai_crawler"] += 5

    # AI Readability Files (20)
    llms = crawl_data.get("llms_txt", {})
    if llms.get("exists") and llms.get("follows_spec"):
        score["ai_readability"] += 10
    if llms.get("has_links"):
        score["ai_readability"] += 5
    ab = crawl_data.get("agents_brief_txt", {})
    if ab.get("exists"):
        score["ai_readability"] += 5

    # Structured Data (25)
    hp = crawl_data.get("homepage", {})
    agg = crawl_data.get("aggregate", {})
    if hp.get("json_ld_count", 0) > 0:
        score["structured_data"] += 5
    schema = set(agg.get("schema_types_found", []))
    if schema & {"Organization", "WebSite"}:
        score["structured_data"] += 5
    if schema & {"LocalBusiness", "Service", "Product", "SoftwareApplication"}:
        score["structured_data"] += 5
    if "FAQPage" in schema:
        score["structured_data"] += 5
    if len(schema) > 1:
        score["structured_data"] += 5

    # Content Accessibility (20)
    if hp.get("has_substantial_content"):
        score["content_access"] += 8
    if hp.get("semantic_tag_count", 0) >= 3:
        score["content_access"] += 4
    if len(hp.get("meta_description", "")) > 50:
        score["content_access"] += 4
    if len(hp.get("title", "")) > 10:
        score["content_access"] += 4

    # Technical Foundation (15)
    if crawl_data.get("sitemap", {}).get("exists"):
        score["technical"] += 5
    if not hp.get("has_anti_bot"):
        score["technical"] += 5
    if not hp.get("has_cookie_consent"):
        score["technical"] += 5

    score["total"] = sum(score[d] for d in ["ai_crawler", "ai_readability", "structured_data", "content_access", "technical"])
    return score


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="AEO Crawl — website data for AEO audit")
    ap.add_argument("url", nargs="?", help="URL to audit (must start with http:// or https://)")
    ap.add_argument("--max-pages", type=int, default=10, help="Max pages from sitemap (default: 10, 0 = all)")
    ap.add_argument("--timeout", type=int, default=15, help="Request timeout in seconds")
    ap.add_argument("--max-bytes", type=int, default=524288, help="Max response size in bytes (default 512KB)")
    ap.add_argument("--no-ssl-verify", action="store_true", help="Skip SSL certificate verification")
    ap.add_argument("--page-types", action="store_true", help="Sample one URL per page type instead of top N by priority")
    ap.add_argument("--compare", nargs="+", metavar="URL", help="Compare two or more URLs (e.g. --compare URL1 URL2)")
    ap.add_argument("--score", action="store_true", help="Calculate and output score from crawl data")
    args = ap.parse_args()

    def validate_url(u):
        u = u.strip()
        if not re.match(r"^https?://", u, re.I):
            return None
        if any(c in u for c in ';|&$`(){}<>\n'):
            return None
        return u

    # Compare mode
    if args.compare:
        urls = [validate_url(u) for u in args.compare]
        urls = [u for u in urls if u]
        if len(urls) < 2:
            print(json.dumps({"error": "--compare requires at least 2 valid URLs"}))
            sys.exit(1)
        results = []
        for u in urls:
            r = crawl(u, max_pages=4 if args.page_types else args.max_pages,
                      timeout=args.timeout, max_bytes=args.max_bytes, verify_ssl=not args.no_ssl_verify)
            results.append(r)
        comp = compare_results(results)
        print(json.dumps(comp, indent=2, default=str))
        return

    # Single URL mode
    if not args.url:
        print(json.dumps({"error": "Provide a URL or use --compare"}))
        sys.exit(1)

    url = validate_url(args.url)
    if not url:
        print(json.dumps({"error": "Invalid URL — must start with http:// or https:// and contain no shell metacharacters"}))
        sys.exit(1)

    result = crawl(
        url,
        max_pages=args.max_pages,
        timeout=args.timeout,
        max_bytes=args.max_bytes,
        verify_ssl=not args.no_ssl_verify,
        page_type_mode=args.page_types,
    )

    if args.score:
        s = calculate_score(result)
        result["score"] = s

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
