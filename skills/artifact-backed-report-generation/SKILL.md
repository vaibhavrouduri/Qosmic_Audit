---
name: artifact-backed-report-generation
description: Generate a merchant-facing Shopify CRO audit report from collected crawl artifacts and a manifest.
---

# Artifact-Backed Report Generation

Use this skill after artifact collection is complete and a crawl `manifest.json` exists.

This skill does not crawl pages and does not modify crawler code. It turns saved storefront artifacts into a CRO audit report.

## Inputs

Expected inputs:

- `HARNESS_SPEC.md`
- `REFERENCE_REPORT.md`
- crawl `manifest.json`
- artifact files referenced by the manifest:
  - screenshots
  - text files
  - HTML files
  - raw endpoint responses

Use `REFERENCE_REPORT.md` only as a quality and structure reference. Do not copy merchant-specific claims, products, competitors, URLs, experiment ideas, evidence paths, lift ranges, confidence scores, or wording from it.

## Core rule

Every meaningful claim in the report must be grounded in one of:

- a screenshot path
- a text artifact path
- an HTML artifact path
- the manifest path
- an inspected URL from the manifest

If a claim cannot be supported by collected artifacts, do not include it.

### Screenshot evidence rule

When screenshots exist in the selected crawl run, cite relevant screenshot paths for visual or layout claims.

Aim for at least 3 screenshot citations across the report, especially for homepage, product detail page, cart/404, locator, navigation, or other visually rendered findings.

Do not cite screenshots just to satisfy a count. Use them where the screenshot strengthens the evidence for what was visibly rendered.


## Run selection rule

Use only the crawl run provided for the current audit.

The selected run is the directory containing the `manifest.json` provided by the harness or prompt.

Do not mix evidence across multiple artifact folders.

All screenshot, text, HTML, raw, and manifest paths cited in the report must come from the selected run folder.

## Workflow

### 1. Read the manifest first

Identify:

- audited store URL
- run folder
- pages captured successfully
- pages blocked or failed
- screenshot paths
- text artifact paths
- HTML artifact paths
- technical endpoint results
- known limitations

Separate evidence into:

- usable storefront evidence
- failed or blocked evidence
- technical-only evidence

Do not use failed, blocked, or 404 pages as positive storefront evidence.

### 2. Build an evidence inventory

Extract concrete observations from usable artifacts.

Look for:

- homepage positioning
- navigation paths
- product detail page buying path
- price, add-to-cart, buy, find-retailer, or store-locator behavior
- reviews, trust, guarantees, ingredients, claims, or proof
- collection/category browsing behavior
- cart or checkout reachability
- Where To Buy or retailer handoff
- FAQ, shipping, returns, and contact clarity
- blog/content paths and whether they connect to products
- newsletter or retention capture
- technical issues from the manifest

For each useful observation, preserve:

- observed fact
- affected surface
- artifact path or URL
- confidence level
- possible CRO implication

### 3. Turn observations into experiments

Create experiments only from artifact-backed observations.

Experiments must be hypotheses, not claims of proven impact.

Good:

- If PDPs make the buy/find handoff clearer, more high-intent visitors should click retailer or store-locator actions.

Bad:

- Customers are confused.
- This is killing conversion.
- Revenue will increase.

Use confidence scores and lift ranges as heuristic estimates only.

Confidence guide:

- 75-90%: directly visible issue on a high-intent surface with strong evidence
- 60-74%: visible issue with reasonable CRO pattern
- 45-59%: plausible opportunity with weaker or partial evidence
- below 45%: avoid unless needed and clearly caveated

## Output requirements

Write one Markdown report with exactly these major sections:

1. Executive summary
2. Proposed experiments
3. Competitor analysis
4. Technical checks

Do not add extra major sections unless explicitly requested.

## Executive summary

Write 2 to 3 concise paragraphs.

Make it merchant-facing, not debug-facing.

Do not claim analytics, revenue, heatmaps, conversion rates, or customer behavior data.

Keep scope limitations brief and natural.

Acceptable scope wording:

- This run did not include analytics or heatmaps, so the recommendations are framed as testable hypotheses from visible storefront evidence.

Use that only if needed.

## Proposed experiments

Include exactly 10 experiments.

Each experiment must include:

- title and experiment ID
- pillar
- affected surface and URL
- evidence
- hypothesis
- primary change
- primary KPI
- decision rule
- expected lift range
- confidence %

Allowed pillars:

- Conversion
- AOV
- Retention
- Acquisition
- Performance

The 10 experiments must span all five pillars.

Every experiment must cite at least one real artifact path or inspected URL.

Prefer crawled pages. If using an uncrawled linked page, say so and lower confidence.

## Competitor analysis

Include 3 to 4 relevant competitors.

Use a table with:

- Competitor
- Positioning
- What they make easier
- Pattern to adapt

