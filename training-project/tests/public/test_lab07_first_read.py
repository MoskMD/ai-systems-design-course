"""First observable action; synthetic transport results are not live evidence."""
import json
import pytest
from pathlib import Path
from types import SimpleNamespace


def test_model_query_drives_actual_read_without_delivering_new_passage(tmp_path):
    from learning_project.lab07 import run_first_action, DEFAULT_CORPUS
    corpus_before = DEFAULT_CORPUS.read_bytes()
    calls = []
    action = {'operation': 'retrieval operation', 'arguments': {
        'text query': 'query embedding vector comparison', 'collection': 'S-AGENT/v1'}}
    def provider(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout=json.dumps({
            'status': 'SUCCESS', 'response': json.dumps(action)}), stderr='')
    result = run_first_action(model_id='test-model', output_dir=tmp_path/'run', runner=provider)
    assert result['status'] == 'candidates returned'
    trace = json.loads((tmp_path/'run/trace.json').read_text())
    assert trace['requested action'] == action
    assert trace['permission']['allowed'] is True
    assert trace['executed input'] == action['arguments']
    assert trace['ranked candidate output'][0]['retrieval_unit_id'] == 'AP-2'
    assert trace['ranked candidate output'][0]['provenance_link']['source_id'] == 'S-AGENT'
    assert trace['delivered to next model request'] is False
    assert len(calls) == 1
    request = json.loads((tmp_path/'run/request.json').read_text())
    assert set(request) == {'task instruction', 'supplied source evidence', 'output contract'}
    assert [x['retrieval_unit_id'] for x in request['supplied source evidence']] == ['AP-1']
    assert 'represents the question as a vector' not in json.dumps(request)
    assert json.loads((tmp_path/'run/run-metadata.json').read_text())['semantic_judgment'] == 'not performed'
    assert DEFAULT_CORPUS.read_bytes() == corpus_before


def test_prompt_schema_acquisition_does_not_add_agy_repair_turn(tmp_path):
    from learning_project.lab07 import run_first_action, ACTION_SCHEMA
    calls = []
    def runner(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout=json.dumps({'status': 'SUCCESS',
            'response': json.dumps({'operation': 'stop', 'arguments': {}})}), stderr='')
    run_first_action(model_id='test', output_dir=tmp_path/'run', runner=runner)
    command = calls[0]
    assert '--json-schema' not in command
    request = json.loads((tmp_path/'run/request.json').read_text())
    assert json.dumps(ACTION_SCHEMA, ensure_ascii=False) in request['output contract']
    assert 'retrieval operation' in json.dumps(ACTION_SCHEMA)
    assert 'model-backed prerequisite-explanation operation' in json.dumps(ACTION_SCHEMA)
    assert 'stop' in json.dumps(ACTION_SCHEMA)
    assert json.loads((tmp_path/'run/attempt.json').read_text())['acquisition'] == 'prompt-schema; no CLI repair turn'



def test_injected_runner_is_not_mislabelled_as_verified_live_evidence(tmp_path):
    from learning_project.lab07 import run_first_action
    def runner(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=json.dumps({'status': 'SUCCESS',
            'response': json.dumps({'operation': 'stop', 'arguments': {}})}), stderr='')
    run_first_action(model_id='test', output_dir=tmp_path/'run', runner=runner)
    meta = json.loads((tmp_path/'run/run-metadata.json').read_text())
    assert meta['evidence_kind'] == 'injected runner; not live attestation'


def test_cli_exposes_one_bounded_action(tmp_path, capsys):
    from learning_project.cli import main
    from learning_project.lab07 import OUTPUTS
    folder = tmp_path/'run'
    folder.mkdir()
    (folder/OUTPUTS[0]).write_text('existing')
    assert main(['lab07', 'run-first-action', '--model', 'test', '--output-dir', str(folder)]) == 1
    assert 'already exists' in capsys.readouterr().err


def test_structured_field_cannot_hide_multiple_action_objects(tmp_path):
    import pytest
    from learning_project.lab07 import run_first_action
    from learning_project.workflow import WorkflowError
    action = {'operation': 'stop', 'arguments': {}}
    raw = json.dumps({'status': 'SUCCESS', 'response': json.dumps(action) + ' ' + json.dumps(action),
                      'structured_output': action})
    def runner(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=raw, stderr='')
    with pytest.raises(WorkflowError, match='uniquely extractable'):
        run_first_action(model_id='test', output_dir=tmp_path/'run', runner=runner)
    assert json.loads((tmp_path/'run/provider-response.json').read_text())['stdout'] == raw
    assert not (tmp_path/'run/action.json').exists()
    assert json.loads((tmp_path/'run/run-metadata.json').read_text())['status'] == 'execution failure'


