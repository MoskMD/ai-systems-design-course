"""Laboratory 07 report structure; human response and task judgments stay human-owned."""
from __future__ import annotations

import re
from pathlib import Path

from . import report_contract
from .lab07 import DEFAULT_CORPUS

HEADINGS = ('Ідентифікація', 'Мета роботи', 'Хід виконання', 'Висновки')
SCREENSHOTS = ('01-model-selected-read.png', '02-adaptive-explanation-feedback.png',
               '03-fixed-adaptive-comparison.png', '04-boundary-checks.png', '05-final-verification.png')
REQUIRED_EVIDENCE = (
    *(f'first-read/{name}' for name in ('attempt.json', 'request.json', 'provider-response.json',
                                       'action.json', 'trace.json', 'run-metadata.json')),
    *(f'adaptive/{name}' for name in ('attempt.json', 'retained-state.json', 'run-metadata.json')),
    *(f'fixed/{name}' for name in ('attempt.json', 'selection-record.json', 'trace.json', 'run-metadata.json',
                                 'generation/request.json', 'generation/provider-response.json',
                                 'generation/call-metadata.json')),
    'boundaries/attempt.json', 'boundaries/summary.json')
INTERNAL = r'(?<![\w-])(?:Authoring\s+(?:Stage|Gate)\b|Stage\s+(?:A|B|C1|C2|C3|C4|D|E)\b)'


def init_report(*, report_dir: Path) -> dict:
    from .lab04 import _write_new_output
    from .workflow import WorkflowError
    screenshot_dir = report_dir/'screenshots'
    if screenshot_dir.is_symlink() or (screenshot_dir.exists() and not screenshot_dir.is_dir()):
        raise WorkflowError('The screenshot directory must be a local directory, not a link or file.')
    fixture = Path(__file__).resolve().parents[2]/'fixtures/lab07/REPORT.md'
    _write_new_output(report_dir/'REPORT.md', fixture.read_text(encoding='utf-8'))
    screenshot_dir.mkdir(exist_ok=True)
    return {'status': 'passed', 'source_report': str(report_dir/'REPORT.md'),
            'screenshots': str(screenshot_dir), 'fixture': str(fixture)}


def _report_scope(report_dir: Path, text: str):
    if not re.search(r'^\s*[-*]?\s*Статус завершення:\s*`?honest-partial`?\s*$', text, re.M):
        return 'complete', SCREENSHOTS
    groups = ('first-read', 'adaptive', 'fixed', 'boundaries')
    reached = [SCREENSHOTS[n] for n, folder in enumerate(groups)
               if any(f.is_file() for f in (report_dir/folder).rglob('*'))]
    return 'honest-partial', (*reached, SCREENSHOTS[-1])


