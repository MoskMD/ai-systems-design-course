"""Diagnostic probes exercise real application code, not live model behavior."""
import importlib.util
import json
from types import SimpleNamespace

import pytest

from learning_project.lab07 import DEFAULT_CORPUS, run_first_action


def load(path):
    return json.loads(path.read_text())


def first_read(folder):
    action = {'operation': 'retrieval operation', 'arguments': {
        'text query': 'why is a query embedding needed for embedding-based retrieval',
        'collection': 'S-AGENT/v1'}}
    run_first_action(model_id='test', output_dir=folder, runner=lambda *a, **kw:
        SimpleNamespace(returncode=0, stderr='', stdout=json.dumps({
            'status': 'SUCCESS', 'response': json.dumps(action)})))
    return folder


def test_diagnostic_denial_never_executes_canonical_write(tmp_path):
    assert importlib.util.find_spec('learning_project.lab07_boundaries'), 'Missing executable boundary probes'
    from learning_project.lab07_boundaries import run_boundary_checks
    source = DEFAULT_CORPUS.read_bytes()
    out = tmp_path/'checks'
    result = run_boundary_checks(first_action_dir=first_read(tmp_path/'first'), output_dir=out)
    denied = load(out/'denial/decision-1/trace.json')
    assert denied['requested action']['operation'] == 'canonical write'
    assert denied['permission']['allowed'] is False
    assert denied['executed input'] is None and denied['returned result'] is None
    assert load(out/'denial/run-metadata.json')['status'] == 'permission denied'
    assert DEFAULT_CORPUS.read_bytes() == source
    assert result['live_provider_invocations'] == 0
    assert 'diagnostic' in result['evidence_kind']
    for metadata_path in out.rglob('call-metadata.json'):
        metadata = load(metadata_path)
        assert metadata['evidence_kind'] == 'injected runner; not live attestation'
        assert metadata['timing_boundary'] == 'One transport invocation through completion only.'


def test_delivery_probe_labels_controlled_budget_and_preserves_omitted_text(tmp_path):
    from learning_project.lab07_boundaries import run_boundary_checks
    out = tmp_path/'checks'
    summary = run_boundary_checks(first_action_dir=first_read(tmp_path/'first'), output_dir=out)
    assert summary['retained_versus_delivered'] == 'passed'
    assert summary['diagnostic_budget_characters'] == 150
    assert summary['normal_route_budget_characters'] == 600
    assert load(out/'delivery/attempt.json')['context_budget_characters'] == 150
    request = load(out/'delivery/decision-1/request.json')
    omitted = next(u['text'] for u in load(DEFAULT_CORPUS)['fragments'] if u['retrieval_unit_id'] == 'AP-2')
    assert omitted not in json.dumps(request)
    assert omitted in json.dumps(load(out/'delivery/retained-state.json'))
    assert load(out/'delivery/run-metadata.json')['evidence_kind'] == 'injected runner; not live attestation'
    assert summary['live_provider_invocations'] == 0


def test_interrupted_diagnostic_is_recorded_without_refusal_or_retry(tmp_path):
    from learning_project.lab07_boundaries import run_boundary_checks
    out = tmp_path/'checks'
    summary = run_boundary_checks(first_action_dir=first_read(tmp_path/'first'), output_dir=out)
    assert summary['honest_stop'] == 'passed'
    failed = load(out/'interrupted/run-metadata.json')
    assert failed['status'] == 'execution failure'
    assert failed['new_provider_invocations'] == 1
    assert failed['task_accomplishment'] == 'not judged'
    assert 'TimeoutExpired' == load(out/'interrupted/decision-1/provider-response.json')['error_type']
    assert not (out/'interrupted/decision-2').exists()
    assert not (out/'interrupted/decision-1/action.json').exists()
    assert summary['live_provider_invocations'] == 0


@pytest.mark.parametrize('budget', [0, -1, 601, True, '150'])
def test_invalid_diagnostic_budget_stops_before_provider_or_output(tmp_path, budget):
    from learning_project.lab07_loop import continue_adaptive
    from learning_project.workflow import WorkflowError
    first = first_read(tmp_path/'first')
    out = tmp_path/'out'
    def forbidden(*a, **kw):
        pytest.fail('Invalid budget must not reach transport')
    with pytest.raises(WorkflowError, match='budget'):
        continue_adaptive(first_action_dir=first, model_id='test', output_dir=out,
            context_budget_characters=budget, runner=forbidden)
    assert not out.exists()


