"""Laboratory 05 Stage B query-rewriting slice."""

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