def validate_report(*, report_dir: Path) -> dict:
    """Pre-commit structural check; does not grade response quality or goal attainment."""
    path = report_dir/'REPORT.md'
    text = path.read_text(encoding='utf-8') if path.is_file() else ''
    state, screenshots = _report_scope(report_dir, text)
    result = report_contract.validate_report_contract(
        report_dir=report_dir, lab_id='lab07', lab_label='Laboratory 07', headings=HEADINGS,
        screenshots=screenshots, required_evidence=REQUIRED_EVIDENCE if state == 'complete' else (),
        internal_stage_pattern=INTERNAL, evidence_present_message='required reporting evidence is present',
        personal_branch_pattern=r'lab07/[A-Za-z0-9._-]+', personal_branch_example='lab07/<student-id>')
    prompts = re.search(r'^\[(?:Дія:|Сформулювати|Стисло|Указати)[^\n]*\]$', text, re.M)
    passed = prompts is None and 'Заповнити кожен розділ' not in text
    result['checks'].append({'check_id': 'report-prompts', 'status': 'passed' if passed else 'failed',
        'message': 'replace all fixture prompts and introductory instructions'})
    if state == 'honest-partial':
        stop = re.search(r'^### Межа зупинки[^\S\n]*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
        recorded = stop is not None and bool(stop[1].strip())
        result['checks'].append({'check_id': 'partial-stop', 'status': 'passed' if recorded else 'failed',
            'message': 'a partial report must record the stopping boundary and missing result'})
    result['completion_state'] = state
    result['screenshots'] = list(screenshots)
    result['status'] = 'passed' if all(c['status'] == 'passed' for c in result['checks']) else 'failed'
    return result


def _committed_inputs(report_dir: Path, final_commit: str) -> None:
    import subprocess
    from .lab02 import _discover_git_root
    from .workflow import WorkflowError
    if not re.fullmatch(r'[0-9a-f]{40}', final_commit):
        raise WorkflowError('Use the exact full final commit hash.')
    root = _discover_git_root(report_dir)
    if root is None or report_dir.is_symlink():
        raise WorkflowError('The source report must be inside its Git repository, not a link.')
    branch = subprocess.check_output(['git', '-C', str(root), 'branch', '--show-current'], text=True).strip()
    recorded = re.search(r'^\s*[-*]?\s*Особиста гілка:\s*`?([^`\s]+)`?\s*$',
                         (report_dir/'REPORT.md').read_text(encoding='utf-8'), re.M)
    if recorded is None or recorded[1] != branch:
        raise WorkflowError('The report personal branch must name the current branch.')
    exempt = {report_dir/'verification-report.json', report_dir/'screenshots'/SCREENSHOTS[-1],
              report_dir/'submission/REPORT.md'}
    paths = list(report_dir.rglob('*')) + [DEFAULT_CORPUS]
    for path in paths:
        if path.is_symlink():
            raise WorkflowError('Report inputs must not be symbolic links: ' + str(path))
        if path in exempt or (path.is_dir() and path != DEFAULT_CORPUS):
            continue
        relative = path.resolve().relative_to(root.resolve()).as_posix()
        from .committed_inputs import matches_committed_file
        if not matches_committed_file(root, path, final_commit):
            raise WorkflowError('Input is missing, uncommitted or changed after the final commit: ' + relative)


def _matching_capture(actual: Path, replay: Path) -> None:
    import math
    from .lab06 import _read
    from .workflow import WorkflowError
    originals = {p.relative_to(actual).as_posix(): p for p in actual.rglob('*') if p.is_file()}
    expected = {p.relative_to(replay).as_posix(): p for p in replay.rglob('*') if p.is_file()}
    if originals.keys() != expected.keys():
        raise WorkflowError('Capture file inventory differs from deterministic replay: ' + str(actual))
    for name, path in originals.items():
        left, right = _read(path), _read(expected[name])
        if path.name in ('run-metadata.json', 'call-metadata.json'):
            if left.keys() != right.keys():
                raise WorkflowError('Metadata field set differs from replay: ' + name)
            for field in ('continuation_seconds', 'provider_process_seconds'):
                if field in left:
                    if type(left[field]) not in (float, int) or not math.isfinite(left[field]) or left[field] < 0:
                        raise WorkflowError('Invalid recorded duration: ' + name)
                    left.pop(field)
                    right.pop(field)
            if left.get('evidence_kind') not in {
                'injected runner; not live attestation', 'live provider invocation',
                'live continuation from retained first-action capture',
                'live fixed continuation from retained first-action capture'}:
                raise WorkflowError('Unknown capture origin label: ' + name)
            left.pop('evidence_kind', None)
            right.pop('evidence_kind', None)
        if left != right:
            raise WorkflowError('Capture content differs from deterministic replay: ' + name)


def _verify_domain(report_dir: Path) -> None:
    import tempfile
    from types import SimpleNamespace
    from .lab06 import _read
    from .lab07_loop import MAX_DECISIONS, _validated_first_read, continue_adaptive
    from .lab07_comparison import run_fixed
    from .lab07_boundaries import run_boundary_checks
    from .workflow import WorkflowError
    _validated_first_read(report_dir/'first-read')
    with tempfile.TemporaryDirectory(prefix='lab07-report-replay-') as tmp:
        root = Path(tmp)
        for folder, operation in [('adaptive', continue_adaptive), ('fixed', run_fixed)]:
            actual = report_dir/folder
            paths = ([actual/f'decision-{n}'/name for n in range(1, MAX_DECISIONS+1)
                      for name in ('provider-response.json', 'generation/provider-response.json')]
                     if folder == 'adaptive' else [actual/'generation/provider-response.json'])
            responses = [_read(path) for path in paths if path.is_file()]
            position = 0
            def captured(*args, **kwargs):
                nonlocal position
                if position >= len(responses):
                    raise WorkflowError('Missing captured provider response; no provider call is permitted.')
                raw = responses[position]
                position += 1
                if raw.get('error_type'):
                    import subprocess
                    if raw['error_type'] == 'TimeoutExpired':
                        raise subprocess.TimeoutExpired('captured', 330, output=raw.get('stdout'), stderr=raw.get('stderr'))
                    # OS error subclasses carry the original class name in recorded metadata.
                    import builtins
                    error_class = getattr(builtins, raw['error_type'], None)
                    if not isinstance(error_class, type) or not issubclass(error_class, OSError):
                        raise WorkflowError('Unsupported recorded provider process failure.')
                    raise error_class('replay of recorded provider process failure')
                return SimpleNamespace(**raw)
            model = _read(actual/'attempt.json')['requested_model']
            try:
                operation(first_action_dir=report_dir/'first-read', model_id=model,
                          output_dir=root/folder, runner=captured)
            except WorkflowError:
                if not (root/folder/'run-metadata.json').is_file():
                    raise
            if position != len(responses):
                raise WorkflowError('Unused captured provider response; preserve the actual sequence.')
            _matching_capture(actual, root/folder)
        run_boundary_checks(first_action_dir=report_dir/'first-read', output_dir=root/'boundaries')
        _matching_capture(report_dir/'boundaries', root/'boundaries')


def verify(*, report_dir: Path, final_commit: str) -> dict:
    """Bind reporting evidence to HEAD; never manufacture human judgments."""
    from .lab06 import _write
    validation = validate_report(report_dir=report_dir)
    committed = False
    try:
        _committed_inputs(report_dir, final_commit)
    except Exception as exc:
        validation['checks'].append({'check_id': 'committed-inputs', 'status': 'failed', 'message': str(exc)})
    else:
        committed = True
        validation['checks'].append({'check_id': 'committed-inputs', 'status': 'passed',
            'message': 'source report, existing evidence and source corpus match committed bytes'})
    domain_passed = False
    if validation['completion_state'] == 'complete':
        try:
            if not committed:
                raise ValueError('Capture replay skipped because committed-input binding failed.')
            _verify_domain(report_dir)
        except Exception as exc:
            validation['checks'].append({'check_id': 'domain-evidence', 'status': 'failed', 'message': str(exc)})
        else:
            domain_passed = True
            validation['checks'].append({'check_id': 'domain-evidence', 'status': 'passed',
                'message': 'actual captures match readonly deterministic replay; no new provider calls or human judgments'})

    def write(path, result):
        result.update(completion_state=validation['completion_state'],
                      domain_completion_claimed=domain_passed and result['outcome'] == 'passed',
                      human_response_judgments_verified=False,
                      live_provider_origin_independently_attested=False)
        _write(path, result)

    return report_contract.verify_report_contract(
        report_dir=report_dir, final_commit=final_commit, lab_id='lab07', lab_label='Laboratory 07',
        screenshots=tuple(validation['screenshots']), validation=validation, write_report=write)
