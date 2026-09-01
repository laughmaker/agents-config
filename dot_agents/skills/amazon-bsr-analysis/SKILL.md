---
name: amazon-bsr-analysis
description: "Analyze Amazon Best Sellers category workbooks and turn raw BSR exports into category insights. Use when Codex is given an Amazon BSR `.xlsx` workbook and needs to: (1) inspect the sheet structure, (2) clean a true core subset from a polluted category shelf, (3) add new analysis sheets without modifying raw data sheets, (4) summarize brand concentration, price bands, selling points, and a category-specific business/model lens, or (5) compress the detailed analysis into a one-page Summary tab."
---

# Amazon BSR Analysis

## Overview

Use this skill for workbook-first Amazon category analysis.
Preserve the raw workbook tabs, add new analysis tabs, and separate facts from inferences.

Read [references/workflow.md](references/workflow.md) before starting.
Read [references/category-patterns.md](references/category-patterns.md) when the category is mixed or the fifth analysis sheet needs a category-specific lens.

## Core workflow

1. Inspect the workbook first.
   Confirm sheet names, row count, key fields, and obvious parsing issues.
   Expect the raw workbook to usually contain `Notes`, `Best Sellers`, and `Brand Summary`.

2. Define the cleaned core subset before interpreting the category.
   Do not assume the BSR shelf is clean.
   Remove obvious non-core items such as accessories, refill SKUs, scanners, alternate device types, or remote-control products that distort the target category.

3. Preserve raw sheets.
   Never modify `Notes`, `Best Sellers`, `Brand Summary`, or equivalent source tabs.
   Create new sheets for every cleaning or analysis step.

4. Build the detailed analysis tabs.
   Default pattern:
   - `Core ... Subset`
   - `Brand Analysis`
   - `Price Analysis`
   - `Selling Points`
   - category-specific fifth sheet
   - `Review Insights`

5. Choose the fifth sheet to match the category.
   Examples:
   - pet location trackers: `Business Model`
   - bark collars: `Training Mode`
   If the category's main strategic tension is not recurring revenue, do not force a subscription analysis.

6. Use review evidence when available.
   If a local raw review workbook exists, use it for pain points and positive signals.
   If no review workbook exists, say so clearly and downgrade `Review Insights` to hypothesis-driven category notes.

7. Add a one-page `Summary` sheet when the user wants an executive view.
   Compress the detailed sheets into:
   - KPI cards
   - `Snapshot`
   - `Key Conclusions`
   - `What To Watch`
   - `Caveats`

8. Validate visually before delivery.
   Render the added tabs and check for clipped text, broken tables, empty sections, and obvious range mistakes.

## Required rules

- Keep raw sheets untouched.
- Put cleaning logic in new tabs, not in overwritten raw columns.
- Keep conclusions scoped to Amazon-visible evidence unless the user explicitly broadens scope.
- Distinguish facts, heuristics, and hypotheses.
- Call out category pollution whenever the raw BSR shelf mixes product types.
- Prefer new output files such as `*-with-analysis.xlsx` and `*-with-summary.xlsx` instead of overwriting the source workbook.

## Default deliverables

Deliver at least one of these, depending on the ask:

- `*-with-analysis.xlsx`
- `*-with-summary.xlsx`

If both are requested, create the analysis workbook first, then derive the summary workbook from it.

## Trigger phrases

This skill is a good fit for prompts like:

- "same method analysis this sheet"
- "analyze this Amazon BSR workbook"
- "clean Top100 into the core subset"
- "add analysis sheets but don't modify raw data"
- "compress it into one Summary page"
- "do the same for another Amazon best sellers sheet"
