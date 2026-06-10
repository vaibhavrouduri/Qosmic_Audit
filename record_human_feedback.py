#!/usr/bin/env python3
"""Record lightweight human feedback for a saved eval result."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REASONS = [
    "score_too_high",
    "score_too_low",
    "eval_missed_serious_issue",
    "eval_flagged_something_fine",
    "report_correct_but_not_useful",
    "report_useful_but_too_risky",
    "other",
]


def usage() -> str:
    return "Usage: python3 record_human_feedback.py <eval_result.json>"


def load_eval_result(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"eval JSON is not valid JSON: {path} ({exc})") from exc


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def prompt_yes_no(prompt: str) -> bool:
    while True:
        answer = input(prompt).strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer y or n.")


def prompt_reason() -> str:
    print("Choose one reason:")
    for index, reason in enumerate(REASONS, start=1):
        print(f"{index}. {reason}")

    while True:
        answer = input("Reason: ").strip()
        if answer in REASONS:
            return answer
        if answer.isdigit():
            index = int(answer)
            if 1 <= index <= len(REASONS):
                return REASONS[index - 1]
        print("Please enter a listed reason or its number.")


def feedback_path(eval_path: Path) -> Path:
    return eval_path.with_name(f"{eval_path.stem}_human_feedback.json")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(usage(), file=sys.stderr)
        return 2

    if not sys.stdin.isatty():
        print(
            "record_human_feedback error: human feedback requires an interactive terminal.",
            file=sys.stderr,
        )
        return 2

    eval_path = Path(argv[0])
    if not eval_path.exists():
        print(f"record_human_feedback error: eval JSON not found: {eval_path}", file=sys.stderr)
        return 2
    if not eval_path.is_file():
        print(f"record_human_feedback error: eval JSON path is not a file: {eval_path}", file=sys.stderr)
        return 2

    try:
        result = load_eval_result(eval_path)
    except (OSError, ValueError) as exc:
        print(f"record_human_feedback error: {exc}", file=sys.stderr)
        return 2

    failures = as_list(result.get("failures"))
    warnings = as_list(result.get("warnings"))
    report_path = result.get("report_path") or result.get("report")
    selected_run = result.get("selected_run")
    score = result.get("score")
    passed = result.get("passed")

    print("Eval result summary")
    print(f"report_path: {report_path}")
    print(f"score: {score}")
    print(f"passed: {passed}")
    print(f"selected_run: {selected_run}")
    print(f"failures: {len(failures)}")
    print(f"warnings: {len(warnings)}")

    human_agrees = prompt_yes_no("Do you agree with this eval result? [y/n] ")
    human_reason = None if human_agrees else prompt_reason()
    human_note = input("Optional note: ").strip()

    feedback = {
        "eval_result_path": eval_path.as_posix(),
        "report_path": report_path,
        "score": score,
        "passed": passed,
        "selected_run": selected_run,
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "human_agrees": human_agrees,
        "human_reason": human_reason,
        "human_note": human_note,
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    output_path = feedback_path(eval_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(feedback, indent=2) + "\n", encoding="utf-8")
    print(f"Saved feedback: {output_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
