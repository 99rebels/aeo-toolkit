# Agent-Hostile Patterns

Patterns that make websites difficult or impossible for AI agents to read. The crawl script detects all of these automatically.

## Detection & Fixes

```
🔴 JS rendering         → Body content <500 chars
                           Fix: Add SSR/SSG (Next.js, Astro, Remix)

🔴 Cookie consent wall   → Cookie banner class/id patterns detected
                           Fix: Render critical content above banner,
                                or use server-side consent detection

🔴 Anti-bot protection   → Cloudflare/CAPTCHA/403 responses
                           Fix: Whitelist AI crawler user-agents,
                                ensure critical pages don't have bot protection

🟡 No semantic HTML      → <1 of 7 semantic tags used
                           Fix: Use <header>, <main>, <article>,
                                <nav>, <footer>, <section>, <aside>

🔴 No sitemap            → /sitemap.xml returns 404
                           Fix: Add sitemap.xml at domain root

🔴 Content in iframes    → Iframes found with external sources
                           Fix: Move critical content into main HTML

🟡 Canonical mismatch    → agensi.io vs www.agensi.io inconsistency
                           Fix: Set consistent canonical URL, add 301 redirect

🟡 Auth/paywall          → HTTP 401/402 or login form detected
                           Fix: Ensure public pages are truly public;
                                consider API access for agents
```

## Semantic Tags Checked

```
<header>  <main>  <article>  <nav>  <footer>  <section>  <aside>
```

A site needs ≥3 of these to pass the semantic HTML check.

## API Pattern Detection

The crawl looks for URLs matching these patterns:

```
/api/    /v\d+/    /rest/    /graphql
.json    /webhook  /oauth    /auth/
/checkout  /booking  /payment  /subscribe
```

Discovered endpoints are used to determine if agents-brief.txt is relevant.
