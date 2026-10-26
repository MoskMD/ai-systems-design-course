"""Laboratory 04 Stage B retrieval-contract and chunking slice."""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import yaml

from .workflow import WorkflowError


STAGE_B_DIRECTORY = "stage-b"
DEFAULT_STAGE_B_FIXTURE = Path(__file__).resolve().parents[2] / "cases" / "lab04" / "stage-b-fixture.json"
BOUNDARY_COMPARISON_FILENAME = "boundary-comparison.json"
BOUNDARY_DECISION_FILENAME = "boundary-decision.yaml"
RETRIEVAL_CONTRACT_FIELDS = {
    "text query",
    "canonical knowledge collection version",
    "retrieval unit and its boundary rule",
    "retrieval configuration",
    "ranked candidate output",
    "evaluator-only expected result",
    "relevance judging basis",
    "designated human evaluator",
    "observation boundary",
}

LAB04_REPORT_HEADINGS = ("Ідентифікація", "Мета роботи", "Хід виконання", "Висновки")
LAB04_REPORT_SCREENSHOTS = (
    "01-boundary-selection.png",
    "02-embedding-index.png",
    "03-retrieval-comparison.png",
    "04-relevance-metrics.png",
    "05-operational-decision.png",
    "06-final-verification.png",
)
LAB04_REQUIRED_EVIDENCE = (
    "stage-b/boundary-comparison.json",
    "stage-b/boundary-decision.yaml",
    "stage-c1/retrieval-unit-embeddings.json",
    "stage-c1/index-manifest.json",
    "stage-c1/binding-check-required-course-seed-v1.json",
    "stage-c1/binding-check-required-course-seed-v2.json",
    "stage-c2/evaluation-case-a-lexical-retrieval.json",
    "stage-c2/evaluation-case-a-embedding-based-retrieval.json",
    "stage-c2/evaluation-case-a-hybrid-retrieval.json",
    "stage-c2/evaluation-case-a-lexical-retrieval-followed-by-embedding-based-reranking.json",
    "stage-c2/evaluation-case-b-lexical-retrieval.json",
    "stage-c2/evaluation-case-b-embedding-based-retrieval.json",
    "stage-c2/evaluation-case-b-hybrid-retrieval.json",
    "stage-c2/evaluation-case-b-lexical-retrieval-followed-by-embedding-based-reranking.json",
    "stage-c3/relevance-judgments.json",
    "stage-c3/retrieval-metrics.json",
    "stage-c3/operational-evidence.json",
    "stage-c3/configuration-decision.json",
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise WorkflowError(message)

def _write_new_output(output: Path, content: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(output, flags, 0o666)
    except FileExistsError as exc:
        raise WorkflowError(f"Output already exists at {output}.") from exc
    except OSError as exc:
        raise WorkflowError(f"Cannot create output at {output}: {exc}") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(content)


def _read_fixture(path: Path) -> dict:
    try:
        fixture = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Cannot read the Laboratory 04 Stage B fixture: {exc}") from exc
    _require(isinstance(fixture, dict), "The Laboratory 04 Stage B fixture must be an object.")
    _require(fixture.get("schema_version") == "1.0", "Unsupported Laboratory 04 Stage B fixture version.")
    return fixture


def _character_provenance(record: dict, start: int, end: int) -> dict:
    return {
        "canonical_knowledge_record_id": record["canonical_knowledge_record_id"],
        "record_version": record["record_version"],
        "supporting_source_id": record["supporting_source_id"],
        "supporting_source_version": record["supporting_source_version"],
        "character_span": f"{start + 1}-{end}",
    }


def _sentence_pair_fragments(record: dict) -> list[dict]:
    text = record["text"]
    matches = list(re.finditer(r"\S(?:.*?[.!?])(?=\s|$)", text))
    _require(matches and "".join(match.group(0) for match in matches).replace(" ", "") == text.replace(" ", ""),
             f"Record {record['canonical_knowledge_record_id']} cannot be split at sentence boundaries.")
    fragments: list[dict] = []
    for pair_index in range(0, len(matches), 2):
        first = matches[pair_index]
        last = matches[min(pair_index + 1, len(matches) - 1)]
        identifier = record["sentence_pair_fragment_id"]
        if len(matches) > 2:
            identifier = f"{identifier}-{pair_index // 2 + 1}"
        fragments.append(
            {
                "stable_retrieval_identifier": identifier,
                "canonical_knowledge_record_id": record["canonical_knowledge_record_id"],
                "text": text[first.start():last.end()],
                "provenance_link": _character_provenance(record, first.start(), last.end()),
                "collection_membership": "derived retrieval-side artifact; not a canonical knowledge collection member",
            }
        )
    return fragments


def _fixed_limit_fragments(record: dict, limit: int = 72) -> list[dict]:
    text = record["text"]
    fragments: list[dict] = []
    start = 0
    sequence = 1
    prefix = record["sentence_pair_fragment_id"]
    while start < len(text):
        if len(text) - start <= limit:
            end = len(text)
        else:
            delimiter = text.rfind(" ", start, start + limit + 1)
            if delimiter >= start:
                end = delimiter
            else:
                following = text.find(" ", start + limit)
                end = len(text) if following == -1 else following
        _require(end > start, f"The fixed boundary rule made no progress for record {record['canonical_knowledge_record_id']}.")
        fragments.append(
            {
                "stable_retrieval_identifier": f"{prefix}-72-{sequence}",
                "canonical_knowledge_record_id": record["canonical_knowledge_record_id"],
                "text": text[start:end],
                "provenance_link": _character_provenance(record, start, end),
                "collection_membership": "derived retrieval-side artifact; not a canonical knowledge collection member",
            }
        )
        start = end + 1 if end < len(text) and text[end] == " " else end
        sequence += 1
    return fragments


def _build_boundary_comparison(fixture: dict) -> dict:
    """Derive the complete comparison from the supplied fixture without writing it."""
    contract_value = fixture.get("retrieval_contract")
    records_value = fixture.get("canonical_knowledge_records")
    configurations_value = fixture.get("chunking_configurations")
    cases_value = fixture.get("evaluation_cases")
    if not isinstance(contract_value, dict):
        raise WorkflowError("The retrieval contract is missing.")
    if not isinstance(records_value, list) or not records_value or not all(isinstance(item, dict) for item in records_value):
        raise WorkflowError("Canonical knowledge records are missing or malformed.")
    if not isinstance(configurations_value, list) or len(configurations_value) != 2 or not all(isinstance(item, dict) for item in configurations_value):
        raise WorkflowError("Exactly two well-formed chunking configurations are required.")
    if not isinstance(cases_value, list) or not cases_value or not all(isinstance(item, dict) for item in cases_value):
        raise WorkflowError("Evaluation cases are missing or malformed.")
    contract = cast(dict[str, Any], contract_value)
    records = cast(list[dict[str, Any]], records_value)
    configurations = cast(list[dict[str, Any]], configurations_value)
    cases = cast(list[dict[str, Any]], cases_value)

    declared_fields = contract.get("declared fields")
    if not isinstance(declared_fields, dict):
        raise WorkflowError("The retrieval contract lacks its nine declared fields.")
    _require(
        set(declared_fields) == RETRIEVAL_CONTRACT_FIELDS,
        "The retrieval contract must contain the nine fields declared by Module 04 theory Section 1.1.",
    )
    roles = contract.get("retrieval configuration roles")
    _require(
        roles == {
            "experiment-baseline retrieval configuration": "lexical retrieval",
            "candidate retrieval configuration": "embedding-based retrieval",
        },
        "The retrieval configuration roles are not the declared Laboratory 04 roles.",
    )
    for case in cases:
        operation_input = case.get("operation_input", {})
        evaluator_only = case.get("evaluator_only_information", {})
        _require("evaluator-only expected result" not in operation_input,
                 f"{case.get('evaluation_case_id', 'Evaluation case')} exposes evaluator-only information to the retrieval operation.")
        _require("evaluator-only expected result" in evaluator_only,
                 f"{case.get('evaluation_case_id', 'Evaluation case')} lacks an evaluator-only expected result.")

    configuration_results = []
    for configuration in configurations:
        identifier = configuration.get("chunking_configuration_id")
        if identifier == "sentence-pair-v1":
            source_fragments = [fragment for record in records for fragment in _sentence_pair_fragments(record)]
        elif identifier == "fixed-72-v1":
            source_fragments = [fragment for record in records for fragment in _fixed_limit_fragments(record)]
        else:
            raise WorkflowError(f"Unsupported chunking configuration {identifier}.")
        configuration_results.append({**configuration, "source_fragments": source_fragments})

    record_manifest = [
        {
            "canonical_knowledge_record_id": record["canonical_knowledge_record_id"],
            "record_version": record["record_version"],
            "supporting_source_id": record["supporting_source_id"],
            "supporting_source_version": record["supporting_source_version"],
            "supplied_seed_record": True,
            "student_generated": False,
            "student_approved": False,
        }
        for record in records
    ]
    return {
        "schema_version": "1.0",
        "retrieval_contract": contract,
        "canonical_knowledge_collection_version": declared_fields["canonical knowledge collection version"],
        "canonical_knowledge_records": record_manifest,
        "evaluation_cases": cases,
        "chunking_configuration_results": configuration_results,
    }

def prepare_boundary_comparison(*, fixture_path: Path, report_dir: Path) -> Path:
    """Apply both supplied chunking configurations and preserve every provenance link."""
    result = _build_boundary_comparison(_read_fixture(fixture_path))
    output = report_dir / STAGE_B_DIRECTORY / BOUNDARY_COMPARISON_FILENAME
    _write_new_output(output, json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return output


def _require_expected_comparison(comparison: object, fixture_path: Path) -> dict:
    expected = _build_boundary_comparison(_read_fixture(fixture_path))
    _require(
        isinstance(comparison, dict)
        and json.dumps(comparison, sort_keys=True) == json.dumps(expected, sort_keys=True),
        "The boundary comparison does not match the supplied fixture.",
    )
    return expected


def record_boundary_decision(
    *,
    report_dir: Path,
    selected_chunking_configuration_id: str,
    rationale: str,
    student: str,
    fixture_path: Path = DEFAULT_STAGE_B_FIXTURE,
) -> Path:
    """Record, without choosing, the engineering team's boundary decision."""
    comparison_path = report_dir / STAGE_B_DIRECTORY / BOUNDARY_COMPARISON_FILENAME
    try:
        comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Cannot read the boundary comparison: {exc}") from exc
    expected = _require_expected_comparison(comparison, fixture_path)
    available = {
        item["chunking_configuration_id"]
        for item in expected["chunking_configuration_results"]
    }
    _require(selected_chunking_configuration_id in available,
             f"Unknown chunking configuration {selected_chunking_configuration_id}.")
    _require(bool(rationale.strip()), "The boundary-decision rationale is required.")
    _require(bool(student.strip()), "The student identifier is required.")

    output = report_dir / STAGE_B_DIRECTORY / BOUNDARY_DECISION_FILENAME
    _require(not output.exists(), f"Boundary decision already exists at {output}.")
    decision = {
        "schema version": "1.0",
        "selected chunking configuration": selected_chunking_configuration_id,
        "selected retrieval-unit definition": f"source fragment under {selected_chunking_configuration_id}",
        "decision actor": "the student acting as the engineering team",
        "decision boundary": "meaning preservation required by the declared evaluation cases",
        "rationale": rationale.strip(),
        "recorded by": student.strip(),
        "authority boundary": "does not authorize a change to the canonical knowledge collection",
    }
    _write_new_output(output, yaml.safe_dump(decision, sort_keys=False, allow_unicode=True))
    return output


def verify_stage_b(*, report_dir: Path, fixture_path: Path = DEFAULT_STAGE_B_FIXTURE) -> dict:
    """Verify Stage B evidence without substituting for the human decision."""
    stage_directory = report_dir / STAGE_B_DIRECTORY
    comparison_path = stage_directory / BOUNDARY_COMPARISON_FILENAME
    decision_path = stage_directory / BOUNDARY_DECISION_FILENAME
    try:
        comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
        decision = yaml.safe_load(decision_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise WorkflowError(f"Cannot read the Laboratory 04 Stage B evidence: {exc}") from exc
    expected = _require_expected_comparison(comparison, fixture_path)
    _require(isinstance(decision, dict), "The boundary decision must be a mapping.")
    identifiers = {item["chunking_configuration_id"] for item in expected["chunking_configuration_results"]}
    selected = decision.get("selected chunking configuration")
    _require(isinstance(selected, str) and selected in identifiers,
             "The boundary decision selects an unknown chunking configuration.")
    _require(decision.get("selected retrieval-unit definition") == f"source fragment under {selected}",
             "The selected retrieval-unit definition does not match the selected chunking configuration.")
    _require(bool(str(decision.get("rationale", "")).strip()), "The boundary decision lacks a rationale.")
    return {
        "outcome": "passed",
        "selected chunking configuration": selected,
        "verification boundary": "structural consistency; no human boundary decision",
    }


def validate_lab04_report(*, report_dir: Path) -> dict:
    """Validate the public Laboratory 04 report and evidence inventory."""
    checks: list[dict[str, str]] = []

    def check(check_id: str, action) -> None:
        try:
            message = action()
        except Exception as exc:  # noqa: BLE001 - collect every report defect
            checks.append({"check_id": check_id, "status": "failed", "message": str(exc)})
        else:
            checks.append({"check_id": check_id, "status": "passed", "message": message})

    report_path = report_dir / "REPORT.md"
    try:
        text = report_path.read_text(encoding="utf-8")
    except OSError:
        text = ""

    def check_headings() -> str:
        _require(report_path.is_file(), "REPORT.md is required.")
        headings = re.findall(r"^## (.+?)\s*$", text, flags=re.MULTILINE)
        _require(
            headings == list(LAB04_REPORT_HEADINGS),
            "REPORT.md must contain the exact required report headings in order.",
        )
        return "required report headings are present in order"

    def check_internal_vocabulary() -> str:
        internal_term = re.search(
            r"(?<![\w-])(?:Authoring\s+)?Stage\s+(?:B|C1|C2|C3)\b",
            text,
            flags=re.IGNORECASE,
        )
        _require(internal_term is None, "Internal course-development vocabulary is not permitted in the report.")
        return "no internal course-development vocabulary is present"

    def check_identity() -> str:
        fork = re.search(r"https://github\.com/([^/\s]+)/([^\s)]+)", text)
        _require(fork is not None, "The report identity section must contain the student's GitHub fork URL.")
        _require(fork.group(1).lower() != "sobol-mo", "The fork URL must identify the student's fork.")
        branch = re.search(r"^\s*[-*]?\s*Особиста гілка:\s*`?([^`\s]+)`?\s*$", text, re.MULTILINE)
        _require(branch is not None, "The report identity section must contain a personal branch.")
        _require(branch.group(1).lower() not in {"main", "master"}, "The personal branch must not be main or master.")
        return "fork URL and personal branch are recorded"

    def check_completion() -> str:
        completion = re.search(
            r"^\s*[-*]?\s*Статус завершення:\s*`?(complete|honest-partial)`?\s*$",
            text,
            re.MULTILINE,
        )
        _require(
            completion is not None,
            "The report identity section must record the completion state `complete` or `honest-partial`.",
        )
        return "the completion state is recorded"

    def check_data_uri() -> str:
        _require("data:image/" not in text.lower(), "REPORT.md must not contain a data URI.")
        return "the source report embeds no data URIs"

    def check_screenshots() -> str:
        image_targets = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
        expected_targets = [f"screenshots/{name}" for name in LAB04_REPORT_SCREENSHOTS]
        _require(
            image_targets == expected_targets,
            "REPORT.md must contain exactly these relative screenshot links in order: "
            + ", ".join(LAB04_REPORT_SCREENSHOTS),
        )
        screenshot_dir = report_dir / "screenshots"
        missing = [name for name in LAB04_REPORT_SCREENSHOTS[:-1] if not (screenshot_dir / name).is_file()]
        _require(not missing, "Required checkpoint screenshot files are missing: " + ", ".join(missing))
        actual = {path.name for path in screenshot_dir.glob("*.png")} if screenshot_dir.is_dir() else set()
        unexpected = sorted(actual - set(LAB04_REPORT_SCREENSHOTS))
        _require(not unexpected, "Unexpected screenshot files are present: " + ", ".join(unexpected))
        return "six exact relative links and five pre-verification screenshot files are present"

    def check_evidence() -> str:
        missing = [relative for relative in LAB04_REQUIRED_EVIDENCE if not (report_dir / relative).is_file()]
        _require(not missing, "Required Laboratory 04 evidence is missing: " + ", ".join(missing))
        return "all required workflow evidence and the final configuration decision are present"

    check("report-headings", check_headings)
    check("internal-vocabulary", check_internal_vocabulary)
    check("report-identity", check_identity)
    check("report-completion", check_completion)
    check("report-data-uri", check_data_uri)
    check("report-screenshots", check_screenshots)
    check("stage-evidence", check_evidence)
    return {
        "schema_version": "1.0",
        "lab_id": "lab04",
        "status": "passed" if all(item["status"] == "passed" for item in checks) else "failed",
        "checks": checks,
    }


def verify_lab04(*, report_dir: Path, final_commit: str) -> dict:
    """Bind complete Laboratory 04 evidence to an exact current branch head."""
    validation = validate_lab04_report(report_dir=report_dir)
    checks = list(validation["checks"])

    def check_final_commit() -> str:
        _require(
            re.fullmatch(r"[0-9a-f]{40}", final_commit) is not None,
            "Final student commit must be a full lowercase 40-character Git hash.",
        )
        try:
            git_root = Path(subprocess.run(
                ["git", "-C", str(report_dir), "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()).resolve()
            resolved = subprocess.run(
                ["git", "-C", str(git_root), "rev-parse", "--verify", f"{final_commit}^{{commit}}"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            head = subprocess.run(
                ["git", "-C", str(git_root), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise WorkflowError("Final student commit is missing or unresolvable in the report repository.") from exc
        _require(resolved == final_commit, "Final student commit did not resolve to the exact supplied hash.")
        _require(resolved == head, "Final student commit must be the current branch head.")
        try:
            report_relative = report_dir.resolve().relative_to(git_root).as_posix()
        except ValueError as exc:
            raise WorkflowError("Laboratory 04 report directory is outside the final commit repository.") from exc
        changed = subprocess.run(
            ["git", "-C", str(git_root), "diff", "--name-only", resolved, "--", report_relative],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        untracked = subprocess.run(
            ["git", "-C", str(git_root), "ls-files", "--others", "--exclude-standard", "--", report_relative],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        allowed = {
            f"{report_relative}/verification-report.json",
            f"{report_relative}/screenshots/{LAB04_REPORT_SCREENSHOTS[-1]}",
            f"{report_relative}/submission/REPORT.md",
        }
        drift = sorted({*changed, *untracked} - allowed)
        _require(not drift, "Laboratory 04 evidence changed after the final commit: " + ", ".join(drift))
        return f"exact final commit {resolved} is the current branch head"

    try:
        message = check_final_commit()
    except Exception as exc:  # noqa: BLE001 - write a complete verification report on failure
        checks.insert(0, {"check_id": "final-commit", "status": "failed", "message": str(exc)})
    else:
        checks.insert(0, {"check_id": "final-commit", "status": "passed", "message": message})

    verification = {
        "schema_version": "1.0",
        "lab_id": "lab04",
        "outcome": "passed" if all(item["status"] == "passed" for item in checks) else "failed",
        "final_commit": final_commit,
        "checks": checks,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    output = report_dir / "verification-report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(verification, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return verification
