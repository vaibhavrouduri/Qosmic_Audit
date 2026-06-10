---
name: storefront-artifact-collection
description: Use this skill when building or running a browser-based crawler that collects artifacts from a Shopify storefront for a CRO audit.
---

# Storefront Artifact Collection Skill

## Purpose

Collect enough reliable storefront evidence for a downstream audit agent to reason about CRO opportunities.

This skill is only for artifact collection. Do not generate audit recommendations, experiments, executive summaries, or competitor analysis in this phase.

## Input

The crawler receives exactly one storefront URL.

The crawler should normalize URLs so both forms work:

```text
example.com
https://example.com
```

## Output

Create a crawl output folder containing machine-readable and human-reviewable artifacts.

Minimum expected outputs:

```text
artifacts/
  <run-folder>/
    manifest.json
    screenshots/
    html/
    text/
    raw/
```

Use a per-run folder so different stores and runs do not overwrite each other.

## Crawl surfaces

Collect artifacts from a representative set of storefront surfaces.

Required or preferred surfaces:

1. Homepage
2. Product pages
3. Collection or category pages
4. Cart
5. FAQ page, if found
6. Shipping page, if found
7. Returns page, if found
8. Contact page, if found
9. Where To Buy or store locator page, if found
10. Blog, recipe, guide, or content page, if found
11. Technical endpoints: `robots.txt`, `sitemap.xml`, and common sitemap variants

Do not require the user to manually provide these pages. Discover them from navigation links, sitemap endpoints, Shopify JSON endpoints, rendered links, and common Shopify/storefront URL patterns.

## Page discovery strategy

Start with:

* normalized homepage URL
* `/cart`
* `/robots.txt`
* `/sitemap.xml`
* `/sitemap_index.xml`
* `/products.json`
* `/collections.json`

From rendered pages, extract internal links and classify them as:

* homepage
* product
* collection/category
* cart
* FAQ/help/shipping/returns/contact
* Where To Buy/store locator
* blog/recipe/guide/content
* other

Select a small representative set rather than crawling the entire site.

Suggested limits:

* homepage: 1
* product pages: 3 to 5
* collection/category pages: 1 to 3
* cart: 1
* key content pages: 2 to 5
* technical endpoints: all required checks
* total rendered pages: roughly 10 to 20

## Browser capture requirements

Use Playwright where possible.

For each rendered page, save:

* final URL
* HTTP response status if available
* page title
* meta description
* rendered HTML
* visible text
* desktop screenshot
* mobile screenshot
* internal links
* external links
* button/CTA text
* forms detected
* product signals
* collection/category signals
* obvious buying-path signals

Desktop viewport suggestion:

```text
1440 x 1200
```

Mobile viewport suggestion:

```text
390 x 844
```

Use full-page screenshots unless the page is extremely long or capture fails.

## Useful product signals

For product-like pages, detect whether the page appears to contain:

* product title
* price
* compare-at price or discount
* add-to-cart button
* buy button
* subscription option
* variant selector
* reviews or ratings
* shipping or returns info
* stock/availability
* retailer handoff
* quantity selector
* bundle/upsell/cross-sell modules
* trust badges or guarantees

## Useful collection/category signals

For collection-like pages, detect whether the page appears to contain:

* product grid
* filters
* sorting
* category copy
* product cards
* price visibility
* review visibility
* quick add
* need/use-case navigation
* empty or broken category state

## Useful content-page signals

For FAQ, Where To Buy, blog, recipe, guide, and other content pages, detect:

* whether the page answers a high-intent shopper question
* whether products are linked from the content
* whether there are calls to action
* whether buying or store-locator paths are visible
* whether the page appears stale, empty, broken, or thin

## Technical endpoint checks

Collect and record:

* SSL/HTTPS behavior
* HTTPS redirect behavior
* robots.txt status and body path
* sitemap status and body path
* homepage status
* cart status
* product page status
* collection page status
* broken internal links sampled during crawl
* meta title and description presence
* structured data presence
* favicon presence
* cookie/privacy link presence
* checkout/cart reachability
* image count and obvious missing alt text where easy to detect
* rough page load timing

Do not overclaim page speed unless Lighthouse or a browser timing measurement was actually run.

## Manifest requirements

Write a `manifest.json` that summarizes the crawl.

Include:

* input URL
* normalized URL
* crawl timestamp
* run folder
* page count
* selected pages
* skipped or failed pages
* technical checks
* limits/known gaps

For each page entry, include:

* surface type
* URL
* final URL
* status
* title
* meta description
* screenshot paths
* HTML path
* text path
* raw path if available
* internal links
* external links
* CTA/button text
* forms detected
* product signals
* collection signals
* content signals
* errors or blocking details

## Handling blocked pages

If a page is blocked, challenged, or returns 403/404/5xx:

* save the response or screenshot if possible
* record the status clearly
* do not invent page content
* do not treat the blocked page as normal storefront evidence
* record the limitation in the manifest

Blocked pages are useful for technical checks, but they are not enough for CRO recommendations unless corroborated by other artifacts.

## Guardrails

* Do not write the final audit report during artifact collection.
* Do not create proposed experiments in the crawler.
* Do not copy findings from `REFERENCE_REPORT.md`.
* Do not hardcode store-specific URLs beyond common storefront patterns.
* Do not require manual page lists.
* Keep the crawler bounded and fast.
* Prefer clear artifacts over clever inference.
