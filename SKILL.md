---
name: aeo-toolkit
description: >-
  Audit any website's visibility to AI agents and generate every file needed
  to fix it. Detects JS rendering gaps, missing structured data, blocked AI
  crawlers, cookie consent walls, anti-bot protections, and more. Generates
  robots.txt, llms.txt, JSON-LD templates, and agents-brief.txt.
allowed-tools:
  - Bash(python3 *)
  - Read
  - Write(*.txt)
  - Write(*.json)
  - Write(*.md)
  - Write(*.html)
---

# AEO Toolkit — Agent Engine Optimization

Audit and improve a website's visibility to AI agents. No external dependencies — pure Python stdlib + curl.

## When to Use

- "Audit my site for AI visibility"
- "Why doesn't my business show up in ChatGPT / Claude / Perplexity?"
- "Check if AI agents can read my website"
- "Generate llms.txt / robots.txt / structured data for my site"
- "AEO audit", "GEO audit", "AI search optimization"
- "Make my site visible to AI agents"

## Quick Start

```bash
python3 scripts/aeo-crawl.py "https://example.com"
```

The default crawls the homepage + robots.txt + llms.txt + agents-brief.txt + sitemap discovery, plus up to 10 additional pages from the sitemap. For a quick homepage-only check or a deep crawl:

```bash
# Homepage + essential files only (no sitemap pages)
python3 scripts/aeo-crawl.py "https://example.com" --max-pages 1

# Deep crawl (up to 50 pages from sitemap)
python3 scripts/aeo-crawl.py "https://example.com" --max-pages 50

# All pages (slow — use only for small sites)
python3 scripts/aeo-crawl.py "https://example.com" --max-pages 0
```

Flags:
- `--max-pages N` — max additional pages from sitemap (default: 10, 0 = all)
- `--timeout SECONDS` — per-request timeout (default: 15)
- `--max-bytes BYTES` — max response size per page (default: 524288 = 512KB)
- `--no-ssl-verify` — skip SSL verification (for local dev / self-signed certs)

## Audit Flow

### Step 1: Run the Crawl

Run the script against the target URL. Review the JSON output carefully.

**Do NOT show the raw JSON to the user.** Parse it, analyze it, and present findings in a human-readable report.

### Step 2: Analyze the Results

Read each section of the output and identify issues. Use the scoring methodology below to calculate a visibility score.

Key sections to analyze:

1. **`homepage`** — The most important page. Check:
   - `has_substantial_content` — if `false`, the site is likely JS-rendered and invisible to agents without a browser
   - `body_char_count` — under 500 = essentially empty for agents
   - `json_ld_count` and `schema_types` — structured data presence
   - `semantic_html` — are semantic tags used?
   - `has_cookie_consent` — cookie wall may block content
   - `has_anti_bot` — site may be blocking agent requests
   - `has_iframes` — content hidden in iframes is invisible to simple fetchers
   - `api_endpoints` — signals interactive features
   - `title`, `meta_description` — basic SEO/AEO hygiene
   - `og_tags` — Open Graph presence

2. **`ai_crawler_summary`** — Critical check:
   - `blocked` — these AI crawlers are explicitly disallowed. The site won't appear in their training data or search results
   - `not_configured` — no explicit rules (neutral, but worth adding explicit allows)
   - `has_any_ai_rules` — does robots.txt mention AI crawlers at all?

3. **`llms_txt`** — AI sitemap:
   - `exists` — is it there?
   - `follows_spec` — does it have the required H1 heading?
   - `has_blockquote`, `has_h2_sections`, `has_links` — quality signals

4. **`agents_brief_txt`** — Agent permissions:
   - `exists` — only relevant for sites with APIs / e-commerce / interactive features

5. **`sitemap`** — Page discovery:
   - `exists` — without a sitemap, agents can't discover all pages
   - `url_count` — how many pages are indexed?

6. **`aggregate`** — Cross-site patterns:
   - `pages_js_rendered` — pages where body content is minimal
   - `pages_with_json_ld` — structured data coverage
   - `pages_with_cookie_consent` — cookie wall prevalence
   - `schema_types_found` — all schema types across the site

### Step 3: Score Visibility

Calculate a score using this methodology:

**AI Crawler Access (20 pts)**
| Check | Points |
|-------|--------|
| robots.txt exists | +5 |
| No AI crawlers blocked (empty `blocked` list) | +10 |
| At least one AI crawler explicitly allowed | +5 |

**AI Readability Files (20 pts)**
| Check | Points |
|-------|--------|
| llms.txt exists and follows spec | +10 |
| llms.txt has links to detailed content | +5 |
| agents-brief.txt exists (only if site has APIs/ecommerce) | +5 |

**Structured Data (25 pts)**
| Check | Points |
|-------|--------|
| Any JSON-LD present on homepage | +5 |
| Organization or WebSite schema | +5 |
| LocalBusiness, Service, or Product schema | +5 |
| FAQPage schema | +5 |
| Multiple schema types found across site | +5 |

