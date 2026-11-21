"""Comparison checks inject transport; live evidence is collected separately."""
import json
from types import SimpleNamespace

import pytest

from learning_project.lab07 import run_first_action


def load(path):
    return json.loads(path.read_text())


def response(value):
    return SimpleNamespace(returncode=0, stdout=json.dumps({
        'status': 'SUCCESS', 'response': json.dumps(value)}), stderr='')


def first_read(folder):
    run_first_action(model_id='test', output_dir=folder, runner=lambda *a, **kw: response({
        'operation': 'retrieval operation', 'arguments': {
            'text query': 'query embedding vector comparison', 'collection': 'S-AGENT/v1'}}))
    return folder


def test_fixed_path_uses_shared_admission_and_exact_generation_request(tmp_path):
    from learning_project.lab07_comparison import run_fixed
    from learning_project.lab07_loop import continue_adaptive
    first = first_read(tmp_path/'first')
    refusal = {'outcome_type': 'refusal', 'blocking_condition': 'insufficient supplied source evidence'}
    replies = iter([{'operation': 'model-backed prerequisite-explanation operation', 'arguments': {}},
                    refusal, {'operation': 'stop', 'arguments': {}}])
    adaptive, fixed = tmp_path/'adaptive', tmp_path/'fixed'
    continue_adaptive(first_action_dir=first, model_id='test', output_dir=adaptive,
                      runner=lambda *a, **kw: response(next(replies)))
    calls = []
    def provider(command, **kwargs):
        calls.append(command)
        return response(refusal)
    result = run_fixed(first_action_dir=first, model_id='test', output_dir=fixed, runner=provider)
    assert result['status'] == 'fixed path completed'
    assert len(calls) == 1
    assert load(fixed/'generation/request.json') == load(adaptive/'decision-1/generation/request.json')
    assert load(fixed/'selection-record.json') == load(adaptive/'decision-1/selection-record.json')
    meta = load(fixed/'run-metadata.json')
    assert meta['new_provider_invocations'] == 1
    assert meta['additional_decisions'] == 0
    assert meta['semantic_judgment'] == 'not performed'
    assert meta['task_accomplishment'] == 'not judged'
    assert meta['evidence_kind'] == 'injected runner; not live attestation'
    assert load(fixed/'generation/outcome.json') == refusal


@pytest.mark.parametrize('name', [
    'attempt.json', 'selection-record.json', 'trace.json', 'run-metadata.json',
    'generation/request.json', 'generation/provider-response.json',
    'generation/call-metadata.json', 'generation/outcome.json'])
@pytest.mark.parametrize('kind', ['regular', 'dangling', 'existing-target'])
def test_fixed_collision_never_calls_provider_or_changes_target(tmp_path, name, kind):
    from learning_project.lab07_comparison import run_fixed
    from learning_project.workflow import WorkflowError
    first = first_read(tmp_path/'first')
    output = tmp_path/'out'
    path, target = output/name, tmp_path/'outside'
    path.parent.mkdir(parents=True, exist_ok=True)
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
        pytest.fail('Provider invoked after output collision')
    with pytest.raises(WorkflowError, match='already exists'):
        run_fixed(first_action_dir=first, model_id='test', output_dir=output, runner=forbidden)
    if target.exists():
        assert target.read_text() == 'unchanged'
    if kind == 'regular':
        assert path.read_text() == 'unchanged'


@pytest.mark.parametrize('kind', ['invalid-json', 'bad-citation', 'timeout'])
def test_fixed_failure_preserves_actual_capture_and_unjudged_outcome(tmp_path, kind):
    import subprocess
    from learning_project.lab07_comparison import run_fixed
    from learning_project.workflow import WorkflowError
    first = first_read(tmp_path/'first')
    calls = []
    def provider(*a, **kw):
        calls.append(a)
        if kind == 'timeout':
            raise subprocess.TimeoutExpired('agy', 330, output=b'partial')
        if kind == 'bad-citation':
            return response({'outcome_type': 'generated prerequisite explanation',
                             'claims': [{'text': 'bad', 'fragment_ids': ['outside']}]})
        return SimpleNamespace(returncode=0, stdout='invalid', stderr='')
    out = tmp_path/'out'
    with pytest.raises(WorkflowError, match='stop without automatic retry'):
        run_fixed(first_action_dir=first, model_id='test', output_dir=out, runner=provider)
    assert len(calls) == 1
    assert (out/'generation/provider-response.json').is_file()
    assert not (out/'generation/outcome.json').exists()
    assert load(out/'trace.json')['executed input'] == load(out/'generation/request.json')
    meta = load(out/'run-metadata.json')
    assert meta['status'] == 'execution failure'
    assert meta['new_provider_invocations'] == 1
    assert meta['semantic_judgment'] == 'not performed'


def test_documented_fixed_cli_executes_relative_paths(tmp_path, monkeypatch, capsys):
    from learning_project.cli import main
    import learning_project.lab07_comparison as comparison
    first_read(tmp_path/'reports/lab07/first-read')
    actual = comparison.run_fixed
    def injected(**kwargs):
        return actual(**kwargs, runner=lambda *a, **kw: response({
            'outcome_type': 'refusal', 'blocking_condition': 'insufficient supplied source evidence'}))
    monkeypatch.setattr(comparison, 'run_fixed', injected)
    monkeypatch.chdir(tmp_path)
    assert main(['lab07', 'run-fixed', '--first-action-dir', 'reports/lab07/first-read',
                 '--model', 'test', '--output-dir', 'reports/lab07/fixed']) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'fixed path completed'


def test_fixed_invalid_predecessor_never_calls_provider(tmp_path):
    from learning_project.lab07_comparison import run_fixed
    from learning_project.workflow import WorkflowError
    first = first_read(tmp_path/'first')
    meta = load(first/'run-metadata.json')
    meta['status'] = 'execution failure'
    (first/'run-metadata.json').write_text(json.dumps(meta))
    def forbidden(*a, **kw):
        pytest.fail('Provider invoked after invalid predecessor')
    with pytest.raises(WorkflowError, match='First-action metadata'):
        run_fixed(first_action_dir=first, model_id='test', output_dir=tmp_path/'out', runner=forbidden)
    assert not (tmp_path/'out/attempt.json').exists()
