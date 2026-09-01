# Workflow

## Standard workbook pattern

Most Amazon BSR workbooks in this workflow follow this raw layout:

- `Notes`
- `Best Sellers`
- `Brand Summary`

Common raw fields:

- `rank`
- `page`
- `asin`
- `brand`
- `title`
- `rating`
- `review_count`
- `price`
- `product_url`

## Standard execution sequence

1. Read the workbook structure.
2. Sample the first rows of `Best Sellers`.
3. Detect shelf pollution.
4. Create a cleaned subset sheet.
5. Build brand analysis.
6. Build price-band analysis.
7. Build selling-point analysis from title-visible claims.
8. Build a category-specific strategy sheet.
9. Build review insights or hypothesis notes.
10. Export `*-with-analysis.xlsx`.
11. If needed, add `Summary`.
12. Export `*-with-summary.xlsx`.

## Analysis sheet goals

### `Core ... Subset`

Purpose:
- Keep a full row-by-row cleaning view
- Show which rows stay in the core subset
- Preserve transparent inclusion logic

Typical columns:
- raw identifiers
- cleaned type
- include/exclude flag
- numeric normalization
- feature flags

### `Brand Analysis`

Purpose:
- Measure review moat, listing breadth, and front-page presence

Useful fields:
- core listings
- top20 listings
- total visible reviews
- average price
- average rating
- category-specific feature counts

### `Price Analysis`

Purpose:
- Find the commercial center of the shelf
- Show how premium tiers differ from mass-market tiers

Typical outputs:
- listing count by band
- total visible reviews by band
- median rating
- median review count
- top20 presence

### `Selling Points`

Purpose:
- Turn title claims into structured demand signals

Typical outputs:
- feature frequency
- top20 feature frequency
- short interpretation panel

### Category-specific fifth sheet

Purpose:
- Reflect the category's real strategic tension

Examples:
- trackers: no-fee vs subscription
- bark collars: correction method
- training collars: remote complexity, range, stimulation modes

### `Review Insights`

Purpose:
- Tie the shelf structure to likely pain points and opportunity zones

If review workbook exists:
- extract themes from review text

If review workbook does not exist:
- make hypothesis-driven notes
- explicitly label the limitation

### `Summary`

Purpose:
- Give a one-page decision surface

Recommended blocks:
- KPI cards
- `Snapshot`
- `Key Conclusions`
- `What To Watch`
- `Caveats`

## Naming rules

Use stable output names:

- `original-name-with-analysis.xlsx`
- `original-name-with-summary.xlsx`

Keep new analysis tabs explicit and readable.
Avoid vague names like `Sheet2`, `Final`, or `copy`.