**Content Accessibility (20 pts)**
| Check | Points |
|-------|--------|
| Homepage has substantial content (>500 chars) | +8 |
| Semantic HTML used (≥3 semantic tags) | +4 |
| Meta description present (>50 chars) | +4 |
| Title tag present and descriptive (>10 chars) | +4 |

**Technical Foundation (15 pts)**
| Check | Points |
|-------|--------|
| Sitemap exists | +5 |
| No anti-bot blocks on homepage | +5 |
| No cookie consent wall hiding content | +5 |

**Total: 100 points**

Grade scale:
| Score | Grade | Meaning |
|-------|-------|---------|
| 90–100 | A+ | Elite — AI agents can fully read and cite this site |
| 80–89 | A | Strong — minor gaps to close |
| 70–79 | B | Good — appears for some queries |
| 60–69 | C | Moderate — significant room for improvement |
| 50–59 | D | Weak — rarely cited by AI |
| 0–49 | F | Invisible — AI agents cannot effectively read this site |

### Step 4: Generate Files

Based on what's missing, generate the appropriate files. **Always explain what each file does and where to place it before generating it.**

**Important — two types of deliverables:**

| Type | Files | Deployment | Effort |
|------|-------|-----------|--------|
| **Drop-in files** | robots.txt, llms.txt, agents-brief.txt | Upload to domain root, done | Zero code changes |
| **Code-embedded** | JSON-LD / structured data | Requires editing site HTML templates | Needs dev work |

Explain this distinction clearly to the user. The .txt files are ready to upload. The JSON-LD is a template they (or their developer) need to embed into their site's codebase.

#### robots.txt

Generate if: missing, or AI crawlers are blocked, or no AI-specific rules exist.

Template structure:
```
# robots.txt for [domain]
# Generated by AEO Toolkit

# Standard crawlers
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

# AI training crawlers
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: CCBot
Allow: /

User-agent: Bytespider
Allow: /

# AI search/indexing crawlers
User-agent: ChatGPT-User
Allow: /

User-agent: Claude-User
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

# Sitemap
Sitemap: https://[domain]/sitemap.xml
```

**Rules:**
- Include ALL AI crawlers from the crawl output's `ai_crawler_summary.not_configured` list
- If the existing robots.txt blocks specific paths, preserve those blocks
- If the user wants to block certain AI crawlers, respect that and add Disallow rules
- Always include the sitemap reference if one exists
- Place at domain root: `https://example.com/robots.txt`

#### llms.txt

Generate if: missing or doesn't follow spec.

**Use the audit data to pre-fill the template:**
- Homepage title → H1 heading
- Meta description → blockquote summary
- Discovered pages from sitemap → H2 sections with links
- Schema types found → inform which sections to include

Template structure:
```markdown
# [Site Name from homepage title]

> [Meta description or a 1-2 sentence summary of what the site does]

## Overview
[Brief description of the company/product based on homepage content]

## Pages
- [Page title]([URL]): [What this page covers]
- [Page title]([URL]): [What this page covers]

## Services / Products
[Only if the site has services or products — generate from discovered content]

## Contact
[If contact info found in the crawl, include it here]
```

**Rules:**
- Follow the llmstxt.org spec: H1 heading (required), blockquote summary, H2 sections with links
- Pre-fill with real URLs discovered from the sitemap
- Use absolute HTTPS URLs for all links
- Include `[PLACEHOLDER: ...]` markers for information the audit couldn't determine (business description, specific service details, etc.)
- Place at domain root: `https://example.com/llms.txt`

#### JSON-LD / Structured Data

Generate if: no JSON-LD on the homepage, or key schema types are missing.

**Generate based on what the site needs:**

For a business/LocalBusiness:
```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "[Business Name]",
  "description": "[from meta description]",
  "url": "[homepage URL]",
  "telephone": "[PLACEHOLDER: phone number]",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "[PLACEHOLDER]",
    "addressLocality": "[PLACEHOLDER]",
    "addressRegion": "[PLACEHOLDER]",
    "postalCode": "[PLACEHOLDER]",
    "addressCountry": "[PLACEHOLDER]"
  },
  "openingHours": "[PLACEHOLDER: e.g. Mo-Fr 09:00-17:00]",
  "priceRange": "[PLACEHOLDER: e.g. $$]"
}
```

For a FAQ section:
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "[PLACEHOLDER: common question 1]",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[PLACEHOLDER: answer]"
      }
    }
  ]
}
```

For Organization:
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "[Site Name]",
  "url": "[homepage URL]",
  "logo": "[PLACEHOLDER: logo URL]",
  "sameAs": [
    "[PLACEHOLDER: social media URLs]"
  ]
}
```

