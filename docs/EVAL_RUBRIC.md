# Eval Rubric

The eval system judges whether a generated Shopify CRO audit report is trustworthy, useful, and grounded in the selected crawl artifacts.

## Eval inputs

- Generated report markdown file
- Selected crawl manifest JSON
- HARNESS_SPEC.md
- Report-generation skill rules

## Scoring categories

Total score: 100

### 1. Contract and structure: 20 points

Checks whether the report follows the required output contract.

- Exactly 4 required major sections
- Exactly 10 proposed experiments
- Every experiment has all required fields
- All 5 pillars are represented
- Technical checks table exists
- Competitor analysis table exists

### 2. Evidence grounding: 25 points

Checks whether report claims are backed by selected-run artifacts.

- Artifact paths must all come from the selected crawl run
- Each experiment must include evidence
- Visual/layout claims should cite screenshots
- Technical claims should cite manifest or endpoint artifacts
- Report should not use old artifacts or mixed crawl runs

### 3. Experiment usefulness: 20 points

Checks whether experiments are specific, testable, and merchant-actionable.

- Each experiment names a specific surface or URL
- Each primary change is concrete
- Each KPI is measurable
- Each decision rule is testable
- Recommendations should be store-specific, not generic CRO filler

### 4. Calibration and claim safety: 15 points

Checks whether the report is appropriately cautious.

- Warn if confidence is above 80%
- Strong warn if confidence is above 85%
- Warn if expected lift upper bound is above 12%
- Strong warn if expected lift upper bound is above 15%
- Warn on unsupported phrases like revenue leak, analytics show, heatmaps show, customers are confused, proved, guaranteed

### 5. Technical-check judgment: 10 points

Checks whether Pass/Warn/Fail statuses are evidence-safe.

- Pass only when directly verified
- Warn when blocked, partial, ambiguous, or not measured
- Fail only when directly observed broken
- Cookie/privacy should not Pass from privacy-link evidence only
- Checkout reachable should not Pass unless checkout/cart flow was actually verified
- Mobile checks should Warn when mobile capture is disabled
- Page speed should Warn without Lighthouse/Core Web Vitals

### 6. Competitor honesty: 10 points

Checks whether competitor analysis is honest and useful.

- If competitors were not crawled, report must say so
- Competitor section should not pretend artifact-backed competitor inspection
- Competitors should be category-plausible
- Adaptations should tie back to audited-store evidence

## Blocking failures

A report should fail eval if any of these occur:

- Missing required report sections
- Not exactly 10 experiments
- Missing required experiment fields
- Missing one or more pillars
- Artifact paths from the wrong crawl run
- Report makes unsupported analytics, heatmap, revenue, or customer-behavior claims as fact
- Competitor section pretends competitors were crawled when they were not

## Warnings

Warnings reduce score but do not automatically fail the report.

- Confidence above 80%
- Lift upper bound above 12%
- Technical status too confident
- Cookie/privacy marked Pass from privacy link only
- Checkout marked Pass without checkout verification
- Mobile or speed marked Pass without measurement
- Fewer than 3 screenshot citations
- Generic experiments
- Risky health/wellness claims