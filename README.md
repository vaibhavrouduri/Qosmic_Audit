# Qosmic Audit Harness

This repo contains a runtime harness for generating artifact-backed CRO audits for Shopify-style storefronts from a single URL.

The intended interaction is:

```text
Audit https://example-store.com
```

A repo-aware coding agent such as Codex or Claude Code reads `AGENTS.md`, runs the crawler, generates a report from the fresh crawl artifacts, runs the eval loop, and stops.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the main runtime dependency:

```bash
pip install playwright
```

Install the Playwright Chromium browser:

```bash
python -m playwright install chromium
```

The virtual environment is needed for the Python runtime dependencies, mainly Playwright. Do not commit `.venv`; evaluators should create it locally using the steps above.

## Run with a coding agent

Open this repo in Codex, Claude Code, or a similar coding agent and give it a URL-only request:

```text
Audit https://example-store.com
```

The agent should follow `AGENTS.md` and run the workflow:

1. Crawl the site with Playwright.
2. Use the newly generated `manifest.json`.
3. Generate the audit report from that selected crawl run only.
4. Run the eval loop.
5. Stop and report the eval result, revision prompt path if created, and human feedback command.

## Manual commands

Crawl a storefront:

```bash
python crawl_playwright.py --headful --no-mobile https://example-store.com
```

The crawler writes artifacts to:

```text
artifacts/<domain>-<timestamp>/
```

Each artifact run includes:

```text
manifest.json
screenshots/
html/
text/
raw/
```

After the coding agent generates a report under `sample_output/`, run the eval loop:

```bash
python run_eval_loop.py sample_output/<domain>_audit.md
```

If the evaluator recommends revision, it writes a revision prompt under `eval_results/`.

The default audit flow stops there. The agent should not automatically apply the revision prompt.

## Human feedback

Human feedback is manual by design. After reviewing the report and eval result, run:

```bash
python record_human_feedback.py eval_results/<domain>_audit.json
```

This saves a human feedback JSON file under `eval_results/`.

## Important files

* `AGENTS.md` — main agent workflow contract.
* `HARNESS_SPEC.md` — report schema and harness requirements.
* `REFERENCE_REPORT.md` — quality reference for report depth and structure.
* `crawl_playwright.py` — Playwright artifact collector.
* `run_eval_loop.py` — eval-loop entrypoint.
* `eval_report.py` — deterministic report evaluator.
* `record_human_feedback.py` — manual human feedback recorder.
* `sample_output/` — generated sample audit reports.
* `eval_results/` — eval JSON, revision prompts, and human feedback.
* `artifacts/` — crawl evidence used by reports.

## Notes

Reports are generated only from saved crawl artifacts. The harness does not use merchant analytics, revenue data, heatmaps, session recordings, or private conversion data. CRO recommendations are framed as testable hypotheses, not proven causes.
