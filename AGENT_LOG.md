# AGENT_LOG.md

## Timebox

Total time spent: ~5 hours

* Harness and crawler setup: ~1 hour
* Artifact-backed report-generation rules and `AGENTS.md` workflow finalization: ~1.5 hours
* Deterministic evaluator and eval loop: ~2 hours
* Human feedback loop and validation: ~0.5 hours

## Rough build log

* Set up the repo-level Codex workflow with `AGENTS.md`, assignment context, skills, sample outputs, artifacts, and eval folders.

* Built the harness around an artifact-first flow: crawl the storefront, save evidence, then generate the audit only from the selected crawl run.

* Replaced the basic crawler with a Playwright crawler that captures rendered HTML, extracted text, raw endpoint responses, screenshots, and a manifest.

* Debugged crawler reliability issues, including false blocked-page detection from Cloudflare script presence.

* Added selected-run discipline so reports cannot mix evidence across crawl folders.

* Added report-generation rules for structure, artifact citations, five-pillar coverage, 10 experiments, calibrated CRO estimates, technical-check caution, and screenshot-backed visual claims.

* Updated `AGENTS.md` so Codex can run the workflow from a minimal prompt like `Audit https://example-store.com`.

* Tested the workflow on Ginger People, Zen Rojas, Chimes Gourmet, and Art of Tea to expose repeated quality issues and avoid overfitting to one storefront.

* Built `eval_report.py` as a deterministic evaluator for report structure, artifact grounding, selected-run consistency, calibration, screenshot evidence, and unsupported claims.

* Added eval JSON output under `eval_results/` so failures, warnings, scores, selected runs, and parsed evidence are inspectable.

* Added safe manifest inference and tested mismatched report/manifest cases to verify selected-run validation.

* Built `run_eval_loop.py` to run evaluation, decide accept/revise/escalate, and create targeted revision prompts when needed.

* Added revision prompts that let Codex revise flagged report issues without recrawling or adding new evidence.

* Tested the revision loop on Ginger People and confirmed evaluator warnings could be fixed through a targeted report revision.

* Added `record_human_feedback.py` to collect human agreement/disagreement, reviewer reason, and notes as structured JSON.

* Kept human feedback manual: Codex prints the command, but the human reviewer runs it locally.

* Updated the final audit flow so every Codex run ends with next actions and the human feedback command.


## Representative prompts fed to Codex while building

1. Read AGENTS.md and skills/storefront-artifact-collection/SKILL.md.

Create a new Playwright-based crawler named crawl_playwright.py.

The skill defines the artifact collection requirements. Implement the crawler as the execution tool for that skill.

Keep crawl.py as the simple HTTP fallback. Do not delete it.

crawl_playwright.py should:
- normalize URLs with or without https
- create a per-run artifact folder
- use Playwright Chromium to visit representative storefront pages and content signals
- check homepage, product pages, collection/category pages, cart, key content pages, robots.txt, sitemap.xml, sitemap_index.xml, products.json, and collections.json where possible
- write a manifest.json summarizing pages, artifacts, technical checks, failed pages, and limitations

2. Read crawl_playwright.py and the latest manifest at artifacts/gingerpeople.com-20260607T220352Z/manifest.json.

The Playwright crawler is mechanically working, but Ginger People returns 403 pages with Cloudflare challenge scripts. Patch the crawler to improve browser access and make blocked-page handling safer.

- Keep crawl.py unchanged.
- Do not treat 403/Forbidden pages as valid storefront pages.
- If a page status is 403, title contains "403", visible text contains "Forbidden", or HTML contains "/cdn-cgi/challenge-platform",
- Remove the custom QosmicAuditCrawler user agent from Playwright browser contexts. Use the default Playwright/Chromium user agent or a normal Chrome-like browser context.
- Add a --headful flag so I can run the crawler in visible browser mode for debugging.
- Add a --no-mobile flag so I can skip mobile screenshots while debugging.
- Change sequencing to browser-first: visit the homepage with Playwright before hitting products.json, collections.json, or sitemap endpoints.
- After patching, run python -m py_compile crawl_playwright.py and tell me the exact commands to test headless and headful mode.

3. Update eval_report.py to add deterministic content-quality warnings.

Add warnings for:

Confidence calibration:
Parse all "Confidence %: NN%" values.
Add a warning for each confidence > 80.
Use check name "high_confidence".
Message should include the experiment heading and confidence value.
Add a stronger warning message when confidence > 85.

Expected lift calibration:
Parse all "Expected lift range: +X-Y%" values.
Add a warning for each upper bound > 12.
Use check name "high_lift_range".
Message should include the experiment heading and lift range.
Add a stronger warning message when upper bound > 15.

Unsupported claim language:
Warn if report text contains risky unsupported phrases outside explicit disclaimers:
revenue leak
conversion rate is low
analytics show
heatmaps show
customers are confused
proved
guaranteed
will increase revenue
Use check name "unsupported_claim_language".
Include the matched phrase in the warning.
Count cited artifact paths containing "/screenshots/".
Warn if fewer than 3 screenshot paths are cited.
Warnings reduce score by 3 points each.
--json and --no-save still work.
Manifest inference still works.