**Rules:**
- Only generate schema types that make sense for the site (don't generate LocalBusiness for a blog)
- Use `[PLACEHOLDER: description]` for anything the audit couldn't determine
- Explain where to place JSON-LD: inside `<script type="application/ld+json">` in the `<head>` section
- If multiple schema types are needed, they can go in separate `<script>` tags or combined in one

#### agents-brief.txt

**Only generate if ALL of these are true:**
1. The file doesn't exist
2. The audit found API endpoints OR e-commerce/interactive patterns
3. The site has functionality an AI agent could act on (booking, purchasing, form submission)

If the site is a simple brochure/blog, **skip this** and explain it's not needed.

Template structure:
```
# Agent Brief for [domain]

## Permissions
# Define what actions AI agents can perform
[allowed]
browse = public pages
search = site search

[forbidden]
purchase = requires human confirmation
submit-forms = requires human confirmation

## Authentication
# If API auth is needed
[PLACEHOLDER: auth method if detected, or "none required for public endpoints"]

## API Endpoints
[If endpoints were discovered in the crawl, list them]
GET /api/... — [PLACEHOLDER: description]

## MCP / A2A
# If MCP or A2A endpoints exist
[PLACEHOLDER: none detected]
```

Place at domain root: `https://example.com/agents-brief.txt`

### Step 5: Present the Report

Structure the output as a clear, actionable report:

```
## AEO Audit: [domain]

**Score: [X]/100 — Grade [A+ through F]**

### Findings

**🔴 Critical** (fixing these will have the biggest impact)
- [Issue 1]
- [Issue 2]

**🟡 Important** (significant improvements)
- [Issue 1]
- [Issue 2]

**🟢 Nice to Have** (minor improvements)
- [Issue 1]

### Agent-Hostile Patterns Detected
| Pattern | Status | Detail |
|---------|--------|--------|
| JS rendering | ✅/🔴 | [What was found] |
| Cookie consent wall | ✅/🔴 | [What was found] |
| Anti-bot protection | ✅/🔴 | [What was found] |
| Semantic HTML | ✅/🟡 | [What was found] |
| Sitemap | ✅/🔴 | [What was found] |
| Content in iframes | ✅/🔴 | [What was found] |
| Auth/paywall | ✅/🔴 | [What was found] |
| Canonical consistency | ✅/🟡 | [What was found] |

### Score Breakdown
| Dimension | Score | Max | Notes |
|-----------|-------|-----|-------|
| AI Crawler Access | [X] | 20 | [brief note] |
| AI Readability Files | [X] | 20 | [brief note] |
| Structured Data | [X] | 25 | [brief note] |
| Content Accessibility | [X] | 20 | [brief note] |
| Technical Foundation | [X] | 15 | [brief note] |
| **Total** | **[X]** | **100** | |

### Files to Generate
- `robots.txt` — [drop-in: upload to domain root]
- `llms.txt` — [drop-in: upload to domain root]
- JSON-LD: [types] — [code-embedded: add to HTML template]
- `agents-brief.txt` — [drop-in: upload to domain root, only if site has APIs/ecommerce]

### Next Steps
1. [Upload drop-in files to server]
2. [Embed JSON-LD into site templates]
3. [Fill in placeholders]
4. [Re-audit after changes]
```

**Rules for the report:**
- Be specific, not generic. Reference actual findings from the crawl data
- Prioritise by impact: AI crawler blocks > JS rendering > missing structured data > missing files
- Explain WHY each finding matters in plain language
- Include concrete next steps
- If the site scored A or above, say so — don't manufacture problems
- Always include the score breakdown table showing points earned vs max per dimension
- Include the agent-hostile patterns table with status for each pattern checked

## Agent-Hostile Patterns Reference

When detecting these patterns, explain what they mean and what to do:

| Pattern | What It Means | Fix |
|---------|--------------|-----|
| JS-rendered (empty body) | AI agents see a blank page — no content to cite | Add SSR/SSG for key pages (Next.js, Astro, Remix) |
| Cookie consent wall | Content hidden behind "Accept cookies" overlay | Ensure critical content renders above the cookie banner, or use server-side consent detection |
| Anti-bot protection | Site actively blocks automated requests (Cloudflare, CAPTCHA) | Whitelist AI crawler user-agents, or ensure critical pages don't have bot protection |
| No semantic HTML | Agent can parse text but can't understand page structure | Use `<header>`, `<main>`, `<article>`, `<nav>`, `<footer>` tags |
| No sitemap | Agent can't discover pages beyond the homepage | Add `sitemap.xml` at domain root |
| Content in iframes | Content loaded from external sources isn't in the main DOM | Move critical content into the main HTML, avoid iframes for important content |
| Missing structured data | Agent can read text but can't understand entities (business, products, FAQs) | Add JSON-LD schema markup |
| Auth/paywall wall | Agent can't access protected content | Ensure public pages are truly public; consider providing an API for agent access |

## Re-Audit

After the user implements changes, re-run the crawl and show the score improvement:

```bash
python3 scripts/aeo-crawl.py "https://example.com"
```

Compare the new score to the original and highlight what improved.

## Security

- Always validate URLs: must start with `http://` or `https://`
- Never interpolate user input into shell commands
- The script rejects URLs containing `;`, `|`, `&`, `$`, backticks, parentheses, braces, angle brackets, or newlines
- Respect robots.txt — the script follows the site's own rules
- Rate-limit: add a 1-second delay between requests for large site crawls
