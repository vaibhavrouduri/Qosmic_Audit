#!/usr/bin/env python3
"""Run the first deterministic evaluation loop for a generated audit report."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
EVAL_RESULTS_DIR = ROOT / "eval_results"


def usage() -> str:
    return "Usage: python3 run_eval_loop.py <report.md>"


def rel_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def eval_json_path(report_path: Path) -> Path:
    return EVAL_RESULTS_DIR / f"{report_path.stem}.json"


def revision_prompt_path(report_path: Path) -> Path:
    return EVAL_RESULTS_DIR / f"{report_path.stem}_revision_prompt.txt"


def human_feedback_path(result_path: Path) -> Path:
    return result_path.with_name(f"{result_path.stem}_human_feedback.json")


def revised_report_path(report_path: Path) -> Path:
    return ROOT / "sample_output" / f"{report_path.stem}_revised.md"


def run_eval(report_path: Path) -> int:
    command = [sys.executable, str(ROOT / "eval_report.py"), str(report_path)]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if completed.returncode not in (0, 1):
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


def load_eval_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def choose_decision(score: int, failures: list[Any]) -> str:
    if failures:
        return "BLOCKED_REVISE_REQUIRED"
    if score >= 85:
        return "ACCEPTABLE_WITH_OR_WITHOUT_MINOR_WARNINGS"
    if score >= 70:
        return "REVISE_ONCE"
    return "ESCALATE_TO_HUMAN_REVIEW"


def write_revision_prompt(report_path: Path, result_path: Path, payload: dict[str, Any]) -> Path:
    output_path = revision_prompt_path(report_path)
    revised_path = revised_report_path(report_path)
    failures = payload.get("failures", [])
    warnings = payload.get("warnings", [])

    prompt = [
        "Revise the audit report using the eval JSON result.",
        "",
        f"Report to revise: {rel_path(report_path)}",
        f"Eval JSON: {rel_path(result_path)}",
        f"Save the revised report as: {rel_path(revised_path)}",
        "",
        "Constraints:",
        "- Do not recrawl.",
        "- Do not use new evidence.",
        "- Only fix the failures and warnings listed in the eval result.",
        "- Keep artifact citations from the same selected run.",
        "- Preserve the required report structure from HARNESS_SPEC.md.",
        "",
        f"Failures to fix: {len(failures)}",
    ]
    for finding in failures:
        prompt.append(f"- {finding.get('check', 'unknown')}: {finding.get('message', '')}")

    prompt.append("")
    prompt.append(f"Warnings to fix: {len(warnings)}")
    for finding in warnings:
        prompt.append(f"- {finding.get('check', 'unknown')}: {finding.get('message', '')}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(prompt).rstrip() + "\n", encoding="utf-8")
    return output_path


def print_findings(label: str, findings: list[Any]) -> None:
    if not findings:
        return
    print(f"{label}:")
    for finding in findings:
        check = finding.get("check", "unknown") if isinstance(finding, dict) else "unknown"
        message = finding.get("message", str(finding)) if isinstance(finding, dict) else str(finding)
        print(f"- {check}: {message}")


def record_human_feedback(result_path: Path) -> Path | None:
    if not sys.stdin.isatty():
        command = f"python3 record_human_feedback.py {rel_path(result_path)}"
        print("Human feedback skipped because stdin is not interactive.")
        print("To record feedback manually, run:")
        print(command)
        return None

    command = [sys.executable, str(ROOT / "record_human_feedback.py"), rel_path(result_path)]
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        print(
            f"run_eval_loop error: human feedback collector exited with code {completed.returncode}",
            file=sys.stderr,
        )
        return None

    output_path = human_feedback_path(result_path)
    return output_path if output_path.exists() else None


def print_next_actions(report_path: Path, result_path: Path, prompt_path: Path | None, feedback_path: Path | None) -> None:
    print("\nNext actions:")
    print("\n1. Optional revision:")
    if prompt_path:
        print("\nA revision prompt was created:")
        print(rel_path(prompt_path))
        print("\nTo improve the report, feed this prompt to the agent, then rerun:")
        print(f"python run_eval_loop.py {rel_path(report_path)}")
    else:
        print("\nNo revision prompt was created. The report meets the current evaluator threshold.")

    print("\n2. Human feedback:")
    print("Record human feedback on this eval/report:")
    print(f"python record_human_feedback.py {rel_path(result_path)}")
    if feedback_path:
        print("Human feedback already recorded at:")
        print(rel_path(feedback_path))


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(usage(), file=sys.stderr)
        return 2

    report_path = Path(argv[0])
    if not report_path.is_absolute():
        report_path = ROOT / report_path
    if not report_path.exists():
        print(f"run_eval_loop error: report not found: {rel_path(report_path)}", file=sys.stderr)
        return 2

    eval_returncode = run_eval(report_path)
    if eval_returncode not in (0, 1):
        return eval_returncode

    result_path = eval_json_path(report_path)
    if not result_path.exists():
        print(f"run_eval_loop error: eval JSON was not saved: {rel_path(result_path)}", file=sys.stderr)
        return 2

    try:
        payload = load_eval_json(result_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"run_eval_loop error: could not read eval JSON: {exc}", file=sys.stderr)
        return 2

    score = int(payload.get("score", 0))
    passed = bool(payload.get("passed", False))
    failures = payload.get("failures", [])
    warnings = payload.get("warnings", [])
    decision = choose_decision(score, failures)

    print("\nEval loop summary")
    print(f"Report path: {rel_path(report_path)}")
    print(f"Eval JSON path: {rel_path(result_path)}")
    print(f"Score: {score}")
    print(f"Passed: {str(passed).lower()}")
    print(f"Failures: {len(failures)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Decision: {decision}")

    print_findings("Failures", failures)
    print_findings("Warnings", warnings)

    prompt_path = None
    if decision in {"REVISE_ONCE", "BLOCKED_REVISE_REQUIRED"}:
        prompt_path = write_revision_prompt(report_path, result_path, payload)
        print(f"Revision prompt: {rel_path(prompt_path)}")

    feedback_path = record_human_feedback(result_path)

    print("\nFinal summary")
    print(f"Eval JSON path: {rel_path(result_path)}")
    print(f"Decision: {decision}")
    if prompt_path:
        print(f"Revision prompt path: {rel_path(prompt_path)}")
    if feedback_path:
        print(f"Human feedback path: {rel_path(feedback_path)}")
    print_next_actions(report_path, result_path, prompt_path, feedback_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