Test with:
python3 -m py_compile eval_report.py
python3 eval_report.py sample_output/artoftea.com_audit.md --no-save
python3 eval_report.py sample_output/chimesgourmet.com_audit.md --no-save
python3 eval_report.py sample_output/zenrojas.com_audit.md --no-save
python3 eval_report.py sample_output/gingerpeople.com_audit_repeat.md --no-save

4. Update run_eval_loop.py so it captures human feedback on every run by calling the separate record_human_feedback.py script.

Important:

Do not modify eval_report.py.
Keep record_human_feedback.py as the separate feedback collector.
Keep the current score threshold logic for revision prompts.
Human feedback should be collected every time, regardless of score or decision.

Terminology:

"Human feedback" means a lightweight agreement/disagreement label on the eval result. This happens every run.
"ESCALATE_TO_HUMAN_REVIEW" means the report is too low-quality or risky to trust automatically. This only happens when score < 70.

Current behavior:
run_eval_loop.py runs eval_report.py, reads eval JSON, prints score/warnings/decision, and creates a revision prompt when needed.

New behavior:
After printing the eval loop summary and creating a revision prompt if needed, run:

python3 record_human_feedback.py eval_results/<report_stem>.json

Behavior details:

If stdin is interactive, call record_human_feedback.py as a subprocess and let it ask:
Do you agree with this eval result? [y/n]
If stdin is not interactive, do not fail the whole eval loop. Instead, print:
Human feedback skipped because stdin is not interactive.
To record feedback manually, run:
python3 record_human_feedback.py eval_results/<report_stem>.json
Keep revision prompt behavior:
failures exist -> BLOCKED_REVISE_REQUIRED and create revision prompt
score >= 90 -> ACCEPTABLE_WITH_OR_WITHOUT_MINOR_WARNINGS and no revision prompt
score >= 70 -> REVISE_ONCE and create revision prompt
score < 70 -> ESCALATE_TO_HUMAN_REVIEW
Rename the low-score decision from HUMAN_REVIEW_REQUIRED to ESCALATE_TO_HUMAN_REVIEW if it currently uses the old name.
For now, do not automatically feed the revision prompt into Codex.
The script should only create the revision prompt.
In production, this handoff could be automated.
Print a clear final summary showing:
decision
revision prompt path if created
human feedback path if created, or the manual feedback command if skipped

python3 run_eval_loop.py sample_output/gingerpeople.com_audit_repeat.md

Expected:

Both runs ask for human feedback.
Revised Ginger People should not create a revision prompt because it scores 100.
Original Ginger People should create a revision prompt because it scores 85.
Both runs should create human feedback JSON files.
Low-score cases, if any, should use decision ESCALATE_TO_HUMAN_REVIEW, not HUMAN_REVIEW_REQUIRED.

5. Create a small orchestration script called `run_eval_loop.py`.

Goal: show the first evaluation loop for a generated audit report.

CLI: `python3 run_eval_loop.py <report.md>`

Behavior:

Run `eval_report.py` on the given report path. Use the simplified manifest inference behavior. Do not require the user to pass `manifest.json`. Let `eval_report.py` save its JSON result to `eval_results/<report_stem>.json`.

Read the saved eval JSON.

Print a clear loop summary with the report path, eval JSON path, score, passed true/false, number of failures, number of warnings, and decision.

Decision rules: if failures exist, decision = `BLOCKED_REVISE_REQUIRED`. Else if score >= 90, decision = `ACCEPTABLE_WITH_OR_WITHOUT_MINOR_WARNINGS`. Else if score >= 70, decision = `REVISE_ONCE`. Else, decision = `HUMAN_REVIEW_REQUIRED`.

If decision is `REVISE_ONCE` or `BLOCKED_REVISE_REQUIRED`, write a revision prompt file to `eval_results/<report_stem>_revision_prompt.txt`.

The revision prompt should tell Codex to revise the report using the eval JSON, not recrawl, not use new evidence, only fix the failures and warnings listed in the eval result, keep artifact citations from the same selected run, and save the revised report as `sample_output/<original_stem>_revised.md`.

If decision is `ACCEPTABLE_WITH_OR_WITHOUT_MINOR_WARNINGS`, do not create a revision prompt.

Keep this deterministic. Do not call an LLM from the script.

Test with:

`python3 run_eval_loop.py sample_output/gingerpeople.com_audit_repeat.md`

`python3 run_eval_loop.py sample_output/zenrojas.com_audit.md`

  
## Agent-driven vs. human-driven work

I used Codex mainly as the implementation agent. I gave it the repo context, scoped the tasks, and asked it to turn the artifact-collection/report-generation ideas into working code.

I drove the main decisions: moving to an artifact-first workflow, switching from a basic crawler to Playwright, enforcing selected-run discipline, and deciding what the evaluator should check. I also reviewed the generated reports and pushed back when the output was too confident, not grounded enough, or making claims the artifacts did not support.

Codex handled most of the mechanical build work: implementing the crawler, evaluator, eval loop, revision prompt flow, instruction-file updates, and first-pass report generation. When the output exposed issues, I took the wheel again, refined the requirements, and used Codex to make the next targeted change.





