"""Laboratory 05 query-rewriting and retrieval-unit selection slices."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

from .workflow import WorkflowError


QUERY_REWRITING_DIRECTORY = "query-rewriting"
QUERY_REWRITING_FILENAME = "query-rewriting-results.json"
DEFAULT_STAGE_B_FIXTURE = Path(__file__).resolve().parents[2] / "cases" / "lab05" / "query-rewriting-cases.json"
MEANING_FIELDS = {"requested concept", "requested relation", "scope restriction"}

RETRIEVAL_UNIT_SELECTION_DIRECTORY = "retrieval-unit-selection"
SELECTION_RECORD_FILENAME = "selection-record.json"
DEFAULT_RETRIEVAL_UNIT_SELECTION_FIXTURE = (
    Path(__file__).resolve().parents[2] / "cases" / "lab05" / "retrieval-unit-selection-cases.json"
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise WorkflowError(message)


def _read_fixture(path: Path) -> dict[str, Any]:
    try:
        fixture = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Cannot read the Laboratory 05 query-rewriting fixture: {exc}") from exc
    _require(isinstance(fixture, dict), "The Laboratory 05 query-rewriting fixture must be an object.")
    _require(fixture.get("schema_version") == "1.0", "Unsupported Laboratory 05 query-rewriting fixture version.")
    return fixture


def _build_query_rewriting_result(fixture: dict[str, Any]) -> dict[str, Any]:
    rule = fixture.get("query_rewriting_rule")
    cases = fixture.get("cases")
    _require(isinstance(rule, dict) and rule.get("rule_id") == "QR-05-v1", "The query-rewriting rule must be QR-05-v1.")
    _require(isinstance(cases, list) and len(cases) == 2 and all(isinstance(item, dict) for item in cases),
             "Exactly one solvable rewrite and one unsolvable rewrite are required.")
    typed_rule = cast(dict[str, Any], rule)
    typed_cases = cast(list[dict[str, Any]], cases)
    _require({item.get("case_id") for item in typed_cases} == {"solvable-rewrite", "unsolvable-rewrite"},
             "The Laboratory 05 query-rewriting cases are incomplete.")

    results: list[dict[str, Any]] = []
    for case in typed_cases:
        case_id = case["case_id"]
        information_need = case.get("information_need")
        requested_meaning = case.get("requested_meaning")
        _require(bool(isinstance(information_need, str) and information_need.strip()), f"{case_id} lacks an information need.")
        _require(isinstance(requested_meaning, dict) and set(requested_meaning) == MEANING_FIELDS,
                 f"{case_id} lacks the complete requested meaning.")
        typed_requested_meaning = cast(dict[str, Any], requested_meaning)
        identity_available = case.get("identity_available_inside_information_need")
        _require(isinstance(identity_available, bool),
                 f"{case_id} must declare identity availability inside the information need.")
        base = {"case id": case_id, "information need": information_need}

        if identity_available:
            rewritten = case.get("course_stipulated_rewritten_retrieval_input")
            rewritten_meaning = case.get("rewritten_meaning")
            _require(bool(isinstance(rewritten, str) and rewritten.strip()), "The solvable rewrite lacks its rewritten retrieval input.")
            _require(rewritten_meaning == typed_requested_meaning, "The solvable rewrite does not preserve the requested meaning.")
            _require(typed_requested_meaning["requested concept"] is not None,
                     "The solvable rewrite lacks the requested concept identity.")
            results.append({
                **base,
                "outcome": "rewritten retrieval input",
                "rewritten retrieval input": rewritten,
                "meaning preservation": typed_requested_meaning,
                "next operation": "accepted retrieval operation",
            })
        else:
            _require(typed_requested_meaning["requested concept"] is None,
                     "The unsolvable rewrite must identify the missing requested concept.")
            _require("course_stipulated_rewritten_retrieval_input" not in case,
                     "The unsolvable rewrite must not contain a rewritten retrieval input.")
            results.append({
                **base,
                "outcome": "unsolvable rewrite",
                "missing identity": "requested concept",
                "next operation": "stop before the accepted retrieval operation",
            })

    return {"schema_version": "1.0", "query-rewriting rule": typed_rule["rule_id"], "cases": results}


def apply_query_rewriting(*, fixture_path: Path, report_dir: Path) -> Path:
    """Apply QR-05-v1 to the supplied cases and create one inspectable result."""
    result = _build_query_rewriting_result(_read_fixture(fixture_path))
    output = report_dir / QUERY_REWRITING_DIRECTORY / QUERY_REWRITING_FILENAME
    output.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(output, flags, 0o666)
    except FileExistsError as exc:
        raise WorkflowError(f"Output already exists at {output}.") from exc
    except OSError as exc:
        raise WorkflowError(f"Cannot create output at {output}: {exc}") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return output


def verify_stage_b(*, fixture_path: Path, report_dir: Path) -> dict[str, Any]:
    """Recompute the two rewrite outcomes and reject changed evidence."""
    output = report_dir / QUERY_REWRITING_DIRECTORY / QUERY_REWRITING_FILENAME
    try:
        observed = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Cannot read the Laboratory 05 query-rewriting result: {exc}") from exc
    expected = _build_query_rewriting_result(_read_fixture(fixture_path))
    _require(
        json.dumps(observed, sort_keys=True) == json.dumps(expected, sort_keys=True),
        "The query-rewriting result does not match the supplied fixture.",
    )
    return {"outcome": "passed", "verified cases": len(expected["cases"])}


def _read_selection_fixture(path: Path) -> dict[str, Any]:
    try:
        fixture = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Cannot read the Laboratory 05 retrieval-unit selection fixture: {exc}") from exc
    _require(isinstance(fixture, dict), "The Laboratory 05 retrieval-unit selection fixture must be an object.")
    _require(fixture.get("schema_version") == "1.0", "Unsupported Laboratory 05 retrieval-unit selection fixture version.")
    return fixture


def _read_query_rewriting_result(report_dir: Path) -> dict[str, Any]:
    path = report_dir / QUERY_REWRITING_DIRECTORY / QUERY_REWRITING_FILENAME
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Cannot read the Laboratory 05 query-rewriting result: {exc}") from exc
    _require(isinstance(result, dict), "The Laboratory 05 query-rewriting result must be an object.")
    return result


def _solvable_text_query(query_rewriting_result: dict[str, Any]) -> str:
    cases = query_rewriting_result.get("cases")
    _require(isinstance(cases, list), "The query-rewriting result lacks cases.")
    typed_cases = cast(list[Any], cases)
    solvable = next(
        (
            item
            for item in typed_cases
            if isinstance(item, dict) and item.get("case id") == "solvable-rewrite"
        ),
        None,
    )
    _require(isinstance(solvable, dict), "The query-rewriting result lacks the solvable rewrite.")
    typed_solvable = cast(dict[str, Any], solvable)
    text_query = typed_solvable.get("rewritten retrieval input")
    _require(
        isinstance(text_query, str) and bool(text_query.strip()),
        "The solvable rewrite lacks a rewritten retrieval input for retrieval-unit selection.",
    )
    return cast(str, text_query)


def _build_selection_record(*, fixture: dict[str, Any], text_query: str) -> dict[str, Any]:
    criteria = fixture.get("retrieval_unit_admission_criteria")
    ranked = fixture.get("ranked_candidate_output")
    required_query = fixture.get("required_text_query")
    selection_id = fixture.get("selection_record_id")
    _require(isinstance(criteria, dict), "The selection fixture lacks retrieval-unit admission criteria.")
    typed_criteria = cast(dict[str, Any], criteria)
    _require(typed_criteria.get("rule_id") == "RUS-05-v1", "The retrieval-unit admission criteria must be RUS-05-v1.")
    _require(typed_criteria.get("criteria_order") == [
        "provenance-link resolution",
        "context-budget fit",
    ], "RUS-05-v1 must check provenance-link resolution before context-budget fit.")
    budget = typed_criteria.get("context_budget_characters")
    _require(isinstance(budget, int) and budget > 0, "RUS-05-v1 must declare a positive context budget.")
    _require(isinstance(required_query, str) and required_query == text_query,
             "The text query bound for selection must match the solvable rewritten retrieval input.")
    _require(isinstance(selection_id, str) and selection_id.strip(), "The selection fixture lacks a selection record id.")
    _require(isinstance(ranked, list) and ranked, "The selection fixture lacks a ranked candidate output.")
    typed_ranked = cast(list[Any], ranked)
    _require(all(isinstance(item, dict) for item in typed_ranked), "Every ranked candidate must be an object.")

    remaining = cast(int, budget)
    ranked_view: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []

    for index, raw_unit in enumerate(typed_ranked, start=1):
        unit = cast(dict[str, Any], raw_unit)
        unit_id = unit.get("retrieval_unit_id")
        text = unit.get("text")
        rank = unit.get("rank")
        provenance = unit.get("provenance_link")
        _require(isinstance(unit_id, str) and unit_id.strip(), f"Ranked candidate {index} lacks a retrieval unit id.")
        _require(isinstance(text, str) and text, f"{unit_id} lacks retrieval-unit text.")
        _require(rank == index, f"{unit_id} must appear in strict ranked order.")
        _require(isinstance(provenance, dict), f"{unit_id} lacks a provenance link object.")
        typed_provenance = cast(dict[str, Any], provenance)
        resolves = typed_provenance.get("resolves_to_registered_source_material")
        _require(isinstance(resolves, bool), f"{unit_id} must declare provenance-link resolution.")
        character_count = len(text)
        ranked_view.append({
            "rank": rank,
            "retrieval unit id": unit_id,
            "text": text,
            "text character count": character_count,
            "provenance link": {
                "record id": typed_provenance.get("record id"),
                "version": typed_provenance.get("version"),
                "sentences": typed_provenance.get("sentences"),
                "resolves to registered source material": resolves,
            },
        })

        if not resolves:
            exclusions.append({
                "retrieval unit id": unit_id,
                "failed criterion": "provenance-link resolution",
                "evaluated criteria": ["provenance-link resolution"],
                "remaining context budget characters before unit": remaining,
            })
            continue

        if character_count > remaining:
            exclusions.append({
                "retrieval unit id": unit_id,
                "failed criterion": "context-budget fit",
                "evaluated criteria": ["provenance-link resolution", "context-budget fit"],
                "remaining context budget characters before unit": remaining,
                "text character count": character_count,
            })
            continue

        remaining -= character_count
        selected.append({
            "retrieval unit id": unit_id,
            "text": text,
            "text character count": character_count,
            "provenance link": {
                "record id": typed_provenance.get("record id"),
                "version": typed_provenance.get("version"),
                "sentences": typed_provenance.get("sentences"),
                "resolves to registered source material": True,
            },
        })

    return {
        "schema_version": "1.0",
        "selection record id": selection_id,
        "retrieval-unit admission criteria": "RUS-05-v1",
        "context budget characters": budget,
        "text query": text_query,
        "ranked candidate output": ranked_view,
        "supplied source evidence": selected,
        "exclusions": exclusions,
        "remaining context budget characters": remaining,
        "next operation": "context construction",
        "authority boundary": "The selection record is not an authorization to change the canonical knowledge collection.",
    }


def apply_retrieval_unit_selection(*, fixture_path: Path, report_dir: Path) -> Path:
    """Apply RUS-05-v1 to one stipulated ranked candidate output bound to the solvable rewrite."""
    text_query = _solvable_text_query(_read_query_rewriting_result(report_dir))
    result = _build_selection_record(fixture=_read_selection_fixture(fixture_path), text_query=text_query)
    output = report_dir / RETRIEVAL_UNIT_SELECTION_DIRECTORY / SELECTION_RECORD_FILENAME
    output.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(output, flags, 0o666)
    except FileExistsError as exc:
        raise WorkflowError(f"Output already exists at {output}.") from exc
    except OSError as exc:
        raise WorkflowError(f"Cannot create output at {output}: {exc}") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return output


def verify_retrieval_unit_selection(*, fixture_path: Path, report_dir: Path) -> dict[str, Any]:
    """Recompute the selection record and reject changed evidence."""
    output = report_dir / RETRIEVAL_UNIT_SELECTION_DIRECTORY / SELECTION_RECORD_FILENAME
    try:
        observed = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Cannot read the Laboratory 05 selection record: {exc}") from exc
    text_query = _solvable_text_query(_read_query_rewriting_result(report_dir))
    expected = _build_selection_record(fixture=_read_selection_fixture(fixture_path), text_query=text_query)
    _require(
        json.dumps(observed, sort_keys=True) == json.dumps(expected, sort_keys=True),
        "The selection record does not match the supplied fixture and query-rewriting result.",
    )
    return {
        "outcome": "passed",
        "selected retrieval units": len(expected["supplied source evidence"]),
        "excluded retrieval units": len(expected["exclusions"]),
    }