@pytest.mark.parametrize('name', ['attempt.json', 'request.json', 'provider-response.json',
                                  'action.json', 'trace.json', 'run-metadata.json'])
@pytest.mark.parametrize('kind', ['regular', 'dangling', 'existing-target'])
def test_every_sibling_collision_stops_before_provider(tmp_path, name, kind):
    from learning_project.lab07 import run_first_action
    from learning_project.workflow import WorkflowError
    folder = tmp_path/'run'
    folder.mkdir()
    target = tmp_path/'outside'
    path = folder/name
    if kind == 'regular':
        path.write_text('unchanged')
    else:
        if kind == 'existing-target':
            target.write_text('unchanged')
        try:
            path.symlink_to(target)
        except OSError:
            pytest.skip('Host does not permit test symlinks')
    def forbidden(*args, **kwargs):
        pytest.fail('Provider called after output collision')
    with pytest.raises(WorkflowError, match='already exists'):
        run_first_action(model_id='test', output_dir=folder, runner=forbidden)
    if target.exists():
        assert target.read_text() == 'unchanged'
    if kind == 'regular':
        assert path.read_text() == 'unchanged'


@pytest.mark.parametrize('action, status, allowed', [
    ({'operation': 'canonical write', 'arguments': {}}, 'permission denied', False),
    ({'operation': 'retrieval operation', 'arguments': {'text query': 'query', 'collection': '../outside'}}, 'permission denied', False),
    ({'operation': 'retrieval operation', 'arguments': {'text query': '', 'collection': 'S-AGENT/v1'}}, 'permission denied', False),
    ({'operation': 'retrieval operation', 'arguments': {'query': 'query', 'collection': 'S-AGENT/v1'}}, 'permission denied', False),
    ({'operation': 'model-backed prerequisite-explanation operation', 'arguments': {}}, 'non-retrieval action requested; not executed in this slice', True),
    ({'operation': 'stop', 'arguments': {}}, 'stop proposed', True)])
def test_no_silent_substitution_for_non_retrieval_choice(tmp_path, action, status, allowed):
    from learning_project.lab07 import run_first_action
    calls = []
    def runner(*args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout=json.dumps({'status': 'SUCCESS',
            'response': json.dumps(action)}), stderr='')
    result = run_first_action(model_id='test', output_dir=tmp_path/'run', runner=runner)
    trace = json.loads((tmp_path/'run/trace.json').read_text())
    assert result['status'] == status
    assert trace['permission']['allowed'] is allowed
    assert trace['requested action'] == action
    assert trace['executed input'] is None
    assert trace['ranked candidate output'] == []
    assert len(calls) == 1


@pytest.mark.parametrize('kind', ['error-status', 'invalid-json', 'timeout'])
def test_provider_failure_never_becomes_refusal_or_retrieval(tmp_path, kind):
    import subprocess
    from learning_project.lab07 import run_first_action
    from learning_project.workflow import WorkflowError
    def runner(*args, **kwargs):
        if kind == 'timeout':
            raise subprocess.TimeoutExpired('agy', 330, output=b'partial stdout', stderr=b'partial stderr')
        return SimpleNamespace(returncode=0, stdout='{' if kind == 'invalid-json' else json.dumps({
            'status': 'ERROR', 'response': '{"operation":"stop","arguments":{}}', 'error': '503 unavailable'}), stderr='')
    with pytest.raises(WorkflowError):
        run_first_action(model_id='test', output_dir=tmp_path/'run', runner=runner)
    assert (tmp_path/'run/attempt.json').exists()
    assert (tmp_path/'run/provider-response.json').exists()
    assert not (tmp_path/'run/action.json').exists()
    assert not (tmp_path/'run/trace.json').exists()
    assert json.loads((tmp_path/'run/run-metadata.json').read_text())['status'] == 'execution failure'


def test_multiple_fences_do_not_hide_second_action(tmp_path):
    import pytest
    from learning_project.lab07 import run_first_action
    from learning_project.workflow import WorkflowError
    action = {'operation': 'stop', 'arguments': {}}
    text = '```json\n' + json.dumps(action) + '\n```\n' + json.dumps(action)
    def runner(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=json.dumps({'status': 'SUCCESS',
            'response': text, 'structured_output': action}), stderr='')
    with pytest.raises(WorkflowError, match='uniquely extractable'):
        run_first_action(model_id='test', output_dir=tmp_path/'run', runner=runner)
