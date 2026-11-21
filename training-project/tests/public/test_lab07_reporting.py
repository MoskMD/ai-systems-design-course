"""Report tests use synthetic fixtures, never student/pilot attestations."""
import importlib.util
import re
import shutil
import json
import subprocess

import pytest
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[2]/'fixtures/lab07/REPORT.md'


def filled_report(tmp_path):
    assert FIXTURE.is_file(), 'Missing actual laboratory report fixture'
    assert importlib.util.find_spec('learning_project.lab07_reporting'), 'Missing report validator'
    from learning_project import lab07_reporting as reporting
    report = tmp_path/'reports/lab07'
    report.mkdir(parents=True)
    text = FIXTURE.read_text()
    text = '\n'.join(line for line in text.splitlines() if not line.startswith('Заповнити кожен розділ'))
    text = re.sub(r'^\[[^\n]*\]$', 'Спостереження для модульного тесту.', text, flags=re.M)
    text = text.replace('- URL форка:', '- URL форка: https://github.com/test-student/course')
    text = text.replace('- Особиста гілка:', '- Особиста гілка: lab07/test-student')
    text = text.replace('`complete` або `honest-partial`', '`complete`')
    (report/'REPORT.md').write_text(text)
    for name in reporting.SCREENSHOTS[:-1]:
        target = report/'screenshots'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'unit-test-only image sentinel; not pilot evidence')
    for name in reporting.REQUIRED_EVIDENCE:
        target = report/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('{}')
    return report


def test_real_report_fixture_and_validator_form_one_contract(tmp_path):
    from learning_project import lab07_reporting as reporting
    result = reporting.validate_report(report_dir=filled_report(tmp_path))
    assert result['status'] == 'passed', result
    assert result['completion_state'] == 'complete'


def test_honest_partial_requires_only_started_checkpoints(tmp_path):
    from learning_project import lab07_reporting as reporting
    report = filled_report(tmp_path)
    text = (report/'REPORT.md').read_text().replace('`complete`', '`honest-partial`')
    for folder in ['adaptive', 'fixed', 'boundaries']:
        shutil.rmtree(report/folder)
    for name in reporting.SCREENSHOTS[1:-1]:
        (report/'screenshots'/name).unlink()
        text = '\n'.join(line for line in text.splitlines() if 'screenshots/'+name not in line)
    (report/'REPORT.md').write_text(text)
    result = reporting.validate_report(report_dir=report)
    assert result['status'] == 'passed', result
    assert result['completion_state'] == 'honest-partial'
    assert result['screenshots'] == [reporting.SCREENSHOTS[0], reporting.SCREENSHOTS[-1]]


def committed_partial_report(tmp_path, monkeypatch):
    from learning_project import lab07_reporting as reporting
    from learning_project.lab07 import DEFAULT_CORPUS
    report = filled_report(tmp_path)
    for folder in ['first-read', 'adaptive', 'fixed', 'boundaries']:
        shutil.rmtree(report/folder)
    text = (report/'REPORT.md').read_text().replace('`complete`', '`honest-partial`')
    for name in reporting.SCREENSHOTS[:-1]:
        (report/'screenshots'/name).unlink()
        text = '\n'.join(line for line in text.splitlines() if 'screenshots/'+name not in line)
    (report/'REPORT.md').write_text(text)
    source = tmp_path/'cases/lab07/accessible-passages.json'
    source.parent.mkdir(parents=True)
    source.write_bytes(DEFAULT_CORPUS.read_bytes())
    monkeypatch.setattr(reporting, 'DEFAULT_CORPUS', source, raising=False)
    def git(*args):
        return subprocess.check_output(['git', '-C', str(tmp_path), *args], text=True).strip()
    git('init', '-q', '-b', 'lab07/test-student')
    git('config', 'user.name', 'Synthetic report unit-test actor')
    git('config', 'user.email', 'unit-test@example.invalid')
    git('config', 'commit.gpgsign', 'false')
    git('add', '.')
    git('commit', '-qm', 'Synthetic report test fixture; not student evidence')
    return report, source, git('rev-parse', 'HEAD')


