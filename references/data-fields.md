# Crawl Output Reference

Field reference for the JSON output from `aeo-crawl.py`.

## New in v2

```
pagetype_mode     → true if --page-types was used
page_types_sampled → [{url, type}] — which pages were selected and why
score             → {total, ai_crawler, ai_readability, structured_data, content_access, technical}
```

## Page Types

Detected automatically from URL patterns and title/meta cues:

```
homepage  → root URL or domain-only
product   → /products/item, /skills/skill-name, /courses/lesson
category  → /products, /blog, /docs, /learn, /skills (index pages)
content   → /blog/post, /article/slug, /docs/guide, /YYYY/MM/date-based
other     → anything that doesn't match above
```

Each page result includes a `page_type` field.

## Compare Mode Output

When using `--compare`, the output includes:

```
urls              → list of compared URLs
scores            → {url: {total, ai_crawler, ai_readability, ...}}
dimension_deltas  → {dimension: {url: score}} per dimension
recommendations   → [{dimension, gap, leader, suggestion}]
```

## Homepage Object

```
status                → HTTP status code (200, 403, 0 = failed)
title                 → <title> tag content
meta_description      → <meta name="description"> content
canonical             → <link rel="canonical"> href
og_tags               → All og:* meta tags
robots_meta           → <meta name="robots"> content
json_ld               → Parsed JSON-LD blocks (array)
json_ld_count         → Number of JSON-LD blocks
schema_types          → Deduplicated @type values from all JSON-LD
semantic_html         → Map of each semantic tag: true/false
semantic_tag_count    → How many of 7 semantic tags found
has_substantial_content → true if body text >500 chars
body_char_count       → Total visible text characters in <body>
has_iframes           → true if any <iframe> found
iframe_count          → Number of iframes
iframe_sources        → First 10 iframe src URLs
has_cookie_consent    → true if cookie banner class/id patterns detected
has_anti_bot          → true if anti-bot class/id patterns detected
api_endpoints         → URLs matching API patterns (max 15)
link_count            → Total unique links found
```

## AI Crawler Summary

```
blocked         → AI crawlers with Disallow: / rules
allowed         → AI crawlers explicitly allowed
not_configured  → AI crawlers with no rules at all
has_any_ai_rules → Whether any AI-specific rules exist
```

## llms.txt Object

```
exists          → Whether /llms.txt returned 200
size_bytes      → File size
has_h1          → Required per spec
has_blockquote  → Recommended per spec
has_h2_sections → Recommended per spec
has_links       → Links to detailed content pages
follows_spec    → true if has_h1 (minimum requirement)
content_preview → First 600 chars
```

## agents-brief.txt Object

```
exists          → Whether /agents-brief.txt returned 200
size_bytes      → File size
content_preview → First 600 chars
```

## Sitemap Object

```
exists           → Whether any URLs were found in sitemap
url_count        → Total URLs in sitemap
crawlable_count  → URLs after filtering (no images, PDFs, etc.)
top_urls         → First 30 URLs with priority and lastmod
```

## Aggregate Object

```
pages_crawled                  → Total HTML pages analyzed
pages_with_json_ld             → Pages containing JSON-LD
pages_with_substantial_content → Pages with >500 chars body text
pages_js_rendered              → Pages with minimal body content
pages_with_semantic_html       → Pages using ≥3 semantic tags
pages_with_cookie_consent      → Pages with cookie banners
pages_with_anti_bot            → Pages with anti-bot protection
pages_with_iframes             → Pages containing iframes
schema_types_found             → All schema types across all pages
api_endpoints                  → All API endpoints across all pages
page_types_found               → Page types detected (homepage, product, etc.)
```
