---
name: company-research-report
description: Generate structured corporate research reports by searching public information across web, e-commerce platforms, social media, and financial databases. Use when the user asks for a company research report, market analysis, due diligence summary, or competitive analysis of a specific company.
---

# Company Research Report Generator

Generate structured, source-backed corporate research reports using the template at `assets/report-template.md`.

## Workflow

### 1. Read the Template

Load `assets/report-template.md` to understand the full structure. The template contains 13 chapters covering:

1. Basic info — 2. History — 3. Products — 4. Tech/IP — 5. Funding/Equity — 6. Market performance — 7. Marketing analysis — 8. Team — 9. Competition — 10. Strategy — 11. AI integration — 12. Risk — 13. Summary

### 2. Research

Search for the company across multiple channels. Prioritize:

- **Official sources** - corporate website, official news, IR filings if public
- **Business registries** - Qichacha (qcc.com), Tianyancha, Qixinbao for equity, registration, legal
- **Funding/VC databases** - 36kr, Qimingpian for funding rounds, investors, valuations
- **E-commerce** - JD.com, Tmall/Taobao for reviews, rankings, price points
- **Social/Content** - Xiaohongshu, Bilibili, YouTube, Douyin for brand sentiment, content strategy
- **Industry data** - AVC (奥维云网), Fortune Business Insights, industry association reports for market benchmarks
- **Financial media** - 36kr, East Money, CBN for industry context

### 3. Data Quality Rules

- **Exact figures** (registered capital, shareholding %, founding date) need at least one authoritative source (business registry or verified news article).
- **Sales/GMV estimates** must be explicitly labeled as estimates with methodology explained (e.g., review-count × assumed review-rate).
- **Leadership quotes** need source attribution.
- **Industry statistics** need source attribution (e.g., "AVC" / "Fortune Business Insights").
- **Cross-reference**: Verify key data points across at least 2 independent sources when possible. Flag single-source data explicitly.
- When exact data is unavailable from public channels, clearly state that limitation and offer the best available proxy.

### 4. Fill the Template

Replace each `{{PLACEHOLDER}}` with researched content. Do NOT leave placeholders empty. If a section is genuinely not applicable, explain why briefly instead of deleting it.

### 5. Equity Structure Penetration

For Chapter 5, when equity data is available, do a deep penetration analysis:

- Trace upstream shareholders to identify ultimate controlling parties
- Identify whether the company is part of a larger ecosystem (e.g., XbotPark, Tencent ecosystem, Xiaomi ecosystem)
- Map co-investment relationships and syndicate patterns
- Analyze founder control vs investor influence balance
- Flag state-owned capital, SOE, or government-guided fund involvement

### 6. Marketing Analysis

For Chapter 7, analyze the full DTC funnel. Look for:

- Social media strategy (Xiaohongshu, Douyin, Instagram)
- KOL/KOC matrix structure
- Content themes and emotional positioning
- Platform-specific viral mechanics
- PR and media coverage patterns
- Pricing strategy relative to competitors
- Cross-border/international marketing signals

### 7. AI Integration Analysis

For Chapter 11, map the industry's AI maturity using an L1-L5 smart-device ladder framework. Analyze:

- Current AI maturity level of the target company vs competitors
- Perception layer (sensors, computer vision, NLP) capabilities
- Decision layer (recommendation engines, adaptive algorithms)
- Execution layer (robotics, automation, autonomous operations)
- Cross-industry applicability of the company's AI stack

### 8. Final Output

Write the completed report to the user's workspace. Use the filename format `{{BRAND_NAME}}-市场调研报告.md`.
