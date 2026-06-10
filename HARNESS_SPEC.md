# HARNESS_SPEC.md

## Objective

Build a runtime harness that turns one Shopify storefront URL into an artifact-backed CRO audit report.

The harness should guide a coding agent through artifact collection, artifact-backed reasoning, and merchant-facing report generation.

The harness must generalize across Shopify stores. It must not rely on store-specific shortcuts or hardcoded findings.

## Input contract

The system accepts one Shopify storefront URL as input.

No manual page list, competitor list, screenshots, analytics exports, or extra configuration should be required.

## Output contract

The system produces one Markdown or HTML audit report.

The report should be written to `sample_output/` or another explicit output path provided by the harness.

The report must contain exactly these sections:

1. Executive summary
2. Proposed experiments
3. Competitor analysis
4. Technical checks

## Executive summary

Write 2 to 3 concise paragraphs.

Summarize the highest-priority visible revenue leaks based only on collected artifacts.

Do not claim access to analytics, revenue, conversion rate, heatmaps, customer data, or internal merchant metrics unless those were explicitly collected as artifacts.

## Proposed experiments

Include exactly 10 proposed experiments.

Each experiment must include:

- Title and experiment ID
- Pillar
- Affected surface and URL
- Evidence
- Hypothesis
- Primary change
- Primary KPI
- Decision rule
- Expected lift range
- Confidence %

Allowed pillars:

- Conversion
- AOV
- Retention
- Acquisition
- Performance

The 10 experiments must span all five pillars.

Each experiment should be framed as a testable hypothesis, not a guaranteed result.

Evidence must point to a specific artifact, screenshot path, saved page artifact, manifest entry, or inspected URL.

## Competitor analysis

Include a table comparing the store to 3 to 4 relevant competitors.

The table should include:

- Competitor
- Positioning
- What the competitor makes easier
- Pattern the audited store could adapt

Competitor analysis should be relevant to the merchant's category and positioning.

If competitor sites were not crawled, the report must say so and treat this section as category-pattern benchmarking.

## Technical checks

Include around 15 standard storefront checks.

Each check must include:

- Check name
- Status: Pass, Warn, or Fail
- One-line detail

Technical checks should cover:

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

## Audit workflow

### Phase 1: Crawl

Visit the storefront and capture artifacts from representative surfaces.

Representative surfaces include:

- Homepage
- Product pages
- Collection or category pages
- Cart or purchase handoff route
- FAQ, shipping, returns, contact, Where To Buy, blog, recipe, guide, or other key content pages when present
- Technical endpoints such as robots.txt and sitemap.xml

Artifacts should include, where possible:

- Final URL
- HTTP status
- Page title
- Meta description
- Visible text
- HTML
- Screenshot paths
- Internal links
- Button or CTA text
- Product or collection signals
- Technical check results

### Phase 2: Reason

Use collected artifacts to identify likely opportunities across:

- Conversion
- AOV
- Retention
- Acquisition
- Performance

Reasoning must be evidence-backed.

Do not speculate without an artifact. If a claim cannot be tied to a screenshot, saved page artifact, manifest entry, or inspected URL, do not include it.

Confidence scores and lift ranges are heuristic estimates. They should reflect evidence strength, affected-surface importance, CRO pattern strength, implementation clarity, and risk. They are not claims of known statistical truth.

### Phase 3: Write

Produce the structured audit report using the required report format.

The report should be specific to the audited store, concise, merchant-useful, and grounded in artifacts.

## Quality rules

- Every meaningful claim must tie to a specific artifact, screenshot path, manifest entry, or inspected URL.
- Do not hardcode findings, products, competitors, screenshots, or recommendations for a specific store.
- Do not copy merchant-specific claims, competitors, products, URLs, experiments, evidence paths, expected lifts, confidence scores, or wording from the reference report.
- Avoid unsupported claims about customer behavior, sales impact, conversion rates, or internal business performance.
- If pages are blocked, unavailable, slow, or only partially inspected, reflect that uncertainty in the report.
