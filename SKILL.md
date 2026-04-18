---
name: aeo-toolkit
description: >-
  Audit any website's visibility to AI agents and generate every file needed
  to fix it. Detects JS rendering gaps, missing structured data, blocked AI
  crawlers, cookie consent walls, anti-bot protections, and more. Generates
  robots.txt, llms.txt, JSON-LD templates, and agents-brief.txt.
homepage: https://github.com/99rebels/aeo-toolkit
allowed-tools:
  - Bash(python3 *)
  - Read
  - Write(*.txt)
  - Write(*.json)
  - Write(*.md)
  - Write(*.html)
---

# 🔍 AEO Toolkit

**Audit any website's AI agent visibility. Get a score, a report, and every file needed to fix it.**

## Why

Websites are increasingly invisible to AI agents — not because agents can't find them, but because sites are built in ways agents can't read. JS rendering, missing structured data, blocked AI crawlers, and no machine-readable descriptions mean ChatGPT, Claude, and Perplexity can't cite or recommend your business.

This skill detects the problems and generates the fixes. No external dependencies — pure Python.

## When to Use

- "Audit my site for AI visibility"
- "Why doesn't my business show up in ChatGPT / Claude / Perplexity?"
- "Check if AI agents can read my website"
- "Generate llms.txt / robots.txt / structured data"
- "AEO audit", "GEO audit", "AI search optimization"
- "Make my site visible to AI agents"

## Quick Start

```bash
python3 scripts/aeo-crawl.py "https://example.com"
```

The default crawls the homepage + essential files + up to 10 pages from the sitemap.

```
# Homepage only (fastest)
python3 scripts/aeo-crawl.py "https://example.com" --max-pages 1

# Deep crawl
python3 scripts/aeo-crawl.py "https://example.com" --max-pages 50

# All pages (slow — small sites only)
python3 scripts/aeo-crawl.py "https://example.com" --max-pages 0
```

**Flags:**

```
--max-pages N       Pages from sitemap (default: 10, 0 = all)
--timeout SECONDS   Per-request timeout (default: 15)
--max-bytes BYTES   Max response size (default: 512KB)
--no-ssl-verify     Skip SSL verification
```

## Audit Flow

### Step 1: Crawl

Run the script. Review the JSON output.

**Do NOT show raw JSON to the user.** Parse, analyze, and present a human-readable report.

See [references/data-fields.md](references/data-fields.md) for the full output schema.

### Step 2: Analyze

Check these sections in order of impact:

```
1. ai_crawler_summary   → Are AI crawlers blocked? (biggest impact)
2. homepage             → JS rendered? No semantic HTML? No JSON-LD?
3. aggregate            → Sitewide patterns across all pages
4. llms_txt             → Exists? Follows spec?
5. agents_brief_txt     → Exists? (only relevant for sites with APIs/ecommerce)
6. sitemap              → Exists? How many pages?
```

### Step 3: Score

Calculate a 0-100 visibility score across 5 dimensions:

```
AI Crawler Access     20 pts   → robots.txt AI crawler rules
AI Readability Files  20 pts   → llms.txt, agents-brief.txt
Structured Data       25 pts   → JSON-LD schema markup
Content Accessibility 20 pts   → semantic HTML, meta tags, content
Technical Foundation  15 pts   → sitemap, anti-bot, cookie walls
```

Full point breakdown: [references/scoring.md](references/scoring.md)

```
90–100  A+   Elite
80–89   A    Strong
70–79   B    Good
60–69   C    Moderate
50–59   D    Weak
 0–49   F    Invisible
```

### Step 4: Generate Files

Based on what's missing, generate the appropriate files.

**Two types of deliverables:**

```
📂 Drop-in files (upload to domain root, no code changes)
   robots.txt          → AI crawler directives
   llms.txt            → AI-readable site description
   agents-brief.txt    → Agent permissions (API/ecommerce sites only)

📂 Code-embedded (requires editing HTML templates)
   JSON-LD             → Structured data (schema.org markup)
```

The .txt files are ready to upload. JSON-LD templates need the user (or their dev) to embed into `<script type="application/ld+json">` tags.

Templates and rules: [references/file-templates.md](references/file-templates.md)

**agents-brief.txt is conditional** — only generate if the site has APIs, e-commerce, or interactive features. Skip for brochure/blog sites.

### Step 5: Present the Report

```
## AEO Audit: [domain]

**Score: [X]/100 — Grade [A+ through F]**

### Findings

🔴 Critical (biggest impact)
- [Issue]

🟡 Important (significant improvement)
- [Issue]

🟢 Nice to Have
- [Issue]

### Agent-Hostile Patterns
| Pattern | Status | Detail |
|---------|--------|--------|
| JS rendering | ✅/🔴 | [...] |
| Cookie wall | ✅/🔴 | [...] |
| Anti-bot | ✅/🔴 | [...] |
| Semantic HTML | ✅/🟡 | [...] |
| Sitemap | ✅/🔴 | [...] |
| Iframes | ✅/🔴 | [...] |
| Auth/paywall | ✅/🔴 | [...] |
| Canonical | ✅/🟡 | [...] |

### Score Breakdown
| Dimension | Score | Max | Notes |
|-----------|-------|-----|-------|
| AI Crawler Access | [X] | 20 | [...] |
| AI Readability Files | [X] | 20 | [...] |
| Structured Data | [X] | 25 | [...] |
| Content Accessibility | [X] | 20 | [...] |
| Technical Foundation | [X] | 15 | [...] |
| **Total** | **[X]** | **100** | |

### Files to Generate
- robots.txt — drop-in
- llms.txt — drop-in
- JSON-LD: [types] — code-embedded
- agents-brief.txt — drop-in (if applicable)

### Next Steps
1. Upload drop-in files to server
2. Embed JSON-LD into site templates
3. Fill in [PLACEHOLDER] values
4. Re-audit to verify improvements
```

**Report rules:**
- Be specific — reference actual crawl findings, not generic advice
- Prioritise: AI crawler blocks > JS rendering > missing structured data > missing files
- Explain WHY each finding matters
- If the site scored A or above, say so — don't manufacture problems

## Agent-Hostile Patterns

The crawl automatically detects 8 patterns that make sites invisible to agents:

```
🔴 JS rendering       → Empty body, agents see nothing
🔴 Cookie consent     → Content hidden behind overlay
🔴 Anti-bot           → Cloudflare/CAPTCHA blocking requests
🟡 No semantic HTML   → Agents can read but can't understand structure
🔴 No sitemap         → Agents can't discover pages
🔴 Iframes            → Content loaded externally, not in DOM
🟡 Canonical mismatch → Inconsistent domain URLs
🟡 Auth/paywall       → Protected content inaccessible
```

Full reference with detection methods and fixes: [references/agent-hostile-patterns.md](references/agent-hostile-patterns.md)

## Re-Audit

After implementing changes, re-run and compare:

```bash
python3 scripts/aeo-crawl.py "https://example.com"
```

Show the score delta and highlight what improved.

## Security

- URLs must start with `http://` or `https://`
- Shell metacharacters rejected (`;`, `|`, `&`, `$`, backticks, etc.)
- Never interpolate user input into shell commands
- Responses capped at 512KB per page
- Respects robots.txt rules
