#!/usr/bin/env python3
"""Evaluate a generated CRO audit report against structure and run evidence rules."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent

REQUIRED_MAJOR_SECTIONS = [
    "Executive summary",
    "Proposed experiments",
    "Competitor analysis",
    "Technical checks",
]

REQUIRED_EXPERIMENT_FIELDS = [
    "Pillar",
    "Affected surface and URL",
    "Evidence",
    "Hypothesis",
    "Primary change",
    "Primary KPI",
    "Decision rule",
    "Expected lift range",
    "Confidence %",
]

ALLOWED_PILLARS = {
    "Conversion",
    "AOV",
    "Retention",
    "Acquisition",
    "Performance",
}

ARTIFACT_PATH_RE = re.compile(r"artifacts/[A-Za-z0-9._/-]+")
MAJOR_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
EXPERIMENT_HEADING_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
CONFIDENCE_RE = re.compile(r"\*\*Confidence %:\*\*\s*(\d+(?:\.\d+)?)%", re.IGNORECASE)
EXPECTED_LIFT_RE = re.compile(
    r"\*\*Expected lift range:\*\*\s*(\+?\s*\d+(?:\.\d+)?\s*-\s*(\d+(?:\.\d+)?)%)",
    re.IGNORECASE,
)
UNSUPPORTED_CLAIM_PHRASES = [
    "revenue leak",
    "conversion rate is low",
    "analytics show",
    "heatmaps show",
    "customers are confused",
    "proved",
    "guaranteed",
    "will increase revenue",
]
UNSUPPORTED_CLAIM_RE = re.compile(
    "|".join(
        rf"\b{re.escape(phrase)}\b"
        for phrase in UNSUPPORTED_CLAIM_PHRASES
    ),
    re.IGNORECASE,
)
DISCLAIMER_RE = re.compile(r"\bdisclaimers?\b", re.IGNORECASE)
TABLE_SEPARATOR_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$")
TECHNICAL_STATUS_VALUES = {"pass", "warn", "fail"}


@dataclass
class EvalFinding:
    check: str
    message: str


@dataclass
class EvalReport:
    report_path: Path
    manifest_path: Path
    selected_run: str
    failures: list[EvalFinding] = field(default_factory=list)
    warnings: list[EvalFinding] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.failures

    @property
    def score(self) -> int:
        return max(0, 100 - (15 * len(self.failures)) - (3 * len(self.warnings)))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate report structure and selected-run artifact citations."
    )
    parser.add_argument("report", help="Generated audit report Markdown file.")
    parser.add_argument(
        "manifest",
        nargs="?",
        help="Selected crawl run manifest.json. If omitted, infer from artifact paths cited in the report.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text summary.",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save eval JSON to eval_results/<report_stem>.json.",
    )
    return parser.parse_args(argv)


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Manifest is not valid JSON: {path} ({exc})") from exc


def normalize_rel_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def selected_run_folder(manifest_path: Path, manifest: dict[str, Any]) -> str:
    run_folder = str(manifest.get("run_folder") or "").strip().rstrip("/")
    if run_folder:
        return run_folder
    return normalize_rel_path(manifest_path.parent)


def section_ranges(markdown: str) -> dict[str, tuple[int, int]]:
    matches = list(MAJOR_HEADING_RE.finditer(markdown))
    ranges: dict[str, tuple[int, int]] = {}
    for index, match in enumerate(matches):
        name = normalize_heading(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        ranges[name] = (start, end)
    return ranges


def normalize_heading(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    value = re.sub(r"^\d+\.\s*", "", value)
    return value


def section_text(markdown: str, ranges: dict[str, tuple[int, int]], name: str) -> str:
    start, end = ranges[name]
    return markdown[start:end]


def experiment_blocks(proposed_section: str) -> list[tuple[str, str]]:
    matches = list(EXPERIMENT_HEADING_RE.finditer(proposed_section))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(proposed_section)
        blocks.append((match.group(1).strip(), proposed_section[start:end]))
    return blocks


def field_regex(field: str) -> re.Pattern[str]:
    escaped = re.escape(field)
    return re.compile(rf"^\s*(?:[-*]\s*)?(?:\*\*)?{escaped}(?:\*\*)?\s*:", re.IGNORECASE | re.MULTILINE)


def extract_pillar(block: str) -> str | None:
    match = field_regex("Pillar").search(block)
    if not match:
        return None
    line = block[match.end() : block.find("\n", match.end()) if "\n" in block[match.end() :] else len(block)]
    value = re.sub(r"[*_`]", "", line).strip()
    return value or None


def has_markdown_table(section: str) -> bool:
    lines = [line.strip() for line in section.splitlines()]
    for index in range(len(lines) - 1):
        if "|" not in lines[index] or "|" not in lines[index + 1]:
            continue
        if re.fullmatch(r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?", lines[index + 1]):
            return True
    return False


def split_markdown_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [re.sub(r"\s+", " ", cell.replace(r"\|", "|").strip()) for cell in line.split("|")]


def normalize_table_header(value: str) -> str:
    value = re.sub(r"[*_`]", "", value).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value


def parse_markdown_tables(section: str) -> list[list[dict[str, str]]]:
    lines = section.splitlines()
    tables: list[list[dict[str, str]]] = []
    index = 0
    while index < len(lines) - 1:
        header_line = lines[index].strip()
        separator_line = lines[index + 1].strip()
        if "|" not in header_line or "|" not in separator_line or not TABLE_SEPARATOR_RE.fullmatch(separator_line):
            index += 1
            continue

        headers = [normalize_table_header(cell) for cell in split_markdown_table_row(header_line)]
        rows: list[dict[str, str]] = []
        index += 2
        while index < len(lines) and "|" in lines[index]:
            line = lines[index].strip()
            if not line or TABLE_SEPARATOR_RE.fullmatch(line):
                break
            cells = split_markdown_table_row(line)
            if len(cells) < len(headers):
                cells.extend([""] * (len(headers) - len(cells)))
            elif len(cells) > len(headers):
                cells = cells[: len(headers) - 1] + [" | ".join(cells[len(headers) - 1 :])]
            rows.append({headers[cell_index]: cell for cell_index, cell in enumerate(cells[: len(headers)])})
            index += 1
        tables.append(rows)
    return tables


def table_cell(row: dict[str, str], candidates: list[str], fallback_index: int | None = None) -> str:
    for candidate in candidates:
        if candidate in row:
            return row[candidate].strip()
    if fallback_index is not None and fallback_index < len(row):
        return list(row.values())[fallback_index].strip()
    return ""


def parse_technical_checks(markdown: str) -> list[dict[str, str]]:
    ranges = section_ranges(markdown)
    if "Technical checks" not in ranges:
        return []

    technical = section_text(markdown, ranges, "Technical checks")
    checks: list[dict[str, str]] = []
    for table in parse_markdown_tables(technical):
        for row in table:
            name = table_cell(row, ["check", "technical_check", "item", "name"], 0)
            status = table_cell(row, ["status", "result"], 1)
            detail = table_cell(row, ["detail", "details", "evidence", "notes", "finding"], 2)
            if status.lower() not in TECHNICAL_STATUS_VALUES:
                continue
            checks.append({"check": name, "status": status, "detail": detail})
    return checks


def extract_artifact_paths(markdown: str) -> set[str]:
    paths: set[str] = set()
    for match in ARTIFACT_PATH_RE.finditer(markdown):
        raw = match.group(0).rstrip("`'\"),.;:")
        paths.add(raw)
    return paths


def extract_artifact_run_folders(markdown: str) -> set[str]:
    run_folders: set[str] = set()
    for artifact_path in extract_artifact_paths(markdown):
        parts = artifact_path.split("/")
        if len(parts) >= 3 and parts[0] == "artifacts" and parts[1]:
            run_folders.add("/".join(parts[:2]))
    return run_folders


def infer_manifest_path(report_path: Path) -> Path:
    if not report_path.exists():
        raise FileNotFoundError(f"Report not found: {report_path}")

    markdown = report_path.read_text(encoding="utf-8")
    run_folders = sorted(extract_artifact_run_folders(markdown))

    if not run_folders:
        raise ValueError(
            "Cannot infer manifest: report cites no artifact paths like artifacts/<run_folder>/..."
        )
    if len(run_folders) > 1:
        raise ValueError(
            "Cannot infer manifest: report cites artifact paths from multiple runs "
            f"({', '.join(run_folders)}). Pass the manifest explicitly."
        )

    manifest_path = ROOT / run_folders[0] / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Inferred manifest not found: {manifest_path}")
    return manifest_path


def resolve_manifest_path(report_path: Path, manifest_arg: str | None) -> Path:
    if manifest_arg:
        return Path(manifest_arg)
    return infer_manifest_path(report_path)


def validate_structure(markdown: str, result: EvalReport) -> None:
    major_sections = [normalize_heading(match.group(1)) for match in MAJOR_HEADING_RE.finditer(markdown)]
    result.details["major_sections"] = major_sections

    if major_sections != REQUIRED_MAJOR_SECTIONS:
        result.failures.append(
            EvalFinding(
                "major_sections",
                "Report must contain exactly these H2 sections in order: "
                + ", ".join(REQUIRED_MAJOR_SECTIONS),
            )
        )

    ranges = section_ranges(markdown)
    missing = [name for name in REQUIRED_MAJOR_SECTIONS if name not in ranges]
    if missing:
        result.failures.append(
            EvalFinding("missing_sections", "Missing required sections: " + ", ".join(missing))
        )
        return

    proposed = section_text(markdown, ranges, "Proposed experiments")
    experiments = experiment_blocks(proposed)
    result.details["experiment_count"] = len(experiments)
    result.details["experiment_headings"] = [heading for heading, _ in experiments]

    if len(experiments) != 10:
        result.failures.append(
            EvalFinding("experiment_count", f"Expected exactly 10 experiments; found {len(experiments)}.")
        )

    seen_pillars: set[str] = set()
    missing_field_details: list[str] = []
    missing_id_details: list[str] = []
    for index, (heading, block) in enumerate(experiments, start=1):
        if not re.search(r"\bexp[-_\w]*\d+\b", heading, flags=re.IGNORECASE):
            missing_id_details.append(f"experiment {index} heading lacks an experiment ID: {heading}")

        for field_name in REQUIRED_EXPERIMENT_FIELDS:
            if not field_regex(field_name).search(block):
                missing_field_details.append(f"experiment {index} missing {field_name}")

        pillar = extract_pillar(block)
        if pillar in ALLOWED_PILLARS:
            seen_pillars.add(pillar)
        elif pillar:
            result.failures.append(
                EvalFinding("invalid_pillar", f"Experiment {index} uses invalid pillar: {pillar}")
            )

    result.details["pillars"] = sorted(seen_pillars)

    if missing_id_details:
        result.failures.append(EvalFinding("experiment_ids", "; ".join(missing_id_details)))
    if missing_field_details:
        result.failures.append(EvalFinding("experiment_fields", "; ".join(missing_field_details)))

    missing_pillars = sorted(ALLOWED_PILLARS - seen_pillars)
    if missing_pillars:
        result.failures.append(
            EvalFinding("pillar_coverage", "Missing required pillars: " + ", ".join(missing_pillars))
        )

    competitor = section_text(markdown, ranges, "Competitor analysis")
    technical = section_text(markdown, ranges, "Technical checks")
    result.details["competitor_table"] = has_markdown_table(competitor)
    result.details["technical_table"] = has_markdown_table(technical)

    if not has_markdown_table(competitor):
        result.failures.append(EvalFinding("competitor_table", "Competitor analysis must include a Markdown table."))
    if not has_markdown_table(technical):
        result.failures.append(EvalFinding("technical_table", "Technical checks must include a Markdown table."))


def validate_artifact_run(markdown: str, manifest_path: Path, result: EvalReport) -> None:
    artifact_paths = sorted(extract_artifact_paths(markdown))
    result.details["artifact_path_count"] = len(artifact_paths)
    result.details["artifact_paths"] = artifact_paths
    screenshot_paths = [path for path in artifact_paths if "/screenshots/" in path]
    result.details["screenshot_path_count"] = len(screenshot_paths)

    selected_run = result.selected_run.rstrip("/")
    selected_manifest = f"{selected_run}/manifest.json"
    manifest_rel = normalize_rel_path(manifest_path)

    if manifest_rel != selected_manifest:
        result.warnings.append(
            EvalFinding(
                "manifest_location",
                f"Manifest path is {manifest_rel}, but manifest run_folder points to {selected_run}.",
            )
        )

    if not artifact_paths:
        result.failures.append(
            EvalFinding("artifact_citations", "Report does not cite any artifact paths from the selected run.")
        )
        return

    wrong_run_paths = [path for path in artifact_paths if not (path == selected_manifest or path.startswith(selected_run + "/"))]
    if wrong_run_paths:
        result.failures.append(
            EvalFinding(
                "mixed_artifact_runs",
                "Artifact paths must come only from selected run "
                f"{selected_run}: "
                + ", ".join(wrong_run_paths),
            )
        )

    missing_paths = [path for path in artifact_paths if path.startswith(selected_run + "/") and not (ROOT / path).exists()]
    if selected_manifest in artifact_paths and not manifest_path.exists():
        missing_paths.append(selected_manifest)
    if missing_paths:
        result.failures.append(
            EvalFinding("missing_artifacts", "Cited artifact paths do not exist: " + ", ".join(sorted(set(missing_paths))))
        )


def warn_high_confidence(experiments: list[tuple[str, str]], result: EvalReport) -> None:
    high_confidences: list[dict[str, Any]] = []
    for heading, block in experiments:
        for match in CONFIDENCE_RE.finditer(block):
            confidence = float(match.group(1))
            if confidence <= 80:
                continue
            confidence_display = f"{confidence:g}%"
            high_confidences.append({"heading": heading, "confidence": confidence})
            if confidence > 85:
                message = (
                    f"{heading} uses very high confidence ({confidence_display}); "
                    "confidence above 85% needs unusually strong selected-run evidence."
                )
            else:
                message = (
                    f"{heading} uses high confidence ({confidence_display}); "
                    "calibrate confidence to the visible artifact evidence."
                )
            result.warnings.append(EvalFinding("high_confidence", message))
    result.details["high_confidence_count"] = len(high_confidences)
    result.details["high_confidences"] = high_confidences


def warn_high_lift_ranges(experiments: list[tuple[str, str]], result: EvalReport) -> None:
    high_lift_ranges: list[dict[str, Any]] = []
    for heading, block in experiments:
        for match in EXPECTED_LIFT_RE.finditer(block):
            lift_range = re.sub(r"\s+", "", match.group(1))
            upper_bound = float(match.group(2))
            if upper_bound <= 12:
                continue
            high_lift_ranges.append(
                {"heading": heading, "lift_range": lift_range, "upper_bound": upper_bound}
            )
            if upper_bound > 15:
                message = (
                    f"{heading} uses very high expected lift range ({lift_range}); "
                    "upper bounds above 15% need unusually strong selected-run evidence."
                )
            else:
                message = (
                    f"{heading} uses high expected lift range ({lift_range}); "
                    "calibrate the upper bound to visible artifact evidence."
                )
            result.warnings.append(EvalFinding("high_lift_range", message))
    result.details["high_lift_range_count"] = len(high_lift_ranges)
    result.details["high_lift_ranges"] = high_lift_ranges


def warn_unsupported_claim_language(markdown: str, result: EvalReport) -> None:
    matches: list[str] = []
    for paragraph in re.split(r"\n\s*\n", markdown):
        if DISCLAIMER_RE.search(paragraph):
            continue
        for match in UNSUPPORTED_CLAIM_RE.finditer(paragraph):
            phrase = match.group(0)
            matches.append(phrase)
            result.warnings.append(
                EvalFinding(
                    "unsupported_claim_language",
                    f"Risky unsupported claim language found: {phrase}",
                )
            )
    result.details["unsupported_claim_language_count"] = len(matches)
    result.details["unsupported_claim_language_matches"] = matches


def warn_low_screenshot_evidence(result: EvalReport) -> None:
    screenshot_count = int(result.details.get("screenshot_path_count", 0))
    if screenshot_count < 3:
        result.warnings.append(
            EvalFinding(
                "low_screenshot_evidence",
                f"Report cites fewer than 3 screenshot artifact paths ({screenshot_count} found).",
            )
        )


def compact_detail(detail: str, limit: int = 180) -> str:
    detail = re.sub(r"\s+", " ", detail).strip()
    if len(detail) <= limit:
        return detail
    return detail[: limit - 3].rstrip() + "..."


def detail_matches_only(detail: str, allowed_re: re.Pattern[str]) -> bool:
    text = re.sub(r"`[^`]+`", "", detail)
    text = re.sub(r"artifacts/[A-Za-z0-9._/-]+", "", text)
    text = re.sub(r"\bEvidence\s*:", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\band\b|\bor\b|with|were|was|is|are|the|a|an|in|on|to|of|this|that|rendered|pages?|detected|found|links?|saved|artifact", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[^a-z0-9/]+", " ", text.lower()).strip()
    if not text:
        return False
    return allowed_re.fullmatch(text) is not None


def detail_only_supports_privacy_link(detail: str) -> bool:
    text = re.sub(r"`[^`]+`", "", detail)
    text = re.sub(r"artifacts/[A-Za-z0-9._/-]+", "", text)
    text = re.sub(r"\bEvidence\s*:", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip().lower()
    if not re.search(r"(privacy|cookie).{0,40}(link|policy|policies|page)|policy.{0,20}(link|page)", text):
        return False
    behavior_terms = re.compile(
        r"(banner|consent|preference|opt[- ]?(?:in|out)|reject|accept|manage|cmp|tested|verified|configured|fires?)",
        re.IGNORECASE,
    )
    return behavior_terms.search(text) is None or re.search(r"did\s+not\s+test|not\s+tested|was\s+not\s+verified", text) is not None


def manifest_has_speed_data(manifest: dict[str, Any]) -> bool:
    speed_key_re = re.compile(
        r"(lighthouse|core[_ -]?web[_ -]?vitals|web[_ -]?vitals|largest[_ -]?contentful[_ -]?paint|"
        r"\blcp\b|cumulative[_ -]?layout[_ -]?shift|\bcls\b|interaction[_ -]?to[_ -]?next[_ -]?paint|"
        r"\binp\b|first[_ -]?input[_ -]?delay|\bfid\b)",
        re.IGNORECASE,
    )

    def walk(value: Any) -> bool:
        if isinstance(value, dict):
            for key, child in value.items():
                if speed_key_re.search(str(key)):
                    return True
                if walk(child):
                    return True
        elif isinstance(value, list):
            return any(walk(child) for child in value)
        return False

    return walk(manifest)


def warn_technical_status_calibration(
    markdown: str,
    manifest: dict[str, Any],
    result: EvalReport,
) -> None:
    checks = parse_technical_checks(markdown)
    result.details["parsed_technical_checks"] = checks

    mobile_capture_enabled = bool(manifest.get("mobile_capture_enabled", False))
    speed_data_present = manifest_has_speed_data(manifest)
    warnings_before = len(result.warnings)

    checkout_pass_risky_re = re.compile(
        r"(checkout\s+was\s+not\s+entered|no\s+checkout\s+was\s+entered|checkout\s+was\s+not\s+verified|"
        r"checkout\s+was\s+not\s+tested|cart\s+only\s+loaded|cart\s+loaded\s+but\s+checkout\s+was\s+not\s+tested|"
        r"no\s+checkout\s+(?:route|path)\s+was\s+reached)",
        re.IGNORECASE,
    )
    checkout_fail_cart_only_re = re.compile(
        r"(/cart\s+returned\s+404|cart\s+returned\s+404|cart\s+was\s+missing|cart\s+was\s+not\s+loaded)",
        re.IGNORECASE,
    )
    checkout_failure_proven_re = re.compile(
        r"(checkout\s+(?:url|route|page|path)?\s*(?:returned|failed|errored|was\s+broken)|"
        r"/checkout\s+(?:returned|failed|errored)|checkout\s+status\s*:\s*(?:4\d\d|5\d\d|fail))",
        re.IGNORECASE,
    )
    desktop_speed_risky_re = re.compile(
        r"(only\s+rough\s+browser\s+timing\s+was\s+collected|rough\s+browser\s+timing\s+was\s+captured\s+only|"
        r"no\s+lighthouse\s+run\s+was\s+performed|no\s+core\s+web\s+vitals\s+data\s+was\s+collected|"
        r"no\s+lab\s+speed\s+test\s+was\s+run)",
        re.IGNORECASE,
    )
    crawler_blocked_re = re.compile(
        r"(403\s+to\s+(?:the\s+)?crawler|blocked\s+to\s+(?:the\s+)?crawler|waf\s+blocked|"
        r"cloudflare\s+blocked|crawler\s+blocked)",
        re.IGNORECASE,
    )

    for check in checks:
        name = check["check"]
        status = check["status"].strip().lower()
        detail = check["detail"]
        detail_plain = re.sub(r"[*_`]", "", detail)
        name_lower = name.lower()
        detail_for_message = compact_detail(detail)

        if ("cookie" in name_lower or "privacy" in name_lower) and status == "pass":
            if detail_only_supports_privacy_link(detail):
                result.warnings.append(
                    EvalFinding(
                        "technical_status_cookie_privacy",
                        f"{name} is marked Pass, but the detail only supports finding a privacy/cookie policy link: {detail_for_message}",
                    )
                )

        if "checkout" in name_lower and status == "pass" and checkout_pass_risky_re.search(detail_plain):
            result.warnings.append(
                EvalFinding(
                    "technical_status_checkout",
                    f"{name} is marked Pass while the detail says checkout was not verified: {detail_for_message}",
                )
            )

        if "checkout" in name_lower and status == "fail":
            if checkout_fail_cart_only_re.search(detail_plain) and not checkout_failure_proven_re.search(detail_plain):
                result.warnings.append(
                    EvalFinding(
                        "technical_status_checkout",
                        f"{name} is marked Fail, but the detail only proves cart availability rather than checkout failure: {detail_for_message}",
                    )
                )

        if "mobile" in name_lower and status == "pass" and not mobile_capture_enabled:
            result.warnings.append(
                EvalFinding(
                    "technical_status_mobile",
                    f"{name} is marked Pass, but manifest mobile_capture_enabled is false.",
                )
            )

        if "mobile" in name_lower and "speed" in name_lower and status == "pass":
            if not mobile_capture_enabled or not speed_data_present:
                result.warnings.append(
                    EvalFinding(
                        "technical_status_mobile_speed",
                        f"{name} is marked Pass without mobile capture or Lighthouse/Core Web Vitals data.",
                    )
                )

        if "desktop" in name_lower and "speed" in name_lower and status == "pass":
            if desktop_speed_risky_re.search(detail_plain):
                result.warnings.append(
                    EvalFinding(
                        "technical_status_desktop_speed",
                        f"{name} is marked Pass while the detail limits evidence to rough or missing lab speed data: {detail_for_message}",
                    )
                )

        if ("robots" in name_lower or "sitemap" in name_lower) and status == "fail":
            if crawler_blocked_re.search(detail_plain):
                result.warnings.append(
                    EvalFinding(
                        "technical_status_crawler_blocked",
                        f"{name} is marked Fail, but the detail indicates crawler blocking rather than a storefront failure: {detail_for_message}",
                    )
                )

    result.details["technical_warning_count"] = len(result.warnings) - warnings_before


def validate_content_quality(markdown: str, manifest: dict[str, Any], result: EvalReport) -> None:
    ranges = section_ranges(markdown)
    experiments: list[tuple[str, str]] = []
    if "Proposed experiments" in ranges:
        experiments = experiment_blocks(section_text(markdown, ranges, "Proposed experiments"))

    warn_high_confidence(experiments, result)
    warn_high_lift_ranges(experiments, result)
    warn_unsupported_claim_language(markdown, result)
    warn_low_screenshot_evidence(result)
    warn_technical_status_calibration(markdown, manifest, result)


def evaluate(report_path: Path, manifest_path: Path) -> EvalReport:
    if not report_path.exists():
        raise FileNotFoundError(f"Report not found: {report_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    manifest = load_manifest(manifest_path)
    selected_run = selected_run_folder(manifest_path, manifest)
    markdown = report_path.read_text(encoding="utf-8")

    result = EvalReport(
        report_path=report_path,
        manifest_path=manifest_path,
        selected_run=selected_run,
    )
    validate_structure(markdown, result)
    validate_artifact_run(markdown, manifest_path, result)
    validate_content_quality(markdown, manifest, result)
    return result


def finding_to_dict(finding: EvalFinding) -> dict[str, str]:
    return {"check": finding.check, "message": finding.message}


def result_payload(result: EvalReport) -> dict[str, Any]:
    report_path = normalize_rel_path(result.report_path)
    manifest_path = normalize_rel_path(result.manifest_path)
    return {
        "score": result.score,
        "passed": result.passed,
        "report": report_path,
        "report_path": report_path,
        "manifest": manifest_path,
        "manifest_path": manifest_path,
        "selected_run": result.selected_run,
        "failures": [finding_to_dict(finding) for finding in result.failures],
        "warnings": [finding_to_dict(finding) for finding in result.warnings],
        "details": result.details,
    }


def default_result_path(report_path: Path) -> Path:
    return ROOT / "eval_results" / f"{report_path.stem}.json"


def save_json(result: EvalReport) -> Path:
    output_path = default_result_path(result.report_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result_payload(result), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


def emit_json(result: EvalReport) -> None:
    payload = result_payload(result)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def emit_text(result: EvalReport) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"{status} eval_report")
    print(f"Report: {normalize_rel_path(result.report_path)}")
    print(f"Manifest: {normalize_rel_path(result.manifest_path)}")
    print(f"Selected run: {result.selected_run}")
    print(f"Score: {result.score}/100")
    print(f"Major sections: {len(result.details.get('major_sections', []))}")
    print(f"Experiments: {result.details.get('experiment_count', 0)}")
    print(f"Pillars: {', '.join(result.details.get('pillars', [])) or 'none'}")
    print(f"Artifact paths: {result.details.get('artifact_path_count', 0)}")

    if result.failures:
        print("\nFailures:")
        for finding in result.failures:
            print(f"- {finding.check}: {finding.message}")

    if result.warnings:
        print("\nWarnings:")
        for finding in result.warnings:
            print(f"- {finding.check}: {finding.message}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    report_path = Path(args.report)
    try:
        manifest_path = resolve_manifest_path(report_path, args.manifest)
        result = evaluate(report_path, manifest_path)
    except (OSError, ValueError) as exc:
        print(f"eval_report error: {exc}", file=sys.stderr)
        return 2

    if not args.no_save:
        try:
            save_json(result)
        except OSError as exc:
            print(f"eval_report error: failed to save JSON result: {exc}", file=sys.stderr)
            return 2

    if args.json:
        emit_json(result)
    else:
        emit_text(result)

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