def test_partial_verification_binds_exact_head_without_claiming_domain_completion(tmp_path, monkeypatch):
    from learning_project import lab07_reporting as reporting
    report, source, head = committed_partial_report(tmp_path, monkeypatch)
    assert callable(getattr(reporting, 'verify', None)), 'Missing final-commit reporting verifier'
    result = reporting.verify(report_dir=report, final_commit=head)
    assert result['outcome'] == 'passed', result
    assert result['completion_state'] == 'honest-partial'
    assert result['domain_completion_claimed'] is False
    assert result['final_commit'] == head
    assert json.loads((report/'verification-report.json').read_text()) == result


def complete_report(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from learning_project import lab07_reporting as reporting
    from learning_project.lab07 import DEFAULT_CORPUS
    from learning_project.lab07_loop import continue_adaptive
    from learning_project.lab07_comparison import run_fixed
    from learning_project.lab07_boundaries import run_boundary_checks
    from test_lab07_boundaries import first_read
    report = filled_report(tmp_path)
    for folder in ['first-read', 'adaptive', 'fixed', 'boundaries']:
        shutil.rmtree(report/folder)
    first_read(report/'first-read')
    def response(value):
        return SimpleNamespace(returncode=0, stderr='', stdout=json.dumps({
            'status': 'SUCCESS', 'response': json.dumps(value)}))
    continue_adaptive(first_action_dir=report/'first-read', model_id='test', output_dir=report/'adaptive',
                      runner=lambda *a, **kw: response({'operation': 'stop', 'arguments': {}}))
    run_fixed(first_action_dir=report/'first-read', model_id='test', output_dir=report/'fixed',
              runner=lambda *a, **kw: response({'outcome_type': 'generated prerequisite explanation',
                  'claims': [{'text': 'Unit-test synthetic claim; not a human quality judgment.', 'fragment_ids': ['AP-1']}]}))
    run_boundary_checks(first_action_dir=report/'first-read', output_dir=report/'boundaries')
    source = tmp_path/'cases/lab07/accessible-passages.json'
    source.parent.mkdir(parents=True)
    source.write_bytes(DEFAULT_CORPUS.read_bytes())
    monkeypatch.setattr(reporting, 'DEFAULT_CORPUS', source)
    def git(*args):
        return subprocess.check_output(['git', '-C', str(tmp_path), *args], text=True).strip()
    git('init', '-q', '-b', 'lab07/test-student')
    git('config', 'user.name', 'Synthetic report unit-test actor')
    git('config', 'user.email', 'unit-test@example.invalid')
    git('config', 'commit.gpgsign', 'false')
    git('add', '.')
    git('commit', '-qm', 'Synthetic complete test fixture; not student or pilot evidence')
    return report, source, git('rev-parse', 'HEAD')


def test_complete_verification_replays_actual_application_captures_without_model_calls(tmp_path, monkeypatch):
    from learning_project import lab07_reporting as reporting
    report, source, head = complete_report(tmp_path, monkeypatch)
    result = reporting.verify(report_dir=report, final_commit=head)
    assert result['outcome'] == 'passed', result
    assert result['domain_completion_claimed'] is True
    assert result['human_response_judgments_verified'] is False


@pytest.mark.parametrize('kind', ['source-edited', 'source-deleted', 'untracked-evidence', 'ignored-evidence', 'wrong-head', 'wrong-branch', 'symlink'])
def test_final_verifier_rejects_unbound_inputs(tmp_path, monkeypatch, kind):
    from learning_project import lab07_reporting as reporting
    report, source, head = committed_partial_report(tmp_path, monkeypatch)
    if kind == 'source-edited':
        source.write_text('{}')
    elif kind == 'source-deleted':
        source.unlink()
    elif kind == 'wrong-head':
        head = '0'*40
    elif kind == 'wrong-branch':
        subprocess.run(['git', '-C', str(tmp_path), 'branch', '-m', 'lab07/other'], check=True)
    elif kind == 'symlink':
        target = tmp_path/'external.txt'
        target.write_text('unchanged')
        try:
            (report/'linked-input').symlink_to(target)
        except OSError:
            pytest.skip('Host does not permit symlinks')
    else:
        if kind == 'ignored-evidence':
            (tmp_path/'.git/info/exclude').write_text('reports/lab07/extra.json\n')
        (report/'extra.json').write_text('{}')
    result = reporting.verify(report_dir=report, final_commit=head)
    assert result['outcome'] == 'failed', result
    assert result['domain_completion_claimed'] is False


@pytest.mark.parametrize('kind', ['missing-heading', 'missing-image', 'wrong-link', 'internal-body', 'retained-prompt', 'data-uri', 'missing-evidence'])
def test_report_validator_rejects_incomplete_source_report(tmp_path, kind):
    from learning_project import lab07_reporting as reporting
    report = filled_report(tmp_path)
    path = report/'REPORT.md'
    text = path.read_text()
    if kind == 'missing-heading':
        text = text.replace('## Хід виконання', '## Інше')
    elif kind == 'missing-image':
        (report/'screenshots'/reporting.SCREENSHOTS[0]).unlink()
    elif kind == 'wrong-link':
        text = text.replace('screenshots/'+reporting.SCREENSHOTS[0], 'screenshots/incorrect.png')
    elif kind == 'internal-body':
        text += '\nPerformed Authoring Stage C2.\n'
    elif kind == 'retained-prompt':
        text += '\n[Дія: заповнити звіт]\n'
    elif kind == 'data-uri':
        text += '\ndata:image/png;base64,AA==\n'
    elif kind == 'missing-evidence':
        (report/reporting.REQUIRED_EVIDENCE[0]).unlink()
    path.write_text(text)
    assert reporting.validate_report(report_dir=report)['status'] == 'failed'


def test_actual_fixture_packages_all_checkpoint_images_without_changing_source(tmp_path):
    from learning_project import lab07_reporting as reporting
    from learning_project.report_submission import prepare_report
    from PIL import Image
    report = filled_report(tmp_path)
    for name in reporting.SCREENSHOTS:
        Image.new('RGB', (32, 24), 'green').save(report/'screenshots'/name)
    original = (report/'REPORT.md').read_bytes()
    destination, images = prepare_report(report/'REPORT.md')
    assert images == len(reporting.SCREENSHOTS)
    assert destination == report/'submission/REPORT.md'
    assert destination.read_text().count('data:image/png;base64,') == len(reporting.SCREENSHOTS)
    assert (report/'REPORT.md').read_bytes() == original


@pytest.mark.parametrize('command', ['validate-report', 'verify'])
def test_reporting_cli_executes_and_returns_machine_status(tmp_path, monkeypatch, capsys, command):
    from learning_project.cli import main
    report, source, head = committed_partial_report(tmp_path, monkeypatch)
    args = ['lab07', command, '--report-dir', str(report)]
    if command == 'verify':
        args += ['--final-commit', head]
    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['outcome' if command == 'verify' else 'status'] == 'passed'


@pytest.mark.parametrize('name', ['fixed/generation/request.json', 'boundaries/summary.json', 'adaptive/run-metadata.json'])
def test_committed_tampered_capture_fails_domain_replay(tmp_path, monkeypatch, name):
    from learning_project import lab07_reporting as reporting
    report, source, head = complete_report(tmp_path, monkeypatch)
    file = report/name
    data = json.loads(file.read_text())
    data['unrecorded alteration'] = True
    file.write_text(json.dumps(data))
    subprocess.run(['git', '-C', str(tmp_path), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(tmp_path), 'commit', '-qm', 'Synthetic negative tamper fixture'], check=True)
    head = subprocess.check_output(['git', '-C', str(tmp_path), 'rev-parse', 'HEAD'], text=True).strip()
    result = reporting.verify(report_dir=report, final_commit=head)
    assert result['outcome'] == 'failed'
    assert next(c for c in result['checks'] if c['check_id'] == 'committed-inputs')['status'] == 'passed'
    assert next(c for c in result['checks'] if c['check_id'] == 'domain-evidence')['status'] == 'failed'


def test_initialize_source_report_uses_real_fixture_and_is_create_only(tmp_path):
    from learning_project.cli import main
    report = tmp_path/'reports/lab07'
    assert main(['lab07', 'init-report', '--report-dir', str(report)]) == 0
    assert (report/'REPORT.md').read_bytes() == FIXTURE.read_bytes()
    assert (report/'screenshots').is_dir()
    original = (report/'REPORT.md').read_bytes()
    assert main(['lab07', 'init-report', '--report-dir', str(report)]) == 1
    assert (report/'REPORT.md').read_bytes() == original


def test_validator_accepts_legitimate_hyphenated_cli_name(tmp_path):
    from learning_project import lab07_reporting as reporting
    report = filled_report(tmp_path)
    with (report/'REPORT.md').open('a') as handle:
        handle.write('\nTool syntax example: verify-stage-c1.\n')
    assert reporting.validate_report(report_dir=report)['status'] == 'passed'
