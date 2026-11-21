"""Controlled diagnostic transports; no paid calls and no model-quality claims."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

from .lab06 import _read, _write
from .lab07 import DEFAULT_CORPUS
from .lab07_loop import CONTEXT_BUDGET, _validated_first_read, continue_adaptive
from .workflow import WorkflowError


def _response(action):
    return SimpleNamespace(returncode=0, stderr='', stdout=json.dumps({
        'status': 'SUCCESS', 'response': json.dumps(action)}))


def run_boundary_checks(*, first_action_dir: Path, output_dir: Path) -> dict:
    """Exercise the normal permission gate using a declared injected request."""
    if any(os.path.lexists(output_dir/name) for name in ('attempt.json', 'denial', 'delivery', 'interrupted', 'summary.json')):
        raise WorkflowError('Boundary-check outputs are create-only; an output already exists.')
    first, corpus, _, _ = _validated_first_read(first_action_dir)
    _write(output_dir/'attempt.json', {'evidence_kind': 'controlled diagnostic; injected transport, not live model behavior',
        'first_action_capture': first, 'source_resource': corpus, 'live_provider_invocations': 0})
    action = {'operation': 'canonical write', 'arguments': {}}
    result = continue_adaptive(first_action_dir=first_action_dir, model_id='diagnostic-injected',
        output_dir=output_dir/'denial', runner=lambda *a, **kw: _response(action))
    trace = _read(output_dir/'denial/decision-1/trace.json')
    if (result['status'] != 'permission denied' or trace['permission']['allowed'] is not False
            or trace['executed input'] is not None or trace['returned result'] is not None
            or _read(DEFAULT_CORPUS) != corpus):
        raise WorkflowError('Permission boundary check failed; preserve all diagnostic outputs.')
    delivery_choices = iter([
        {'operation': 'retrieval operation', 'arguments': {
            'text query': 'query embedding vector comparison', 'collection': corpus['collection_version']}},
        {'operation': 'stop', 'arguments': {}}])
    continue_adaptive(first_action_dir=first_action_dir, model_id='diagnostic-injected',
        output_dir=output_dir/'delivery', context_budget_characters=150,
        runner=lambda *a, **kw: _response(next(delivery_choices)))
    selection = _read(output_dir/'delivery/decision-2/selection-record.json')
    request = _read(output_dir/'delivery/decision-2/request.json')
    retained = _read(output_dir/'delivery/retained-state.json')
    omitted = next(u['text'] for u in corpus['fragments'] if u['retrieval_unit_id'] == 'AP-2')
    if ([u['retrieval unit id'] for u in selection['supplied source evidence']] != ['AP-1']
            or request['supplied source evidence'] != selection['supplied source evidence']
            or omitted in json.dumps(request) or omitted not in json.dumps(retained)):
        raise WorkflowError('Retained-versus-delivered check failed; preserve diagnostic outputs.')
    def interrupted(*args, **kwargs):
        raise subprocess.TimeoutExpired('diagnostic-injected', 330, output=b'controlled partial return')

    try:
        continue_adaptive(first_action_dir=first_action_dir, model_id='diagnostic-injected',
            output_dir=output_dir/'interrupted', runner=interrupted)
    except WorkflowError:
        failed = _read(output_dir/'interrupted/run-metadata.json')
        if (failed['status'] != 'execution failure' or failed['new_provider_invocations'] != 1
                or failed['task_accomplishment'] != 'not judged'):
            raise WorkflowError('Honest-stop check failed; preserve diagnostic outputs.')
    else:
        raise WorkflowError('Interrupted diagnostic unexpectedly continued; preserve outputs.')
    summary = {'status': 'boundary checks passed',
        'evidence_kind': 'controlled diagnostic; injected transport, not live model behavior',
        'live_provider_invocations': 0, 'permission_denial': 'passed',
        'retained_versus_delivered': 'passed', 'honest_stop': 'passed',
        'diagnostic_budget_characters': 150,
        'normal_route_budget_characters': CONTEXT_BUDGET,
        'semantic_judgment': 'not performed', 'task_accomplishment': 'not judged'}
    _write(output_dir/'summary.json', summary)
    return summary
