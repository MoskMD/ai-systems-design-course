"""Fixed continuation of the same retained read; no action-selection model calls."""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from .lab06 import _write
from .lab07_loop import (CONTEXT_BUDGET, _call, _generation_request, _selection,
                         _validate_generation, _validated_first_read)
from .workflow import WorkflowError

FIXED_OUTPUTS = ('attempt.json', 'selection-record.json', 'trace.json', 'run-metadata.json',
                 'generation/request.json', 'generation/provider-response.json',
                 'generation/call-metadata.json', 'generation/outcome.json')


def run_fixed(*, first_action_dir: Path, model_id: str, output_dir: Path,
              runner=subprocess.run) -> dict:
    """Reuse validation, admission, generation request, transport and outcome checks."""
    if not isinstance(model_id, str) or not model_id.strip():
        raise WorkflowError('An explicit fixed-path model id is required.')
    if any(os.path.lexists(output_dir/name) for name in FIXED_OUTPUTS):
        raise WorkflowError('Fixed outputs are create-only; an output already exists.')
    first, corpus, query, candidates = _validated_first_read(first_action_dir)
    _write(output_dir/'attempt.json', {'requested_model': model_id, 'first_action_capture': first,
        'source_resource': corpus, 'context_budget_characters': CONTEXT_BUDGET,
        'attempts_per_call': 1, 'acquisition': 'prompt-schema; no CLI repair turn',
        'settings': {'useG1Credits': False},
        'predefined_path': 'admit retained read candidates; generate once; terminate'})
    started = time.monotonic()
    failure = None
    trace = {'control': 'predefined application path; no model action request',
             'permission': {'allowed': True, 'reason': 'permitted read-only generation'},
             'executed input': None, 'returned result': None}
    calls = 0
    try:
        selection = _selection(candidates, query, corpus)
        _write(output_dir/'selection-record.json', selection)
        evidence = selection['supplied source evidence']
        request = _generation_request(evidence)
        trace['executed input'] = request
        calls = 1
        outcome = _call(request, model_id=model_id, folder=output_dir/'generation', runner=runner)
        _validate_generation(outcome, evidence)
        _write(output_dir/'generation/outcome.json', outcome)
        trace['returned result'] = outcome
    except WorkflowError as exc:
        failure = str(exc)
        trace['execution failure'] = failure
    _write(output_dir/'trace.json', trace)
    status = 'execution failure' if failure else 'fixed path completed'
    _write(output_dir/'run-metadata.json', {'status': status, 'failure': failure,
        'requested_model': model_id, 'new_provider_invocations': calls, 'additional_decisions': 0,
        'semantic_judgment': 'not performed', 'task_accomplishment': 'not judged',
        'evidence_kind': 'live fixed continuation from retained first-action capture'
                         if runner is subprocess.run else 'injected runner; not live attestation',
        'continuation_seconds': time.monotonic() - started,
        'timing_boundary': 'Continuation after capture validation; excludes predecessor execution and human evaluation.',
        'consumption': 'Raw envelopes retained; unavailable usage is unknown, not zero.'})
    if failure:
        raise WorkflowError(failure + ' Preserve the attempt; stop without automatic retry.')
    return {'status': status, 'metadata': str(output_dir/'run-metadata.json')}
