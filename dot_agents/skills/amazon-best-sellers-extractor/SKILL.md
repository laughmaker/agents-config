---
name: amazon-best-sellers-extractor
description: Extract Amazon Best Sellers category pages into Excel, especially two-page top-100 lists. Use when the user asks to obtain Amazon Best Sellers products, add product URLs, resolve exact brands from product pages, count brand occurrences, or build an Excel workbook with a brand chart.
---

# Amazon Best Sellers Extractor
## Core Workflow
Use this skill to turn an Amazon Best Sellers category into a verified Excel workbook. The common target is a top-100 list split across `pg=1` and `pg=2`, 50 products per page.

Prefer the repository's web priority: Exa for simple public lookup, Dia when login or the user's loaded page matters, then in-app browser, then computer use. For Amazon pages that are already fully loaded in the user's browser, use the browser state the user provided instead of re-fetching from scratch.

## Workbook Requirements
Create or update an `.xlsx` in the user's requested folder, usually `amazon/`.

Use a `Best Sellers` sheet with these columns:

```text
rank, page, asin, brand, title, rating, review_count, price, product_url
```

Add a `Brand Summary` sheet with one row per brand and occurrence count. Include a horizontal bar chart showing brand counts. If the workbook is research-facing, include a notes or data说明 sheet that states:

- Amazon marketplace and category URL
- 榜单类型: Best Sellers
- category node or category name
- collection date
- update method
- reliability limits, including that Best Sellers pages and product detail pages can change

## Capture Best Sellers Pages
1. Start from `pg=1`, not `pg=2`.
2. Confirm all 50 products are loaded before extraction.
3. Extract rank, title, rating, review count, price, URL, and ASIN when available.
4. Move to `pg=2` only after page 1 is complete, then extract ranks 51-100.
5. Normalize product URLs to `https://www.amazon.com/dp/<ASIN>` when ASIN is available.
6. Verify exactly 100 rows unless the page itself visibly has fewer.

If browser DOM extraction misses products, use the user's full-page screenshots as a fallback for visible fields, but still resolve URLs and brands from product pages when possible.

## Resolve Exact Brands
Do not trust a guessed brand just because it appeared in the title, app-compatibility wording, or an earlier scrape. Treat `Generic`, blank, title-guessed, and suspicious carry-over brands as unresolved. Examples of suspicious values include:

- a platform or ecosystem name such as `Google`
- a competing brand copied from nearby products
- a normalized name that does not match Amazon's visible item details

Audit all brands when quality matters, not only `Generic` rows. If the workbook already exists, compare every stored brand against the Amazon product detail page and overwrite any mismatch with the exact Amazon-visible brand.

For each unresolved or suspicious product URL, open the product detail page and resolve brand using this priority:

1. Product information or item details table row where the label is `Brand` or `Brand Name`
2. Byline text such as `Visit the X Store`
3. Text patterns such as `Brand: X`
4. If Amazon shows no brand after checking the page, keep the best evidence-backed value and note the uncertainty

Useful product page targets in browser automation:

```text
#bylineInfo
#productOverview_feature_div
```

When extracting from page text:

- preserve Amazon's exact capitalization where visible, including unusual marketplace seller-style brands
- prefer the table value over title wording, even when the title contains terms like `Google`, `Android`, `Apple`, `Find My`, or another well-known brand string
- if both `Brand` and `Brand Name` appear, either is acceptable evidence as long as the value matches

## Verification Checklist
Before final handoff, run workbook checks:

- `Best Sellers` has 100 rows for a two-page top-100 capture.
- ranks are complete and unique from 1 to 100.
- every row has a product URL.
- `brand` has zero blanks.
- `brand` has zero `Generic` values unless the exact Amazon product page truly says the brand is Generic.
- `brand` does not contain title-derived placeholder values contradicted by the product detail page.
- any existing workbook brands have been audited against live product pages when the user asked for correction or exact brands.
- `Brand Summary` counts match the `Best Sellers` brand column.
- the chart in `Brand Summary` reflects the updated counts.

Report the final workbook path and the remaining unresolved brand count. If any unresolved rows remain, list their ranks and URLs instead of implying the workbook is complete.
