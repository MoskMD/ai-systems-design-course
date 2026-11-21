"""Adaptive continuation tests use injected transport, never live attestations."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from learning_project.lab07 import run_first_action


def response(value):
    return SimpleNamespace(returncode=0, stdout=json.dumps({
        'status': 'SUCCESS', 'response': json.dumps(value)}), stderr='')


def first_read(folder):
    run_first_action(model_id='test', output_dir=folder, runner=lambda *a, **kw: response({
        'operation': 'retrieval operation', 'arguments': {
            'text query': 'query embedding vector comparison', 'collection': 'S-AGENT/v1'}}))
    return folder


def load(path):
    return json.loads(path.read_text())


@pytest.mark.parametrize('action,status', [
    ({'operation': 'canonical write', 'arguments': {}}, 'permission denied'),
    ({'operation': 'stop', 'arguments': {}}, 'stop proposed'),
    ({'operation': 'retrieval operation', 'arguments': {'text query': 'zzzz-no-overlap', 'collection': 'S-AGENT/v1'}}, 'application decision limit reached'),
    ({'operation': 'retrieval operation', 'arguments': {'text query': 'query vector', 'collection': '../outside'}}, 'permission denied')])
def test_actual_choice_controls_denial_empty_return_and_bounded_stop(tmp_path, action, status):
    from learning_project.lab07_loop import continue_adaptive, MAX_DECISIONS
    first = first_read(tmp_path/'first')
    calls = []
    def provider(*a, **kw):
        calls.append(a)
        return response(action)
    out = tmp_path/'out'
    assert continue_adaptive(first_action_dir=first, model_id='test', output_dir=out, runner=provider)['status'] == status
    assert len(calls) == (MAX_DECISIONS if status == 'application decision limit reached' else 1)
    if status == 'application decision limit reached':
        assert load(out/'decision-2/request.json')['supplied source evidence'] == []
        assert load(out/'decision-1/trace.json')['returned result'] == []
    else:
        assert load(out/'decision-1/trace.json')['executed input'] is None


@pytest.mark.parametrize('kind', ['invalid-json', 'multiple', 'conflicting-structured', 'timeout', 'invalid-citation'])
def test_failed_generation_never_becomes_refusal_or_success(tmp_path, kind):
    import subprocess
    from learning_project.lab07_loop import continue_adaptive
    from learning_project.workflow import WorkflowError
    first = first_read(tmp_path/'first')
    calls = []
    def provider(*a, **kw):
        calls.append(a)
        if len(calls) == 1:
            return response({'operation': 'model-backed prerequisite-explanation operation', 'arguments': {}})
        if kind == 'timeout':
            raise subprocess.TimeoutExpired('agy', 330, output=b'partial')
        if kind == 'invalid-citation':
            return response({'outcome_type': 'generated prerequisite explanation',
                             'claims': [{'text': 'unsupported', 'fragment_ids': ['outside']}]})
        value = {'outcome_type': 'refusal', 'blocking_condition': 'insufficient supplied source evidence'}
        raw = response(value)
        env = json.loads(raw.stdout)
        if kind == 'invalid-json':
            env['response'] = 'not JSON'
        elif kind == 'multiple':
            env['response'] += ' ' + env['response']
        else:
            env['structured_output'] = {'other': 'object'}
        raw.stdout = json.dumps(env)
        return raw
    out = tmp_path/'out'
    with pytest.raises(WorkflowError):
        continue_adaptive(first_action_dir=first, model_id='test', output_dir=out, runner=provider)
    assert len(calls) == 2
    assert (out/'decision-1/generation/provider-response.json').is_file()
    assert not (out/'decision-1/generation/outcome.json').exists()
    assert load(out/'run-metadata.json')['status'] == 'execution failure'


def test_refusal_is_delivered_as_progress_not_evidence(tmp_path):
    from learning_project.lab07_loop import continue_adaptive
    first = first_read(tmp_path/'first')
    refusal = {'outcome_type': 'refusal', 'blocking_condition': 'insufficient supplied source evidence'}
    replies = iter([{'operation': 'model-backed prerequisite-explanation operation', 'arguments': {}}, refusal,
                    {'operation': 'stop', 'arguments': {}}])
    out = tmp_path/'out'
    continue_adaptive(first_action_dir=first, model_id='test', output_dir=out, runner=lambda *a, **kw: response(next(replies)))
    request = load(out/'decision-2/request.json')
    assert json.dumps(refusal) in request['task instruction']
    assert refusal not in request['supplied source evidence']
    assert load(out/'run-metadata.json')['task_accomplishment'] == 'not judged'


def test_budget_excluded_text_is_not_smuggled_into_progress(tmp_path, monkeypatch):
    import learning_project.lab07_loop as loop
    first = first_read(tmp_path/'first')
    monkeypatch.setattr(loop, 'CONTEXT_BUDGET', 150)
    out = tmp_path/'out'
    loop.continue_adaptive(first_action_dir=first, model_id='test', output_dir=out,
        runner=lambda *a, **kw: response({'operation': 'stop', 'arguments': {}}))
    selection = load(out/'decision-1/selection-record.json')
    assert [u['retrieval unit id'] for u in selection['supplied source evidence']] == ['AP-1']
    assert selection['exclusions'][0]['retrieval unit id'] == 'AP-2'
    excluded = next(u['text'] for u in selection['ranked candidate output'] if u['retrieval unit id'] == 'AP-2')
    assert excluded not in json.dumps(load(out/'decision-1/request.json'))
    assert excluded in json.dumps(load(out/'retained-state.json'))


@pytest.mark.parametrize('name', ['attempt.json', 'retained-state.json', 'run-metadata.json',
    *[f'decision-{n}/{f}' for n in range(1, 4) for f in ('selection-record.json', 'request.json',
    'provider-response.json', 'call-metadata.json', 'action.json', 'trace.json', 'generation/request.json',
    'generation/provider-response.json', 'generation/call-metadata.json', 'generation/outcome.json')]])
@pytest.mark.parametrize('kind', ['regular', 'dangling', 'existing-target'])
def test_all_output_collisions_stop_before_provider(tmp_path, name, kind):
    from learning_project.lab07_loop import continue_adaptive
    from learning_project.workflow import WorkflowError
    first = first_read(tmp_path/'first')
    out = tmp_path/'out'
    path = out/name
    path.parent.mkdir(parents=True, exist_ok=True)
    target = tmp_path/'outside'
    if kind == 'regular':
        path.write_text('unchanged')
    else:
        if kind == 'existing-target':
            target.write_text('unchanged')
        try:
            path.symlink_to(target)
        except OSError:
            pytest.skip('Host does not permit test symlinks')
    def forbidden(*a, **kw):
        pytest.fail('No provider allowed after collision')
    with pytest.raises(WorkflowError, match='already exists'):
        continue_adaptive(first_action_dir=first, model_id='test', output_dir=out, runner=forbidden)
    if target.exists():
        assert target.read_text() == 'unchanged'
    if kind == 'regular':
        assert path.read_text() == 'unchanged'


def test_documented_relative_cli_path_executes_in_fresh_workspace(tmp_path, monkeypatch, capsys):
    from learning_project.cli import main
    import learning_project.lab07_loop as loop
    first_read(tmp_path/'reports/lab07/first-read')
    actual = loop.continue_adaptive
    def injected(**kwargs):
        return actual(**kwargs, runner=lambda *a, **kw: response({'operation': 'stop', 'arguments': {}}))
    monkeypatch.setattr(loop, 'continue_adaptive', injected)
    monkeypatch.chdir(tmp_path)
    assert main(['lab07', 'continue-adaptive', '--first-action-dir', 'reports/lab07/first-read',
                 '--model', 'test', '--output-dir', 'reports/lab07/adaptive']) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'stop proposed'
    assert load(tmp_path/'reports/lab07/adaptive/run-metadata.json')['evidence_kind'] == 'injected runner; not live attestation'


def test_admission_rejects_bad_locator_before_considering_budget():
    from learning_project.lab07_loop import _selection
    from learning_project.lab07 import DEFAULT_CORPUS
    corpus = load(DEFAULT_CORPUS)
    unit = dict(rank=1, **corpus['fragments'][0])
    unit['text'] = 'x' * 1000
    unit['provenance_link'] = {**unit['provenance_link'], 'location': 'nonexistent'}
    selected = _selection([unit], 'query', corpus)
    assert selected['supplied source evidence'] == []
    assert selected['exclusions'][0]['failed criterion'] == 'provenance-link resolution'
    assert selected['exclusions'][0]['evaluated criteria'] == ['provenance-link resolution']


def test_changed_predecessor_metadata_is_rejected_before_provider(tmp_path):
    from learning_project.lab07_loop import continue_adaptive
    from learning_project.workflow import WorkflowError
    first = first_read(tmp_path/'first')
    meta = load(first/'run-metadata.json')
    meta['status'] = 'execution failure'
    (first/'run-metadata.json').write_text(json.dumps(meta))
    def forbidden(*a, **kw):
        pytest.fail('No provider allowed after inconsistent predecessor')
    with pytest.raises(WorkflowError, match='First-action metadata'):
        continue_adaptive(first_action_dir=first, model_id='test', output_dir=tmp_path/'out', runner=forbidden)
    assert not (tmp_path/'out/attempt.json').exists()


def test_cli_continuation_requires_existing_first_action(tmp_path, capsys):
    from learning_project.cli import main
    assert main(['lab07', 'continue-adaptive', '--first-action-dir', str(tmp_path/'missing'),
                 '--model', 'test', '--output-dir', str(tmp_path/'out')]) == 1
    assert 'Cannot read' in capsys.readouterr().err
    assert not (tmp_path/'out/attempt.json').exists()


def test_generation_failure_preserves_permission_and_actual_invocation(tmp_path):
    from learning_project.lab07_loop import continue_adaptive
    from learning_project.workflow import WorkflowError
    first = first_read(tmp_path/'first')
    replies = iter([response({'operation': 'model-backed prerequisite-explanation operation', 'arguments': {}}),
                    SimpleNamespace(returncode=0, stdout=json.dumps({'status': 'ERROR', 'error': '503'}), stderr='')])
    out = tmp_path/'out'
    with pytest.raises(WorkflowError, match='stop without automatic retry'):
        continue_adaptive(first_action_dir=first, model_id='test', output_dir=out,
                          runner=lambda *a, **kw: next(replies))
    trace = load(out/'decision-1/trace.json')
    assert trace['permission']['allowed'] is True
    assert trace['executed input'] == load(out/'decision-1/generation/request.json')
    assert trace['execution failure']
    assert trace['returned result'] is None
    assert not (out/'decision-1/generation/outcome.json').exists()
    assert load(out/'run-metadata.json')['status'] == 'execution failure'
    assert load(out/'run-metadata.json')['new_provider_invocations'] == 2


def test_admission_generation_feedback_and_model_stop_continue_same_task(tmp_path):
    from learning_project.lab07_loop import continue_adaptive
    first = first_read(tmp_path/'first')
    before = {p.name: p.read_bytes() for p in first.iterdir()}
    generated = {'outcome_type': 'generated prerequisite explanation', 'claims': [{
        'text': 'A query embedding represents the question as a vector for comparison with stored vectors.',
        'fragment_ids': ['AP-2']}]}
    values = iter([{'operation': 'model-backed prerequisite-explanation operation', 'arguments': {}},
                   generated, {'operation': 'stop', 'arguments': {}}])
    calls = []
    def provider(command, **kwargs):
        calls.append(command)
        return response(next(values))
    out = tmp_path/'adaptive'
    result = continue_adaptive(first_action_dir=first, model_id='test', output_dir=out, runner=provider)
    assert result['status'] == 'stop proposed'
    selection = load(out/'decision-1/selection-record.json')
    assert {u['retrieval unit id'] for u in selection['supplied source evidence']} == {'AP-1', 'AP-2'}
    first_request = load(out/'decision-1/request.json')
    generation_request = load(out/'decision-1/generation/request.json')
    feedback_request = load(out/'decision-2/request.json')
    for request in [first_request, generation_request, feedback_request]:
        assert set(request) == {'task instruction', 'supplied source evidence', 'output contract'}
        assert 'Explain why a query embedding is needed for embedding-based retrieval in this teaching route.' in request['task instruction']
        assert request['supplied source evidence'] == selection['supplied source evidence']
    assert '"task-progress data"' in feedback_request['task instruction']
    assert json.dumps(generated, ensure_ascii=False) in feedback_request['task instruction']
    assert generated not in feedback_request['supplied source evidence']
    assert load(out/'decision-1/generation/outcome.json') == generated
    assert load(out/'decision-1/trace.json')['permission']['allowed'] is True
    assert load(out/'decision-1/trace.json')['executed input'] == generation_request
    meta = load(out/'run-metadata.json')
    assert meta['semantic_judgment'] == 'not performed'
    assert meta['task_accomplishment'] == 'not judged'
    assert meta['new_provider_invocations'] == 3
    assert meta['evidence_kind'] == 'injected runner; not live attestation'
    assert len(calls) == 3
    assert all('--json-schema' not in command for command in calls)
    assert all(json.loads(command[command.index('--settings')+1]) == {'useG1Credits': False} for command in calls)
    assert {p.name: p.read_bytes() for p in first.iterdir()} == before
