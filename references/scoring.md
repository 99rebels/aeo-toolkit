# Scoring Methodology

Full point breakdown for the 100-point AEO visibility score.

## Dimensions

```
AI Crawler Access     (20 pts)  — robots.txt AI crawler directives
AI Readability Files  (20 pts)  — llms.txt, agents-brief.txt
Structured Data       (25 pts)  — JSON-LD / schema markup
Content Accessibility (20 pts)  — semantic HTML, meta tags, content
Technical Foundation  (15 pts)  — sitemap, anti-bot, cookie walls
```

## Point Breakdown

### AI Crawler Access (20 pts)

```
robots.txt exists                          +5
No AI crawlers blocked                     +10
At least one AI crawler explicitly allowed +5
```

AI crawlers checked: GPTBot, ChatGPT-User, OAI-SearchBot, ClaudeBot, Claude-User, Claude-SearchBot, Google-Extended, PerplexityBot, Bytespider, CCBot, FacebookBot, Applebot-Extended, TiktokBot.

### AI Readability Files (20 pts)

```
llms.txt exists and follows spec (has H1)  +10
llms.txt has links to detailed content      +5
agents-brief.txt exists (only if site has
  APIs / e-commerce / interactive features) +5
```

### Structured Data (25 pts)

```
Any JSON-LD present on homepage                    +5
Organization or WebSite schema                     +5
LocalBusiness, Service, or Product schema          +5
FAQPage schema                                     +5
Multiple schema types found across site            +5
```

### Content Accessibility (20 pts)

```
Homepage has substantial content (>500 chars)  +8
Semantic HTML used (≥3 of 7 semantic tags)     +4
Meta description present (>50 chars)           +4
Title tag present and descriptive (>10 chars)   +4
```

Semantic tags checked: header, main, article, nav, footer, section, aside.

### Technical Foundation (15 pts)

```
Sitemap exists                           +5
No anti-bot blocks on homepage           +5
No cookie consent wall hiding content    +5
```

## Grade Scale

```
90–100  A+  Elite — AI agents can fully read and cite this site
80–89   A   Strong — minor gaps to close
70–79   B   Good — appears for some queries
60–69   C   Moderate — significant room for improvement
50–59   D   Weak — rarely cited by AI
0–49    F   Invisible — AI agents cannot effectively read this site
```
