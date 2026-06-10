# Qosmic Audit Harness: Agent Instructions

## Project goal

This repo builds a runtime harness that lets a coding agent audit a Shopify storefront from a single URL and produce an artifact-backed CRO audit report.

The system should work for arbitrary Shopify storefronts. Do not hardcode findings, products, competitors, URLs, or recommendations for a specific store.

## Primary instruction

The user-facing input is one Shopify storefront URL.

When the user asks to audit a storefront URL, do not ask for manual screenshots, page lists, competitor lists, analytics exports, or extra configuration.

The harness must infer and execute the workflow from the URL alone:

1. Collect storefront artifacts.
2. Select the newly generated `manifest.json` as the current crawl run.
3. Generate the audit report from that selected crawl run only.
4. Run `python run_eval_loop.py <report_path>` after writing the report.

Do not write audit findings before artifact collection is complete.

## Default audit execution

When asked to audit a URL, execute the harness workflow directly.

Use this process:

1. Run `python crawl_playwright.py --headful --no-mobile <URL>` on the provided URL.
2. Use the `Manifest:` path printed by the crawler as the selected crawl run. If the crawler does not print a manifest path, use the newest `artifacts/<domain>-*/manifest.json` created by that execution.
3. Generate the report using:

   * `HARNESS_SPEC.md`
   * `REFERENCE_REPORT.md`
   * `skills/artifact-backed-report-generation/SKILL.md`
   * the selected crawl run's `manifest.json`
4. Write the report to the output path requested by the user.
5. If no output path is requested, write to `sample_output/<domain>_audit.md`.
6. After writing the report, run:

   `python run_eval_loop.py <report_path>`

   Use `run_eval_loop.py` as the final evaluation entrypoint. Do not call `eval_report.py` directly as the final validation step unless debugging. `run_eval_loop.py` wraps `eval_report.py`, applies the accept/revise/escalate decision logic, creates a revision prompt when needed, and prints the human feedback command for the user.
7. After `run_eval_loop.py` finishes, stop and report the eval result.

   Do not edit, patch, tighten, revise, or improve the report after eval.

   Do not revise the report because warnings exist.

   Do not revise the report because the score is below 100.

   Do not revise the report even if `run_eval_loop.py` created a revision prompt.

   If a revision prompt was created, only report its path. The revision prompt is an output artifact, not permission to apply it.

   Return the report path, eval JSON path, score, decision, revision prompt path if one exists, and human feedback command.

   After every `run_eval_loop.py` run, the final user-facing response must include the human feedback command for the latest eval JSON:

   `python record_human_feedback.py <eval_json_path>`

   Do not omit this command, even if it appeared earlier in terminal output.

   Do not run `record_human_feedback.py` automatically during Codex audit runs. Human feedback must be collected manually by the user after reviewing the report and eval result.
8. Do not use artifacts from previous crawl runs.
9. Do not crawl new pages after artifact collection is complete.
10. If pages are blocked, failed, unavailable, or incomplete, record that honestly instead of inventing findings.

Before finishing, self-check:

* the report has exactly 4 major sections
* the report has exactly 10 proposed experiments
* all 5 pillars are represented
* every experiment has all required fields
* every meaningful claim cites evidence from the selected crawl run
* when screenshot artifacts exist, the report cites at least 3 relevant screenshot paths across the report
* technical checks are evidence-safe
* there are no unsupported analytics, revenue, heatmap, conversion-rate, or private-data claims
* `run_eval_loop.py` has been run on the generated report.
* after eval, the report has not been edited, patched, tightened, revised, or improved.
* any revision prompt path has been reported as an artifact only, not applied.
* the final response includes the human feedback command for the latest eval JSON.

## User-facing command

The intended user interaction is a minimal audit request, such as:

Audit https://example-store.com

If the user provides an output path, use it. Otherwise write the report to `sample_output/<domain>_audit.md`.


## Source-of-truth files

Read these files when relevant:

* `HARNESS_SPEC.md`: runtime contract, report schema, audit workflow, and quality rules.
* `REFERENCE_REPORT.md`: quality reference only. Use it to understand specificity, structure, and depth. Do not copy merchant-specific claims, products, competitors, URLs, experiments, confidence scores, lift ranges, or wording.
* `skills/storefront-artifact-collection/SKILL.md`: crawler behavior specification.
* `skills/artifact-backed-report-generation/SKILL.md`: report generation specification.

## Operating principles

* Artifact collection comes before audit writing.
* Every meaningful audit claim must be grounded in a saved artifact, screenshot path, manifest entry, or inspected URL.
* Do not claim access to analytics, revenue, conversion rate, heatmaps, session recordings, or private merchant data.
* Frame CRO recommendations as hypotheses to test, not proven causes.
* Prefer reliable, repeatable scripts over ad hoc one-off terminal commands.
* Keep the harness general. The same workflow should work on a new Shopify storefront without manual page lists or custom config.

## Crawl/report boundary

Crawler scripts should only collect artifacts. They should not generate CRO recommendations or write the audit report.

Report-generation steps should use only collected artifacts and explicitly cite evidence.

Reports must be generated from the current crawl run only. The current crawl run is identified by the `manifest.json` produced by the crawler for that execution. Do not mix evidence across artifact folders.

## Artifact collection implementation

Use `crawl_playwright.py` as the primary artifact collector.

The crawler is the runtime source of truth for artifact collection. The artifact collection skill is retained as reference documentation for the intended crawl behavior, artifact expectations, and selected-run discipline:

`skills/storefront-artifact-collection/SKILL.md`

## Report generation implementation

Use the report generation behavior documented in:

`skills/artifact-backed-report-generation/SKILL.md`

The report must follow `HARNESS_SPEC.md`.