def test_documented_relative_boundary_cli_uses_no_model_argument(tmp_path, monkeypatch, capsys):
    from learning_project.cli import main
    first_read(tmp_path/'reports/lab07/first-read')
    monkeypatch.chdir(tmp_path)
    assert main(['lab07', 'check-boundaries', '--first-action-dir', 'reports/lab07/first-read',
                 '--output-dir', 'reports/lab07/boundaries']) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'boundary checks passed'
    assert load(tmp_path/'reports/lab07/boundaries/summary.json')['live_provider_invocations'] == 0


@pytest.mark.parametrize('name', ['attempt.json', 'summary.json', 'denial', 'delivery', 'interrupted'])
@pytest.mark.parametrize('kind', ['regular', 'dangling', 'existing-target'])
def test_collision_stops_before_input_read_and_preserves_target(tmp_path, monkeypatch, name, kind):
    import learning_project.lab07_boundaries as module
    from learning_project.workflow import WorkflowError
    out = tmp_path/'out'
    out.mkdir()
    slot = out/name
    target = tmp_path/'outside'
    if kind == 'regular':
        slot.write_text('unchanged')
    else:
        if kind == 'existing-target':
            target.write_text('unchanged')
        try:
            slot.symlink_to(target)
        except OSError:
            pytest.skip('Host does not permit test symlinks')
    def forbidden(*a, **kw):
        pytest.fail('Detected collision must stop before reading or running anything')
    monkeypatch.setattr(module, '_validated_first_read', forbidden)
    with pytest.raises(WorkflowError, match='create-only'):
        module.run_boundary_checks(first_action_dir=tmp_path/'unused', output_dir=out)
    if target.exists():
        assert target.read_text() == 'unchanged'
    if kind == 'regular':
        assert slot.read_text() == 'unchanged'


@pytest.mark.parametrize('query', ['teaching route', 'vector'])
def test_controlled_delivery_check_does_not_require_favorable_live_candidates(tmp_path, query):
    from learning_project.lab07_boundaries import run_boundary_checks
    first = tmp_path/'first'
    action = {'operation': 'retrieval operation', 'arguments': {'text query': query, 'collection': 'S-AGENT/v1'}}
    run_first_action(model_id='test', output_dir=first, runner=lambda *a, **kw:
        SimpleNamespace(returncode=0, stderr='', stdout=json.dumps({'status': 'SUCCESS', 'response': json.dumps(action)})))
    assert len(load(first/'trace.json')['ranked candidate output']) == 1
    out = tmp_path/'checks'
    result = run_boundary_checks(first_action_dir=first, output_dir=out)
    assert result['retained_versus_delivered'] == 'passed'
    assert load(out/'attempt.json')['first_action_capture']['trace.json'] == load(first/'trace.json')
    selected = load(out/'delivery/decision-2/selection-record.json')
    assert [u['retrieval unit id'] for u in selected['supplied source evidence']] == ['AP-1']
    omitted = next(u['text'] for u in load(DEFAULT_CORPUS)['fragments'] if u['retrieval_unit_id'] == 'AP-2')
    assert omitted not in json.dumps(load(out/'delivery/decision-2/request.json'))
    assert omitted in json.dumps(load(out/'delivery/retained-state.json'))


def test_controlled_budget_changes_delivery_without_erasing_retention(tmp_path):
    from learning_project.lab07_loop import continue_adaptive
    first = first_read(tmp_path/'first')
    out = tmp_path/'controlled'
    stop = {'operation': 'stop', 'arguments': {}}
    continue_adaptive(first_action_dir=first, model_id='test', output_dir=out,
        context_budget_characters=150, runner=lambda *a, **kw: SimpleNamespace(
            returncode=0, stderr='', stdout=json.dumps({'status': 'SUCCESS', 'response': json.dumps(stop)})))
    selection = load(out/'decision-1/selection-record.json')
    request = load(out/'decision-1/request.json')
    assert [u['retrieval unit id'] for u in selection['supplied source evidence']] == ['AP-1']
    omitted = next(u['text'] for u in load(DEFAULT_CORPUS)['fragments'] if u['retrieval_unit_id'] == 'AP-2')
    assert omitted in json.dumps(load(out/'retained-state.json'))
    assert omitted not in json.dumps(request)
    assert [u['retrieval unit id'] for u in request['supplied source evidence']] == ['AP-1']
    assert load(out/'attempt.json')['context_budget_characters'] == 150