If competitor sites were not crawled, label this as category-pattern benchmarking. Do not pretend competitor artifacts were collected.

Tie every adaptation back to the audited store’s artifacts.

## Technical checks

Include around 15 checks.

Each row must include:

- Check name
- Status: Pass, Warn, or Fail
- One-line detail

Required checks:

- SSL
- HTTPS redirect
- Sitemap
- Robots.txt
- Critical pages loading
- Meta tags
- Structured data
- Favicon
- Mobile friendliness
- Mobile page speed
- Desktop page speed
- Broken links
- Image optimization
- Cookie/privacy
- Checkout reachable

Use manifest evidence.

Do not cite a 404, blocked page, or failed page as positive proof for structured data, favicon, meta tags, or other positive technical checks.

## Final self-check

Before writing the final report, verify:

- exactly 4 major sections
- exactly 10 experiments
- all 5 pillars represented
- every experiment has all required fields
- every experiment has artifact-backed evidence
- evidence paths come from the current run
- when screenshots exist, the report cites at least 3 relevant screenshot artifact paths across visual or layout findings
- no unsupported analytics, revenue, heatmap, or conversion-rate claims
- no positive claims based on failed or blocked pages
- competitor analysis is honest about whether competitors were crawled
- technical checks are evidence-safe
- tone is merchant-facing, not debug-facing

## Calibration and quality rules

Use conservative calibration because the harness has storefront artifacts, not analytics, revenue, conversion rates, heatmaps, or experiment results.

### Expected lift range rules

Expected lift ranges must be plausible, modest, and tied to evidence strength.

Use these defaults unless there is unusually strong artifact evidence:

- Strong issue on a high-intent purchase surface: +5-12%
- Broken route, 404 recovery, or missing handoff path: +3-8%
- Navigation, merchandising, or content-routing improvement: +3-7%
- Retention or routine-building recommendation without customer data: +2-6%
- Performance or technical recommendation without Lighthouse/Core Web Vitals data: +2-6%
- Acquisition/content recommendation without search data: +3-8%

Do not use lift ranges above +15% unless the report explains why the artifact evidence is unusually strong.

Do not imply the lift is proven. Always frame it as an expected test range.

### Confidence calibration rules

Confidence must reflect evidence quality and uncertainty.

Use this scale:

- 80-90%: direct artifact evidence, low ambiguity, important surface, clear user path, and low-risk recommendation.
- 65-79%: good artifact evidence, but no behavioral analytics or some ambiguity.
- 50-64%: partial evidence, missing mobile data, blocked endpoints, indirect evidence, or technical uncertainty.
- Below 50%: weak evidence or exploratory recommendation.

Do not assign 80%+ confidence when the claim is based only on:
- a 404 page
- a missing crawler signal
- an uncrawled behavior
- a blocked endpoint
- category assumptions
- mobile or speed claims without mobile/Lighthouse artifacts

### Technical check status rules

Use Pass only when the selected crawl artifacts directly support the check.

Use Warn when:
- the check was only partially measured
- the crawler lacks the right artifact
- the status is plausible but not directly validated
- the issue may be caused by crawler limitations
- the evidence is ambiguous

Use Fail only when the selected crawl artifacts directly show a broken or missing requirement.

Examples:
- Privacy/cookie should be Warn if only a privacy-policy link is observed but no consent behavior was audited.
- HTTPS redirect should be Warn unless HTTP-to-HTTPS redirect was explicitly tested.
- Broken links should be Warn if the failed URLs look like crawler-generated malformed social/email paths.
- Checkout reachable should be Fail only if the report clearly states that no checkout route was reached in the selected crawl, not that checkout is globally impossible.
- Mobile friendliness and mobile speed should be Warn if mobile capture or Lighthouse was not run.

### Competitor analysis rules

If competitor sites were not crawled, explicitly label the section as category-pattern benchmarking.

Do not imply competitor pages were inspected unless their artifacts exist.

Competitor analysis should:
- use 3-4 relevant category competitors
- explain that competitor claims are pattern-level, not artifact-backed competitor crawl findings
- tie every suggested adaptation back to evidence from the audited store's selected crawl run
- avoid claiming competitor performance, conversion rates, pricing superiority, or traffic data

### KPI and decision-rule rules

KPIs may be proposed for future experiments, but the report must not imply the harness observed those KPIs.

Decision rules should be test-oriented and measurable.

Do not say that bounce rate, AOV, exit rate, conversion rate, revenue, or scroll depth is currently high or low unless analytics artifacts exist.

### Final quality bar

Before finishing, revise the report if any of these appear:

- expected lift range above +15% without strong justification
- confidence above 80% without direct low-ambiguity evidence
- Pass status without direct artifact support
- Fail status based on incomplete measurement
- competitor claims that sound like crawled evidence when competitors were not crawled
- KPI wording that implies current analytics access

